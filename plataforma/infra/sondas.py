"""Sondas caixa-preta (camada 2): testam o servico de fora, como um usuario.

HTTP e TCP generico, mais as sondas especificas: SELECT 1 no MySQL, consulta
DNS e dialogo SMTP. Cada uma devolve `disponivel` (0/1) e `latencia_ms`.
Nao esconde erro: cada except lista so as excecoes esperadas de rede/protocolo.
"""

from __future__ import annotations

import smtplib
import socket
import time

import dns.exception
import dns.resolver
import pymysql
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


# Contadores do SHOW GLOBAL STATUS que o catalogo usa (db.*). O Coletor/derivadas
# transforma os acumulados em taxas; aqui so se le o valor bruto.
_STATUS_USADOS = (
    "Questions", "Com_rollback", "Aborted_connects", "Threads_connected",
    "Threads_running", "Threads_cached", "Slow_queries",
)
_BANCOS_DO_SISTEMA = "('information_schema', 'mysql', 'performance_schema', 'sys')"


def sonda_mysql(host: str, porta: int, usuario: str, senha: str, timeout_s: float) -> dict[str, float]:
    """Conecta, executa SELECT 1 e le SHOW GLOBAL STATUS.

    Alem de `disponivel` e `latencia_ms`, devolve (so quando o banco responde):
    `status.<Contador>` brutos, `max_connections` e `tamanho_mb`.
    A latencia e o tempo de conectar + SELECT 1 (os contadores ficam de fora).
    """
    inicio = time.perf_counter()
    try:
        conexao = pymysql.connect(host=host, port=porta, user=usuario, password=senha,
                                  connect_timeout=timeout_s, read_timeout=timeout_s,
                                  write_timeout=timeout_s)
    except (pymysql.MySQLError, OSError):
        return {"disponivel": 0.0, "latencia_ms": (time.perf_counter() - inicio) * 1000}

    try:
        with conexao.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
            latencia_ms = (time.perf_counter() - inicio) * 1000
            cur.execute("SHOW GLOBAL STATUS")
            status = {nome: valor for nome, valor in cur.fetchall()}
            cur.execute("SHOW GLOBAL VARIABLES LIKE 'max_connections'")
            variaveis = {nome: valor for nome, valor in cur.fetchall()}
            cur.execute("SELECT COALESCE(SUM(data_length + index_length), 0) FROM information_schema.tables"
                        f" WHERE table_schema NOT IN {_BANCOS_DO_SISTEMA}")
            tamanho_bytes = cur.fetchone()[0]
    except (pymysql.MySQLError, OSError):
        return {"disponivel": 0.0, "latencia_ms": (time.perf_counter() - inicio) * 1000}
    finally:
        conexao.close()

    medida = {"disponivel": 1.0, "latencia_ms": latencia_ms}
    for nome in _STATUS_USADOS:
        if nome in status:
            medida[f"status.{nome}"] = float(status[nome])
    if "max_connections" in variaveis:
        medida["max_connections"] = float(variaveis["max_connections"])
    medida["tamanho_mb"] = float(tamanho_bytes) / (1024 * 1024)
    return medida


def sonda_dns(host: str, porta: int, nome: str, timeout_s: float) -> dict[str, float]:
    """Consulta A de `nome` direto no servidor. So conta como no ar se houver resposta com dados."""
    resolvedor = dns.resolver.Resolver(configure=False)
    resolvedor.nameservers = [host]
    resolvedor.port = porta
    resolvedor.timeout = timeout_s
    resolvedor.lifetime = timeout_s
    inicio = time.perf_counter()
    try:
        resolvedor.resolve(nome, "A")  # levanta excecao se nao vier resposta com dados
        disponivel = 1.0
    except (dns.exception.DNSException, OSError):
        # NXDOMAIN, resposta vazia (NoAnswer), SERVFAIL/REFUSED (NoNameservers), timeout...
        disponivel = 0.0
    return {"disponivel": disponivel, "latencia_ms": (time.perf_counter() - inicio) * 1000}


def sonda_smtp(host: str, porta: int, timeout_s: float) -> dict[str, float]:
    """Dialogo completo: banner 220, EHLO 250 e QUIT."""
    inicio = time.perf_counter()
    try:
        # smtplib.SMTP() ja confere o banner e levanta SMTPConnectError se nao for 220.
        with smtplib.SMTP(host, porta, timeout=timeout_s, local_hostname="monitor.lab.local") as s:
            codigo, _ = s.ehlo()
            disponivel = 1.0 if codigo == 250 else 0.0
            s.quit()
    except (smtplib.SMTPException, OSError):
        disponivel = 0.0
    return {"disponivel": disponivel, "latencia_ms": (time.perf_counter() - inicio) * 1000}
