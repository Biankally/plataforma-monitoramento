"""Do que a sonda do MySQL leu para as amostras `db.*` do catalogo (camada 1, Python puro).

Cada leitura e um dicionario: {"ts": epoch, "disponivel": ..., "status.Questions": ..., "max_connections": ...,
"tamanho_mb": ...} (a saida de `sonda_mysql` mais o `ts`). Metrica que nao da para calcular e omitida.

- Contadores acumulados (Questions, Com_rollback, Aborted_connects, Slow_queries): diferenca para a leitura anterior.
- Crescimento do banco: compara com a leitura `base` (mais antiga, ex. 10 min). Com intervalos curtos o tamanho
  oscila por paginas de 16 KB e a projecao para 24 h dispararia; por isso exige >= 60 s de historico.
"""

from __future__ import annotations

import math

from plataforma.contrato.metricas import Amostra
from plataforma.dominio.taxas import taxa_por_segundo

HISTORICO_MINIMO_S = 60.0
SEGUNDOS_POR_DIA = 86400.0


def _n(leitura: dict | None, chave: str) -> float | None:
    if not isinstance(leitura, dict):
        return None
    v = leitura.get(chave)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    return float(v)


def _delta(atual: dict, anterior: dict | None, chave: str) -> float | None:
    a, b = _n(atual, chave), _n(anterior, chave)
    if a is None or b is None or a < b:  # contador que diminuiu: o banco reiniciou
        return None
    return a - b


def derivar_db(atual: dict, anterior: dict | None, base: dict | None) -> list[Amostra]:
    saida: dict[str, float] = {}
    intervalo = None
    if _n(atual, "ts") is not None and _n(anterior, "ts") is not None:
        intervalo = _n(atual, "ts") - _n(anterior, "ts")

    # valores instantaneos
    for chave, metrica in (("status.Threads_connected", "db.conexoes"),
                           ("status.Threads_running", "db.conexoes_executando"),
                           ("status.Threads_cached", "db.threads_cache"),
                           ("tamanho_mb", "db.tamanho_mb")):
        if (v := _n(atual, chave)) is not None:
            saida[metrica] = v
    conectadas, maximo = _n(atual, "status.Threads_connected"), _n(atual, "max_connections")
    if conectadas is not None and maximo is not None and maximo > 0:
        saida["db.uso_conexoes_pct"] = conectadas / maximo * 100

    # taxas entre a leitura atual e a anterior
    if intervalo is not None:
        for chave, metrica in (("status.Questions", "db.qps"), ("status.Com_rollback", "db.rollbacks_s")):
            if (d := _delta(atual, anterior, chave)) is not None:
                if (t := taxa_por_segundo(0.0, d, intervalo)) is not None:
                    saida[metrica] = t
        if (d := _delta(atual, anterior, "status.Slow_queries")) is not None and intervalo > 0:
            saida["db.slow_queries_min"] = d / (intervalo / 60)
        if (d := _delta(atual, anterior, "status.Aborted_connects")) is not None and intervalo > 0:
            saida["db.conexoes_abortadas"] = d

    # crescimento projetado para 24 h, contra a leitura base
    tam_atual, tam_base = _n(atual, "tamanho_mb"), _n(base, "tamanho_mb")
    if tam_atual is not None and tam_base is not None and _n(atual, "ts") is not None and _n(base, "ts") is not None:
        janela = _n(atual, "ts") - _n(base, "ts")
        if janela >= HISTORICO_MINIMO_S:
            saida["db.crescimento_mb_dia"] = (tam_atual - tam_base) / janela * SEGUNDOS_POR_DIA

    return [Amostra("db", m, v) for m, v in saida.items()]
