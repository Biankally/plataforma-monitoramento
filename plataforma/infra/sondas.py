"""Sondas caixa-preta (camada 2): testam o servico de fora, como um usuario.

Esqueleto: HTTP e TCP generico. As sondas especificas (SELECT 1 no MySQL,
consulta DNS, dialogo SMTP) substituem a TCP no trabalho de P2.
"""

from __future__ import annotations

import socket
import time

import requests


def sonda_http(url: str, timeout_s: float) -> dict[str, float]:
    inicio = time.perf_counter()
    try:
        r = requests.get(url, timeout=timeout_s)
        disponivel = 1.0 if r.status_code < 500 else 0.0
    except requests.RequestException:
        disponivel = 0.0
    return {"disponivel": disponivel, "latencia_ms": (time.perf_counter() - inicio) * 1000}


def sonda_tcp(host: str, porta: int, timeout_s: float) -> dict[str, float]:
    inicio = time.perf_counter()
    try:
        with socket.create_connection((host, porta), timeout=timeout_s):
            disponivel = 1.0
    except OSError:
        disponivel = 0.0
    return {"disponivel": disponivel, "latencia_ms": (time.perf_counter() - inicio) * 1000}
