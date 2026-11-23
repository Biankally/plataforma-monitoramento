"""Contrato de dados da plataforma (camada 0).

Tudo o que as partes trocam entre si passa por aqui: os nomes das metricas,
os niveis de alerta e o formato do lote enviado pelo Coletor para a API.
Ninguem muda este arquivo sem combinar com o grupo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SERVICOS: tuple[str, ...] = ("web", "db", "dns", "smtp", "host")

NIVEIS: tuple[str, ...] = ("OK", "ATENCAO", "CRITICO")
SEM_DADOS = "SEM_DADOS"

# Catalogo fechado: nome -> (unidade, descricao). Metrica fora daqui e recusada.
METRICAS: dict[str, tuple[str, str]] = {
    # Servidor web
    "web.disponivel": ("0/1", "Responde HTTP com status < 500"),
    "web.latencia_ms": ("ms", "Tempo total da sonda HTTP"),
    "web.latencia_p95_ms": ("ms", "Percentil 95 do tempo de servidor (log)"),
    "web.rps": ("req/s", "Requisicoes por segundo (mod_status)"),
    "web.taxa_erro_4xx_pct": ("%", "Respostas 4xx sobre o total da janela"),
    "web.taxa_erro_5xx_pct": ("%", "Respostas 5xx sobre o total da janela"),
    "web.req_4xx": ("requisicoes", "Contagem de respostas 4xx na janela"),
    "web.req_5xx": ("requisicoes", "Contagem de respostas 5xx na janela"),
    "web.conexoes_ativas": ("conexoes", "ConnsTotal do mod_status"),
    # Banco de dados
    "db.disponivel": ("0/1", "Conecta e executa SELECT 1"),
    "db.latencia_ms": ("ms", "Tempo da sonda do banco"),
    "db.qps": ("consultas/s", "Diferenca de Questions por segundo"),
    "db.rollbacks_s": ("/s", "Diferenca de Com_rollback por segundo"),
    "db.conexoes_abortadas": ("conexoes", "Diferenca de Aborted_connects"),
    "db.conexoes": ("conexoes", "Threads_connected"),
    "db.conexoes_executando": ("conexoes", "Threads_running"),
    "db.uso_conexoes_pct": ("%", "Threads_connected / max_connections"),
    "db.threads_cache": ("threads", "Threads_cached"),
    "db.tamanho_mb": ("MB", "data_length + index_length"),
    "db.crescimento_mb_dia": ("MB/dia", "Crescimento projetado para 24 h"),
    "db.slow_queries_min": ("consultas/min", "Diferenca de Slow_queries por minuto"),
    "db.cpu_pct": ("%", "Uso de CPU do container do banco (docker stats)"),
    "db.mem_pct": ("%", "Uso de memoria do container do banco sobre o limite (docker stats)"),
    # DNS
    "dns.disponivel": ("0/1", "Resposta valida em ate 2 s"),
    "dns.latencia_ms": ("ms", "Tempo de resolucao da consulta de teste"),
    "dns.qps": ("consultas/s", "Diferenca de total.num.queries por segundo"),
    "dns.taxa_erro_pct": ("%", "SERVFAIL + REFUSED + falhas da sonda sobre o total"),
    # SMTP
    "smtp.disponivel": ("0/1", "Banner 220, EHLO e QUIT na porta 25"),
    "smtp.latencia_ms": ("ms", "Tempo do dialogo da sonda SMTP"),
    "smtp.taxa_entrega_pct": ("%", "sent / (sent + deferred + bounced)"),
    "smtp.fila": ("mensagens", "Mensagens na fila (postqueue -j)"),
    "smtp.latencia_envio_s": ("s", "Media do campo delay= do log"),
    "smtp.rejeicoes": ("contagem", "Linhas reject no log da janela"),
    "smtp.timeouts": ("contagem", "Linhas timeout no log da janela"),
    "smtp.taxa_erro_pct": ("%", "(rejeicoes + timeouts) sobre o total"),
    "smtp.emails_min": ("e-mails/min", "Mensagens enviadas por minuto"),
    # Maquina / containers
    "host.cpu_pct": ("%", "Uso de CPU"),
    "host.mem_pct": ("%", "Uso de memoria"),
    "host.disco_io_kbs": ("KB/s", "Leitura + escrita em disco"),
    "host.disco_latencia_ms": ("ms", "Tempo de I/O por operacao"),
}


class ErroContrato(ValueError):
    """Dado que nao respeita o contrato."""


@dataclass(frozen=True)
class Amostra:
    servico: str
    metrica: str
    valor: float


@dataclass(frozen=True)
class Lote:
    ts: int
    amostras: tuple[Amostra, ...]


def servico_da_metrica(metrica: str) -> str:
    return metrica.split(".", 1)[0]


def validar_lote(dados: object) -> Lote:
    """Converte o JSON recebido em Lote ou levanta ErroContrato explicando o motivo."""
    if not isinstance(dados, dict):
        raise ErroContrato("o lote precisa ser um objeto JSON")
    ts = dados.get("ts")
    if not isinstance(ts, int) or isinstance(ts, bool) or ts <= 0:
        raise ErroContrato("'ts' precisa ser um inteiro positivo (epoch UTC em segundos)")
    brutas = dados.get("amostras")
    if not isinstance(brutas, list) or not brutas:
        raise ErroContrato("'amostras' precisa ser uma lista nao vazia")

    amostras = []
    for i, a in enumerate(brutas):
        if not isinstance(a, dict):
            raise ErroContrato(f"amostra {i}: precisa ser um objeto")
        servico, metrica, valor = a.get("servico"), a.get("metrica"), a.get("valor")
        if metrica not in METRICAS:
            raise ErroContrato(f"amostra {i}: metrica fora do catalogo: {metrica!r}")
        if servico != servico_da_metrica(metrica):
            raise ErroContrato(f"amostra {i}: servico {servico!r} nao bate com a metrica {metrica!r}")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
            raise ErroContrato(f"amostra {i}: 'valor' precisa ser um numero finito")
        amostras.append(Amostra(servico, metrica, float(valor)))
    return Lote(ts, tuple(amostras))
