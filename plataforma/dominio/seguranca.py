"""Regras de seguranca (camada 1, Python puro: sem rede, banco, arquivo ou e-mail).

Tres deteccoes, cada uma devolve EventoSeguranca (o tipo bate com o CHECK da tabela evento_seguranca):
- TRAFEGO (DDoS): escore z do valor atual contra o historico recente (z >= 3 ATENCAO, z >= 5 CRITICO).
- AUTENTICACAO (forca bruta): falhas de login por IP em 60 s (5 = ATENCAO, 20 = CRITICO).
- CONFIGURACAO: hash de arquivo diferente da linha de base (sempre CRITICO).

Quem chama (a API) guarda os eventos e usa `deve_emitir` para nao repetir o mesmo aviso a cada ciclo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

MINIMO_AMOSTRAS = 20      # historico minimo para o escore z fazer sentido
Z_ATENCAO = 3.0
Z_CRITICO = 5.0
JANELA_LOGIN_S = 60
FALHAS_ATENCAO = 5
FALHAS_CRITICO = 20
COOLDOWN_S = 300          # um mesmo aviso so se repete depois disto (ou se o nivel subir)

# Metricas vigiadas pelo escore z e o piso do desvio (mesma unidade da metrica: req/s, consultas/s).
PISO_DESVIO_TRAFEGO = {"web.rps": 5.0, "dns.qps": 5.0}

_ORDEM = {None: 0, "ATENCAO": 1, "CRITICO": 2}


@dataclass(frozen=True)
class EventoSeguranca:
    tipo: str            # TRAFEGO, AUTENTICACAO, CONFIGURACAO
    servico: str
    nivel: str           # ATENCAO ou CRITICO
    origem: str | None   # IP de origem ou caminho do arquivo
    detalhe: str
    valor: float         # z, numero de falhas ou 1 (hash)
    limite: float | None


def _media_e_desvio(historico: list[float]) -> tuple[float, float]:
    media = sum(historico) / len(historico)
    variancia = sum((x - media) ** 2 for x in historico) / len(historico)
    return media, math.sqrt(variancia)


def escore_z(historico: list[float], valor: float, piso_desvio: float) -> float | None:
    """(valor - media) / desvio. O `piso_desvio` evita z enorme quando o historico e quase constante.

    None quando ha menos de MINIMO_AMOSTRAS no historico.
    """
    if len(historico) < MINIMO_AMOSTRAS:
        return None
    media, desvio = _media_e_desvio(historico)
    return (valor - media) / max(desvio, piso_desvio)


def avaliar_trafego(servico: str, metrica: str, historico: list[float], valor: float,
                    piso_desvio: float) -> EventoSeguranca | None:
    z = escore_z(historico, valor, piso_desvio)
    if z is None or z < Z_ATENCAO:  # so o aumento e suspeito; queda de trafego nao e DDoS
        return None
    nivel, limite = ("CRITICO", Z_CRITICO) if z >= Z_CRITICO else ("ATENCAO", Z_ATENCAO)
    media, desvio = _media_e_desvio(historico)
    detalhe = f"{metrica} = {valor:.1f} (media {media:.1f}, desvio {desvio:.1f}, z = {z:.1f})"
    return EventoSeguranca("TRAFEGO", servico, nivel, None, detalhe, z, limite)


def avaliar_login(falhas_por_ip: dict[str, int]) -> list[EventoSeguranca]:
    """`falhas_por_ip`: falhas de login de cada IP nos ultimos 60 s. Cada IP e avaliado sozinho."""
    eventos = []
    for ip, falhas in falhas_por_ip.items():
        if falhas >= FALHAS_CRITICO:
            nivel, limite = "CRITICO", FALHAS_CRITICO
        elif falhas >= FALHAS_ATENCAO:
            nivel, limite = "ATENCAO", FALHAS_ATENCAO
        else:
            continue
        eventos.append(EventoSeguranca("AUTENTICACAO", "web", nivel, ip,
                                       f"{falhas} falhas de login em {JANELA_LOGIN_S} s", float(falhas), float(limite)))
    return eventos


def servico_do_arquivo(caminho: str) -> str:
    c = caminho.lower()
    for trecho, servico in (("postfix", "smtp"), ("unbound", "dns"), ("named", "dns"), ("mysql", "db"),
                            ("my.cnf", "db"), ("mariadb", "db"), ("apache", "web"), ("nginx", "web"),
                            ("httpd", "web"), ("/var/www", "web")):
        if trecho in c:
            return servico
    return "host"


def avaliar_hashes(atual: dict[str, str], base: dict[str, str]) -> list[EventoSeguranca]:
    """Arquivo da linha de base cujo hash mudou. Arquivo novo ou ausente nao gera evento."""
    eventos = []
    for caminho, hash_base in base.items():
        hash_atual = atual.get(caminho)
        if hash_atual is None or hash_atual == hash_base:
            continue
        detalhe = f"hash {hash_atual[:12]} difere da linha de base {hash_base[:12]}"
        eventos.append(EventoSeguranca("CONFIGURACAO", servico_do_arquivo(caminho), "CRITICO",
                                       caminho, detalhe, 1.0, None))
    return eventos


def deve_emitir(nivel_novo: str, ultimo_nivel: str | None) -> bool:
    """True se o nivel novo for maior que o ultimo ja avisado (None = nunca avisado)."""
    return _ORDEM[nivel_novo] > _ORDEM[ultimo_nivel]


def maior_nivel(niveis: list[str]) -> str | None:
    return max(niveis, key=lambda n: _ORDEM[n]) if niveis else None


def alerta_do_evento(evento: EventoSeguranca, ts: int) -> dict:
    """Dicionario no formato que o notificador usa (mesmas chaves dos alertas de metrica, mais `detalhe`)."""
    return dict(ts=ts, servico=evento.servico, metrica=f"seguranca.{evento.tipo.lower()}",
                nivel_anterior="OK", nivel_novo=evento.nivel, valor=round(evento.valor, 3),
                limite=evento.limite, detalhe=evento.detalhe + (f" [origem: {evento.origem}]" if evento.origem else ""))
