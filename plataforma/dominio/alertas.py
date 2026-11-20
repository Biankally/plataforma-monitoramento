"""Motor de alertas (camada 1): maquina de estados com histerese.

Python puro, sem rede, banco ou e-mail: recebe uma regra, o estado atual e um
valor, e devolve o novo estado. Por isso e testavel isoladamente.

- Subir de nivel: a condicao precisa se repetir `subir` amostras seguidas.
- Descer de nivel: `descer` amostras seguidas abaixo do nivel atual.
- atencao_imediata (disponibilidade): a 1a falha ja vai para ATENCAO;
  a falha seguinte completa as `subir` e vai para CRITICO.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from plataforma.contrato.metricas import NIVEIS

_ORDEM = {nivel: i for i, nivel in enumerate(NIVEIS)}


@dataclass(frozen=True)
class Regra:
    metrica: str
    operador: str  # ">" para maximos, "<" para minimos
    atencao: float
    critico: float
    subir: int = 2
    descer: int = 3
    atencao_imediata: bool = False

    def __post_init__(self) -> None:
        if self.operador not in (">", "<"):
            raise ValueError(f"{self.metrica}: operador deve ser '>' ou '<'")
        if self.subir < 1 or self.descer < 1:
            raise ValueError(f"{self.metrica}: subir e descer precisam ser >= 1")


@dataclass(frozen=True)
class Estado:
    nivel: str = "OK"
    seq_violacao: int = 0
    seq_normal: int = 0


def regra_de_dict(metrica: str, d: dict) -> Regra:
    return Regra(metrica=metrica, **d)


def classificar(regra: Regra, valor: float) -> str:
    """Nivel que este valor sozinho indicaria."""
    passou = (lambda limite: valor > limite) if regra.operador == ">" else (lambda limite: valor < limite)
    if passou(regra.critico):
        return "CRITICO"
    if passou(regra.atencao):
        return "ATENCAO"
    return "OK"


def avaliar(regra: Regra, estado: Estado, valor: float) -> tuple[Estado, bool]:
    """Devolve (novo_estado, mudou_de_nivel)."""
    alvo = classificar(regra, valor)
    atual = estado.nivel

    if _ORDEM[alvo] > _ORDEM[atual]:
        seq = estado.seq_violacao + 1
        if seq >= regra.subir:
            return Estado(nivel=alvo), True
        if regra.atencao_imediata and atual == "OK":
            # Mantem a contagem: a proxima falha completa `subir` e vai a CRITICO.
            return Estado(nivel="ATENCAO", seq_violacao=seq), True
        return replace(estado, seq_violacao=seq, seq_normal=0), False

    if _ORDEM[alvo] < _ORDEM[atual]:
        seq = estado.seq_normal + 1
        if seq >= regra.descer:
            return Estado(nivel=alvo), True
        return replace(estado, seq_normal=seq, seq_violacao=0), False

    return Estado(nivel=atual), False


def pior_nivel(niveis: list[str]) -> str:
    return max(niveis, key=lambda n: _ORDEM[n]) if niveis else "OK"
