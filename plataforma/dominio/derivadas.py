"""Do JSON do agente para amostras do catalogo (camada 1, Python puro).

Recebe a leitura atual e a anterior do agente e devolve as amostras `web.*`,
`dns.*`, `smtp.*`, `host.*` e `db.cpu_pct`/`db.mem_pct`. Regra de ouro: metrica que nao da para calcular
(secao ausente, sem leitura anterior, contador que diminuiu, divisao por zero)
e OMITIDA. Nunca se inventa valor.

Premissas sobre o agente (ver tests/falsos/agente_exemplo.json):
- `apache`, `unbound`: contadores acumulados -> taxa = diferenca / intervalo.
- `log_web` e `postfix`: contagens da janela desde a leitura anterior (nao acumulam).
"""

from __future__ import annotations

import math

from plataforma.contrato.metricas import Amostra, servico_da_metrica
from plataforma.dominio.taxas import taxa_por_segundo


def _num(secao: object, chave: str) -> float | None:
    """Numero de `secao[chave]`, ou None se a secao/chave nao existe ou nao e numero."""
    if not isinstance(secao, dict):
        return None
    v = secao.get(chave)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    return float(v)


def _intervalo_s(atual: dict, anterior: dict | None) -> float | None:
    if anterior is None:
        return None
    ts_atual, ts_anterior = _num(atual, "ts"), _num(anterior, "ts")
    if ts_atual is None or ts_anterior is None:
        return None
    return ts_atual - ts_anterior


def _delta(atual: dict, anterior: dict | None, secao: str, chave: str) -> float | None:
    """Aumento de um contador entre duas leituras; None se nao der para calcular."""
    if anterior is None:
        return None
    a, b = _num(atual.get(secao), chave), _num(anterior.get(secao), chave)
    if a is None or b is None or a < b:  # contador que diminuiu = servico reiniciou
        return None
    return a - b


def _percentil_95(valores: list[float]) -> float:
    """Posto mais proximo: o valor na posicao ceil(0,95 * n) da lista ordenada."""
    ordenados = sorted(valores)
    return ordenados[math.ceil(0.95 * len(ordenados)) - 1]


def _pct(parte: float, total: float) -> float | None:
    return parte / total * 100 if total > 0 else None


def derivar(atual: dict, anterior: dict | None, falhas_sonda_dns: int = 0) -> list[Amostra]:
    """Converte as leituras do agente em amostras do catalogo.

    `falhas_sonda_dns`: quantas vezes a sonda DNS falhou neste ciclo (entra na
    taxa de erro do DNS, como diz o catalogo).
    """
    saida: dict[str, float] = {}
    intervalo = _intervalo_s(atual, anterior)

    # ---- web
    apache = atual.get("apache")
    if (aumento := _delta(atual, anterior, "apache", "total_accesses")) is not None and intervalo:
        if (rps := taxa_por_segundo(0.0, aumento, intervalo)) is not None:
            saida["web.rps"] = rps
    if (conexoes := _num(apache, "conns_total")) is not None:
        saida["web.conexoes_ativas"] = conexoes

    log = atual.get("log_web")
    if isinstance(log, dict) and isinstance(log.get("por_codigo"), dict):
        por_codigo = log["por_codigo"]
        total = _num(log, "total")
        req_4xx = sum(n for c, n in por_codigo.items() if str(c).startswith("4") and isinstance(n, (int, float)))
        req_5xx = sum(n for c, n in por_codigo.items() if str(c).startswith("5") and isinstance(n, (int, float)))
        saida["web.req_4xx"] = float(req_4xx)
        saida["web.req_5xx"] = float(req_5xx)
        if total is not None:
            if (p := _pct(req_4xx, total)) is not None:
                saida["web.taxa_erro_4xx_pct"] = p
            if (p := _pct(req_5xx, total)) is not None:
                saida["web.taxa_erro_5xx_pct"] = p
    tempos = log.get("tempo_servidor_us") if isinstance(log, dict) else None
    if isinstance(tempos, list) and tempos:
        saida["web.latencia_p95_ms"] = _percentil_95([float(t) for t in tempos]) / 1000

    # ---- dns
    consultas = _delta(atual, anterior, "unbound", "total.num.queries")
    if consultas is not None and intervalo:
        if (qps := taxa_por_segundo(0.0, consultas, intervalo)) is not None:
            saida["dns.qps"] = qps
        servfail = _delta(atual, anterior, "unbound", "num.answer.rcode.SERVFAIL") or 0.0
        refused = _delta(atual, anterior, "unbound", "num.answer.rcode.REFUSED") or 0.0
        if (p := _pct(servfail + refused + falhas_sonda_dns, consultas + falhas_sonda_dns)) is not None:
            saida["dns.taxa_erro_pct"] = p

    # ---- smtp
    pf = atual.get("postfix")
    if (fila := _num(pf, "fila")) is not None:
        saida["smtp.fila"] = fila
    enviados, adiados, devolvidos = (_num(pf, k) for k in ("sent", "deferred", "bounced"))
    rejeicoes, timeouts = _num(pf, "rejeicoes"), _num(pf, "timeouts")
    if None not in (enviados, adiados, devolvidos):
        if (p := _pct(enviados, enviados + adiados + devolvidos)) is not None:
            saida["smtp.taxa_entrega_pct"] = p
    if rejeicoes is not None:
        saida["smtp.rejeicoes"] = rejeicoes
    if timeouts is not None:
        saida["smtp.timeouts"] = timeouts
    if None not in (enviados, adiados, devolvidos, rejeicoes, timeouts):
        total_eventos = enviados + adiados + devolvidos + rejeicoes + timeouts
        if (p := _pct(rejeicoes + timeouts, total_eventos)) is not None:
            saida["smtp.taxa_erro_pct"] = p
    if (delay := _num(pf, "delay_medio_s")) is not None:
        saida["smtp.latencia_envio_s"] = delay
    if enviados is not None and intervalo and intervalo > 0:
        saida["smtp.emails_min"] = enviados / (intervalo / 60)

    # ---- banco: CPU e memoria do container (enunciado 3.2; o resto do db.* vem da sonda MySQL)
    containers = atual.get("containers")
    db = containers.get("db") if isinstance(containers, dict) else None
    for chave in ("cpu_pct", "mem_pct"):
        if (v := _num(db, chave)) is not None:
            saida[f"db.{chave}"] = v

    # ---- host
    host = atual.get("host")
    for chave in ("cpu_pct", "mem_pct", "disco_io_kbs", "disco_latencia_ms"):
        if (v := _num(host, chave)) is not None:
            saida[f"host.{chave}"] = v

    return [Amostra(servico_da_metrica(m), m, v) for m, v in saida.items()]
