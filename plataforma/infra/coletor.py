"""Coletor (camada 2): mede cada servico e envia o lote para a API.

Uso:
    python -m plataforma.infra.coletor            # repete a cada intervalo
    python -m plataforma.infra.coletor --uma-vez  # um ciclo e sai
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass, field

import requests

from plataforma.contrato import config
from plataforma.contrato.metricas import Amostra
from plataforma.dominio.derivadas import derivar
from plataforma.dominio.derivadas_db import derivar_db
from plataforma.infra.agente_cliente import ErroAgente, ler_metricas
from plataforma.infra.sondas import sonda_dns, sonda_http, sonda_mysql, sonda_smtp, sonda_tcp

AGENTE_TIMEOUT_S = 5.0
JANELA_CRESCIMENTO_S = 600  # o crescimento do banco compara com a leitura mais antiga dos ultimos 10 min


@dataclass
class Memoria:
    """O que o Coletor lembra de um ciclo para o outro (as taxas precisam de duas leituras)."""

    agente: dict | None = None                 # ultima leitura boa do agente
    db_anterior: dict | None = None            # ultima leitura boa do MySQL
    db_historico: list[dict] = field(default_factory=list)  # leituras boas dentro da janela


def _exigir_env(nome: str) -> str:
    valor = os.environ.get(nome)
    if not valor:
        raise RuntimeError(f"defina {nome} no .env")
    return valor


def medir(servico: config.ServicoMonitorado) -> dict[str, float]:
    if servico.tipo == "http":
        return sonda_http(servico.url, servico.timeout_s)
    if servico.tipo == "tcp":
        return sonda_tcp(servico.host, servico.porta, servico.timeout_s)
    if servico.tipo == "mysql":
        usuario = os.environ.get("MONITOR_DB_USUARIO") or "monitor"
        return sonda_mysql(servico.host, servico.porta, usuario, _exigir_env("MONITOR_DB_SENHA"), servico.timeout_s)
    if servico.tipo == "dns":
        consulta = os.environ.get("MONITOR_DNS_CONSULTA") or "teste.lab.local"
        return sonda_dns(servico.host, servico.porta, consulta, servico.timeout_s)
    if servico.tipo == "smtp":
        return sonda_smtp(servico.host, servico.porta, servico.timeout_s)
    raise ValueError(f"tipo de sonda desconhecido: {servico.tipo!r}")


def _amostra(servico: str, metrica: str, valor: float) -> dict:
    return {"servico": servico, "metrica": metrica, "valor": round(valor, 3)}


def _de_amostras(amostras: list[Amostra]) -> list[dict]:
    return [_amostra(a.servico, a.metrica, a.valor) for a in amostras]


def _amostras_mysql(servico: config.ServicoMonitorado, medida: dict[str, float], ts: int,
                    memoria: Memoria) -> list[dict]:
    saida = [_amostra(servico.nome, f"{servico.nome}.{n}", medida[n]) for n in ("disponivel", "latencia_ms")]
    if medida["disponivel"] != 1.0:
        return saida  # banco fora do ar: nao vira leitura de referencia para as taxas
    atual = {"ts": ts, **medida}
    historico = [r for r in memoria.db_historico if r["ts"] >= ts - JANELA_CRESCIMENTO_S]
    base = historico[0] if historico else None
    saida += _de_amostras(derivar_db(atual, memoria.db_anterior, base))
    memoria.db_anterior = atual
    memoria.db_historico = [*historico, atual]
    return saida


def _agente_configurado() -> tuple[str, str] | None:
    """(url, token) do agente; None se o agente nao foi configurado (o Coletor segue so com as sondas)."""
    url = os.environ.get("MONITOR_AGENTE_URL") or config.plataforma().get("agente_url")
    if not url:
        return None
    return url, _exigir_env("MONITOR_AGENTE_TOKEN")


def _amostras_agente(memoria: Memoria, falhas_sonda_dns: int) -> list[dict]:
    cfg = _agente_configurado()
    if cfg is None:
        return []
    try:
        atual = ler_metricas(cfg[0], cfg[1], AGENTE_TIMEOUT_S)
    except ErroAgente as erro:
        print(f"[coletor] agente indisponivel, metricas dele omitidas neste ciclo: {erro}", file=sys.stderr)
        return []
    amostras = derivar(atual, memoria.agente, falhas_sonda_dns=falhas_sonda_dns)
    memoria.agente = atual
    return _de_amostras(amostras)


def montar_lote(ts: int, memoria: Memoria | None = None) -> dict:
    if memoria is None:
        memoria = Memoria()
    amostras: list[dict] = []
    falhas_sonda_dns = 0
    for s in config.servicos_monitorados():
        medida = medir(s)
        if s.tipo == "mysql":
            amostras += _amostras_mysql(s, medida, ts, memoria)
        else:
            amostras += [_amostra(s.nome, f"{s.nome}.{nome}", valor) for nome, valor in medida.items()]
        if s.tipo == "dns" and medida["disponivel"] == 0.0:
            falhas_sonda_dns += 1
    amostras += _amostras_agente(memoria, falhas_sonda_dns)
    return {"ts": ts, "amostras": amostras}


def enviar(lote: dict, api_url: str, token: str) -> None:
    r = requests.post(f"{api_url}/api/ingest", json=lote, headers={"X-Token": token}, timeout=10)
    r.raise_for_status()


def ciclo(api_url: str, token: str, memoria: Memoria | None = None) -> None:
    enviar(montar_lote(int(time.time()), memoria), api_url, token)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coletor da plataforma de monitoramento")
    parser.add_argument("--uma-vez", action="store_true", help="executa um ciclo e sai")
    args = parser.parse_args(argv)

    config.carregar_env()
    plat = config.plataforma()
    api_url = os.environ.get("MONITOR_API_URL") or plat.get("api_url", "http://127.0.0.1:5000")
    token = os.environ["MONITOR_TOKEN"]
    intervalo = float(plat.get("intervalo_s", 15))

    if args.uma_vez:
        ciclo(api_url, token)
        return 0
    memoria = Memoria()
    while True:
        inicio = time.monotonic()
        try:
            ciclo(api_url, token, memoria)
        except requests.RequestException as erro:
            print(f"[coletor] falha ao enviar o lote: {type(erro).__name__}", file=sys.stderr)
        time.sleep(max(0.0, intervalo - (time.monotonic() - inicio)))


if __name__ == "__main__":
    raise SystemExit(main())
