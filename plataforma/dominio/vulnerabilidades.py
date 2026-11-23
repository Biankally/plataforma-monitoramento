"""Vulnerabilidade conhecida por servico (camada 1, Python puro).

Compara a versao de cada programa (lida pelo agente) com a lista de CVEs de config/vulnerabilidades.toml.
Uma entrada pega a versao quando: esta no ramo certo (se `ramo` existe), e >= `afeta_desde` (se existe)
e < `corrigido_em`. Versao ilegivel ou ausente nao gera evento (nao se inventa falha).
"""

from __future__ import annotations

import re

from plataforma.dominio.seguranca import EventoSeguranca

_NUMEROS = re.compile(r"^\d+(\.\d+){0,3}")


def versao_em_tupla(texto: str) -> tuple[int, ...]:
    """'8.0.40' -> (8, 0, 40); completa com zeros ate 3 partes ('3.9' -> (3, 9, 0)). ValueError se ilegivel."""
    achado = _NUMEROS.match(str(texto).strip())
    if not achado:
        raise ValueError(f"versao ilegivel: {texto!r}")
    partes = tuple(int(p) for p in achado.group(0).split("."))
    return partes + (0,) * (3 - len(partes))


def vulneravel(versao: str, entrada: dict) -> bool:
    atual = versao_em_tupla(versao)
    if "ramo" in entrada and atual[:2] != versao_em_tupla(entrada["ramo"])[:2]:
        return False
    if "afeta_desde" in entrada and atual < versao_em_tupla(entrada["afeta_desde"]):
        return False
    return atual < versao_em_tupla(entrada["corrigido_em"])


def avaliar_versoes(versoes: dict, catalogo: list[dict]) -> list[EventoSeguranca]:
    """versoes: {"dns": {"unbound": "1.20.0"}, ...} -> um evento VULNERABILIDADE por CVE que pega a versao."""
    eventos = []
    for entrada in catalogo:
        versao = (versoes.get(entrada["servico"]) or {}).get(entrada["programa"])
        if not versao:
            continue
        try:
            achou = vulneravel(versao, entrada)
        except ValueError:
            continue   # versao ilegivel: sem dado, sem evento
        if achou:
            detalhe = (f"{entrada['cve']}: {entrada['descricao']} "
                       f"(versao {versao}; corrigido em {entrada['corrigido_em']})")
            eventos.append(EventoSeguranca("VULNERABILIDADE", entrada["servico"], entrada["nivel"],
                                           f"{entrada['programa']} {versao}", detalhe, 1.0, None))
    return eventos
