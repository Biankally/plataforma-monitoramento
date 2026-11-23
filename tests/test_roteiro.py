"""Roteiro de testes (P3, tarefa 3): confere que testes/roteiro.md tem os casos T01 a T15 completos.

Cada caso precisa de objetivo, requisito, passos, resultado esperado e evidencia (o print da tarefa 4).
"""

from __future__ import annotations

import re
from pathlib import Path

ROTEIRO = Path(__file__).resolve().parents[1] / "testes" / "roteiro.md"
CASOS = [f"T{n:02d}" for n in range(1, 16)]
CAMPOS = ["**Objetivo:**", "**Requisito:**", "**Passos:**", "**Resultado esperado:**", "**Evidência:**"]


def _secoes(texto: str) -> dict[str, str]:
    """Separa o texto em casos: cada '### Txx — titulo' ate o proximo cabecalho de caso."""
    partes = re.split(r"^### (T\d{2}) — .+$", texto, flags=re.MULTILINE)
    return {partes[i]: partes[i + 1] for i in range(1, len(partes) - 1, 2)}


def problemas(texto: str) -> list[str]:
    secoes = _secoes(texto)
    erros = [f"{c}: caso ausente" for c in CASOS if c not in secoes]
    erros += [f"{c}: caso a mais" for c in secoes if c not in CASOS]
    for caso, corpo in secoes.items():
        erros += [f"{caso}: falta {campo}" for campo in CAMPOS if campo not in corpo]
        if f"testes/evidencias/{caso}" not in corpo:
            erros.append(f"{caso}: evidencia sem arquivo em testes/evidencias/{caso}...")
        if not re.search(r"^\s*1\. ", corpo, flags=re.MULTILINE):
            erros.append(f"{caso}: passos nao numerados")
        if caso not in texto.split("## Resumo dos casos", 1)[-1].split("## Casos", 1)[0]:
            erros.append(f"{caso}: fora da tabela de resumo")
    return erros


def test_roteiro_tem_os_15_casos_completos():
    assert problemas(ROTEIRO.read_text(encoding="utf-8")) == []


def test_sabotagem_caso_ausente_e_acusado():
    texto = ROTEIRO.read_text(encoding="utf-8")
    sem_t07 = re.sub(r"^### T07 — .+?(?=^### T08)", "", texto, flags=re.MULTILINE | re.DOTALL)
    assert "T07: caso ausente" in problemas(sem_t07)


def test_sabotagem_campo_faltando_e_acusado():
    texto = ROTEIRO.read_text(encoding="utf-8")
    inicio = texto.index("### T03 — ")
    fim = texto.index("### T04 — ")
    trecho = texto[inicio:fim].replace("**Resultado esperado:**", "**Resultado:**")
    assert "T03: falta **Resultado esperado:**" in problemas(texto[:inicio] + trecho + texto[fim:])


def test_sabotagem_evidencia_sem_arquivo_e_acusada():
    texto = ROTEIRO.read_text(encoding="utf-8").replace("testes/evidencias/T12", "a definir")
    assert any(e.startswith("T12: evidencia sem arquivo") for e in problemas(texto))


def test_sabotagem_caso_fora_do_resumo_e_acusado():
    texto = ROTEIRO.read_text(encoding="utf-8")
    resumo, resto = texto.split("## Casos", 1)
    resumo = resumo.replace("| T15 |", "| — |")
    assert "T15: fora da tabela de resumo" in problemas(resumo + "## Casos" + resto)
