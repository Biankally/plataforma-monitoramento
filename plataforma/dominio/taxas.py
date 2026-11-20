"""Calculo de taxas a partir de contadores acumulados (camada 1).

Ex.: o MySQL informa "Questions = 10000 desde que ligou". Com duas leituras:
taxa = (atual - anterior) / intervalo.
"""

from __future__ import annotations


def taxa_por_segundo(anterior: float, atual: float, intervalo_s: float) -> float | None:
    """Devolve a taxa, ou None quando nao da para calcular.

    None quando o intervalo e invalido ou o contador diminuiu (o servico
    reiniciou e o contador voltou a zero): nesse ciclo nao ha amostra.
    """
    if intervalo_s <= 0 or atual < anterior:
        return None
    return (atual - anterior) / intervalo_s
