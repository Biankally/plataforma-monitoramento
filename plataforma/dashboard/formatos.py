"""Funcoes puras do dashboard (camada 4): cores dos niveis, valores com unidade, limites e horario.

Ficam separadas do app.py (que so desenha a tela) para poderem ser testadas sem o Streamlit.
"""

from __future__ import annotations

from datetime import datetime

INFORMATIVA = "INFORMATIVA"  # metrica sem regra de alerta: so aparece no dashboard

ICONES = {
    "OK": "🟢",
    "ATENCAO": "🟡",
    "CRITICO": "🔴",
    "SEM_DADOS": "⚪",
    INFORMATIVA: "🔵",
}
ICONE_DESCONHECIDO = "❔"


def icone(nivel: str) -> str:
    """Bolinha colorida do nivel (verde, amarelo, vermelho; branco sem dados; azul informativa)."""
    return ICONES.get(nivel, ICONE_DESCONHECIDO)


def com_icone(nivel: str) -> str:
    return f"{icone(nivel)} {nivel}"


def nivel_por_metrica(alertas: list[dict]) -> dict[str, str]:
    """Nivel atual de cada metrica = nivel_novo do alerta mais novo dela.

    A API devolve os alertas do mais novo para o mais antigo, entao vale a primeira ocorrencia.
    """
    niveis: dict[str, str] = {}
    for alerta in alertas:
        niveis.setdefault(alerta["metrica"], alerta["nivel_novo"])
    return niveis


def nivel_exibido(metrica: str, tem_dados: bool, niveis: dict[str, str], com_regra: set[str]) -> str:
    """Nivel mostrado no cartao da metrica."""
    if not tem_dados:
        return "SEM_DADOS"
    if metrica not in com_regra:
        return INFORMATIVA
    return niveis.get(metrica, "OK")  # tem regra e nunca mudou de nivel: continua OK


def _numero(valor: float) -> str:
    """Numero no padrao brasileiro, com ate 2 casas: 1234.5 -> '1.234,5'."""
    texto = f"{valor:,.2f}".rstrip("0").rstrip(".")
    if texto in ("-0", ""):
        texto = "0"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def formatar_valor(valor: float, unidade: str) -> str:
    if unidade == "0/1":
        return "no ar" if valor >= 1 else "fora do ar"
    return f"{_numero(valor)} {unidade}"


def descrever_limites(regra: dict | None, unidade: str) -> str:
    """Texto dos limites de config/regras.toml (aparece na ajuda de cada cartao)."""
    if regra is None:
        return "Métrica informativa (sem regra de alerta)"
    if unidade == "0/1":
        return "1ª falha = Atenção · 2ª falha seguida = Crítico"
    op = regra["operador"]
    return (f"Atenção {op} {formatar_valor(regra['atencao'], unidade)} · "
            f"Crítico {op} {formatar_valor(regra['critico'], unidade)}")


def hora(ts: int | None) -> str:
    """Epoch em segundos -> 'dd/mm/aaaa hh:mm:ss' no horario da maquina do dashboard."""
    if ts is None:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M:%S")
