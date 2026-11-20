"""Cliente do agente (camada 2): le o JSON de metricas do agente que roda na VM-S.

Quem chama (o Coletor) decide o que fazer quando o agente falha: aqui o erro
sobe como ErroAgente, nunca vira um dicionario vazio.
"""

from __future__ import annotations

import requests


class ErroAgente(RuntimeError):
    """O agente nao respondeu, recusou o token ou devolveu algo que nao e um objeto JSON."""


def ler_metricas(url_base: str, token: str, timeout_s: float) -> dict:
    """GET {url_base}/metrics com o cabecalho X-Token; devolve o JSON como dicionario."""
    url = url_base.rstrip("/") + "/metrics"
    try:
        r = requests.get(url, headers={"X-Token": token}, timeout=timeout_s)
    except requests.RequestException as erro:
        raise ErroAgente(f"agente inacessivel em {url}: {type(erro).__name__}") from erro
    if r.status_code != 200:
        raise ErroAgente(f"agente respondeu HTTP {r.status_code}")
    try:
        dados = r.json()
    except ValueError as erro:
        raise ErroAgente("resposta do agente nao e JSON valido") from erro
    if not isinstance(dados, dict):
        raise ErroAgente("resposta do agente precisa ser um objeto JSON")
    return dados
