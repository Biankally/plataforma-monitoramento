"""Agente de telemetria da VM-S (P1, tarefa 6).

Roda no Linux onde estao os containers (no nosso caso, o WSL) e responde:
    GET /metrics   com o cabecalho X-Token   ->   JSON com as chaves de tests/falsos/agente_exemplo.json

O que cada parte do JSON significa (o coletor da P2 le a cada 15 s):
- apache, unbound .............. contadores ACUMULADOS do servico (a taxa e a diferenca entre duas leituras)
- log_web, postfix (menos fila), auth ... o que aconteceu desde a leitura ANTERIOR (janela)
- containers, host, postfix.fila, hashes ... foto do momento
- versoes ......................... versao de cada programa (guardada por 10 min; vulnerabilidade conhecida)
- campo None = a fonte nao respondeu (container parado etc.); o motivo aparece no terminal do agente.
Por causa da "janela", so o coletor deve ler o /metrics enquanto a plataforma estiver medindo.

Uso:  python servicos/agente/agente.py        (le MONITOR_AGENTE_TOKEN do .env da raiz; porta 9101)
Nao importa nada de plataforma/ (regra de camadas do projeto): e um programa separado.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import agente_fontes as fontes
from agente_log import LeitorIncremental, avisar

RAIZ = Path(__file__).resolve().parent.parent.parent
PREFIXO = "monitoramento"   # nome do projeto no docker-compose.yml
NOMES = {nome: f"{PREFIXO}-{nome}-1" for nome in ("web", "db", "dns", "smtp")}
CONFIGURACOES = {   # arquivos vigiados para detectar alteracao de configuracao
    NOMES["web"]: ["/etc/apache2/apache2.conf", "/etc/apache2/conf-enabled/zz-status.conf"],
    NOMES["dns"]: ["/etc/unbound/unbound.conf"],
    NOMES["smtp"]: ["/etc/postfix/main.cf", "/etc/postfix/master.cf"],
}


class Agente:
    """Junta as fontes num JSON. Uma leitura por vez (as janelas dos logs nao podem se misturar)."""

    def __init__(self, url_status: str, log_acesso: Path, log_login: Path,
                 executor: fontes.Executor = fontes.executar) -> None:
        self.url_status = url_status
        self.executor = executor
        self.acesso = LeitorIncremental(log_acesso)
        self.login = LeitorIncremental(log_login)
        self.log_smtp = fontes.LeitorDockerLogs(executor, NOMES["smtp"])
        self.host = fontes.MedidorHost()
        self.versoes = fontes.LeitorVersoes(executor, NOMES)
        self._trava = threading.Lock()

    def metricas(self) -> dict:
        # As consultas ao Docker demoram (docker stats leva ~2 s); rodando ao mesmo tempo, a resposta
        # inteira fica no tempo da mais lenta, abaixo do limite de 5 s do coletor.
        with self._trava, ThreadPoolExecutor(max_workers=8) as paralelo:
            tarefas = {
                "apache": paralelo.submit(fontes.apache_status, self.url_status),
                "unbound": paralelo.submit(fontes.unbound, self.executor, NOMES["dns"], "/etc/unbound/unbound.conf"),
                "postfix": paralelo.submit(fontes.postfix, self.executor, NOMES["smtp"], self.log_smtp),
                "containers": paralelo.submit(fontes.containers, self.executor, NOMES),
                "hashes": paralelo.submit(fontes.hashes, self.executor, CONFIGURACOES),
                "versoes": paralelo.submit(self.versoes.ler),
            }
            leitura = {
                "ts": int(time.time()),
                "log_web": fontes.resumir_log_web(self.acesso.linhas_novas()),
                "auth": fontes.tentativas(self.login.linhas_novas()),
                "host": self.host.medir(),
            }
            leitura.update({nome: tarefa.result() for nome, tarefa in tarefas.items()})
        ordem = ["ts", "apache", "log_web", "unbound", "postfix", "auth", "containers", "host", "hashes", "versoes"]
        return {chave: leitura[chave] for chave in ordem}


def criar_servidor(agente: Agente, token: str, host: str, porta: int) -> ThreadingHTTPServer:
    if not token:
        raise ValueError("MONITOR_AGENTE_TOKEN vazio: defina no .env da raiz")

    class Manipulador(BaseHTTPRequestHandler):
        def _responder(self, status: int, dados: dict) -> None:
            corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self):  # noqa: N802 (nome exigido pelo http.server)
            recebido = self.headers.get("X-Token", "")
            if not hmac.compare_digest(recebido.encode(), token.encode()):  # compara sem vazar tempo
                self._responder(401, {"erro": "token ausente ou invalido"})
            elif self.path.split("?")[0] != "/metrics":
                self._responder(404, {"erro": "rota inexistente; use /metrics"})
            else:
                self._responder(200, agente.metricas())

        def log_message(self, formato, *args):
            avisar(f"{self.address_string()} {formato % args}")

    return ThreadingHTTPServer((host, porta), Manipulador)


def carregar_env(arquivo: Path) -> None:
    """Le CHAVE=valor do .env sem sobrescrever o que ja esta no ambiente."""
    if not arquivo.is_file():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def main(argv: list[str] | None = None) -> int:
    carregar_env(RAIZ / ".env")
    p = argparse.ArgumentParser(description="Agente de telemetria da VM-S")
    p.add_argument("--host", default=os.environ.get("AGENTE_HOST", "127.0.0.1"))
    p.add_argument("--porta", type=int, default=int(os.environ.get("AGENTE_PORTA", "9101")))
    p.add_argument("--logs", type=Path, default=RAIZ / "servicos" / "logs" / "web",
                   help="pasta com acesso.log e login.log do container web")
    p.add_argument("--status", default="http://127.0.0.1:8080/server-status?auto")
    args = p.parse_args(argv)

    token = os.environ.get("MONITOR_AGENTE_TOKEN", "")
    try:
        servidor = criar_servidor(Agente(args.status, args.logs / "acesso.log", args.logs / "login.log"),
                                  token, args.host, args.porta)
    except (ValueError, OSError) as e:
        print(f"[agente] nao foi possivel iniciar: {e}", file=sys.stderr)
        return 1
    print(f"[agente] ouvindo em http://{args.host}:{args.porta}/metrics", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("[agente] encerrado", flush=True)
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
