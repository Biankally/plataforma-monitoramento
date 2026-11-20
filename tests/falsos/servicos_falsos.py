"""Servicos falsos para os testes: um servidor HTTP e ouvintes TCP que podem ser derrubados."""

from __future__ import annotations

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _Responde(BaseHTTPRequestHandler):
    status = 200

    def do_GET(self):  # noqa: N802 (nome exigido pelo http.server)
        corpo = b"<h1>site falso</h1>"
        self.send_response(self.status)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


class WebFalso:
    def __init__(self, status: int = 200) -> None:
        self.porta = porta_livre()
        manipulador = type("Manipulador", (_Responde,), {"status": status})
        self._servidor = ThreadingHTTPServer(("127.0.0.1", self.porta), manipulador)
        threading.Thread(target=self._servidor.serve_forever, daemon=True).start()

    def derrubar(self) -> None:
        self._servidor.shutdown()
        self._servidor.server_close()


class TcpFalso:
    def __init__(self) -> None:
        self.porta = porta_livre()
        self._sock = socket.socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", self.porta))
        self._sock.listen()
        self._ativo = True
        threading.Thread(target=self._aceitar, daemon=True).start()

    def _aceitar(self) -> None:
        while self._ativo:
            try:
                conexao, _ = self._sock.accept()
                conexao.close()
            except OSError:
                return

    def derrubar(self) -> None:
        self._ativo = False
        try:
            self._sock.shutdown(socket.SHUT_RDWR)  # acorda o accept() bloqueado na outra thread
        except OSError:
            pass  # em alguns sistemas o shutdown de um socket ouvinte nao e suportado; o close abaixo resolve
        self._sock.close()
