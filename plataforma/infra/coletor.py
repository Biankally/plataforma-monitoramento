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

import requests

from plataforma.contrato import config
from plataforma.infra.sondas import sonda_http, sonda_tcp


def medir(servico: config.ServicoMonitorado) -> dict[str, float]:
    if servico.tipo == "http":
        return sonda_http(servico.url, servico.timeout_s)
    if servico.tipo == "tcp":
        return sonda_tcp(servico.host, servico.porta, servico.timeout_s)
    raise ValueError(f"tipo de sonda desconhecido: {servico.tipo!r}")


def montar_lote(ts: int) -> dict:
    amostras = []
    for s in config.servicos_monitorados():
        for nome, valor in medir(s).items():
            amostras.append({"servico": s.nome, "metrica": f"{s.nome}.{nome}", "valor": round(valor, 3)})
    return {"ts": ts, "amostras": amostras}


def enviar(lote: dict, api_url: str, token: str) -> None:
    r = requests.post(f"{api_url}/api/ingest", json=lote, headers={"X-Token": token}, timeout=10)
    r.raise_for_status()


def ciclo(api_url: str, token: str) -> None:
    enviar(montar_lote(int(time.time())), api_url, token)


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
    while True:
        inicio = time.monotonic()
        try:
            ciclo(api_url, token)
        except requests.RequestException as erro:
            print(f"[coletor] falha ao enviar o lote: {type(erro).__name__}", file=sys.stderr)
        time.sleep(max(0.0, intervalo - (time.monotonic() - inicio)))


if __name__ == "__main__":
    raise SystemExit(main())
