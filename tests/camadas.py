"""Verificador da regra de camadas: le os imports de cada arquivo (sem executa-lo).

Um arquivo so pode importar da propria camada ou de camadas abaixo:
    0 contrato < 1 dominio < 2 infra < 3 api < 4 dashboard
"""

from __future__ import annotations

import ast
from pathlib import Path

CAMADAS = {"contrato": 0, "dominio": 1, "infra": 2, "api": 3, "dashboard": 4}


def _camada_do_modulo(modulo: str) -> str | None:
    partes = modulo.split(".")
    if len(partes) >= 2 and partes[0] == "plataforma" and partes[1] in CAMADAS:
        return partes[1]
    return None


def violacoes(pasta_plataforma: Path) -> list[str]:
    problemas = []
    for arquivo in sorted(Path(pasta_plataforma).rglob("*.py")):
        relativo = arquivo.relative_to(pasta_plataforma)
        if len(relativo.parts) < 2 or relativo.parts[0] not in CAMADAS:
            continue
        propria = relativo.parts[0]
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                modulos = [a.name for a in no.names]
            elif isinstance(no, ast.ImportFrom) and no.level == 0 and no.module:
                modulos = [no.module] + [f"{no.module}.{a.name}" for a in no.names]
            else:
                continue
            for modulo in modulos:
                alvo = _camada_do_modulo(modulo)
                if alvo and CAMADAS[alvo] > CAMADAS[propria]:
                    problemas.append(f"{relativo.as_posix()}:{no.lineno} ({propria}) importa {modulo} ({alvo})")
                    break
    return problemas
