"""Servicos falsos de DNS (UDP) e SMTP para testar as sondas de P2."""

from __future__ import annotations

import socket
import threading

import dns.flags
import dns.message
import dns.rcode
import dns.rrset

from tests.falsos.servicos_falsos import porta_livre


class DnsFalso:
    """Servidor DNS UDP. `rcode` NOERROR devolve 192.0.2.10; `mudo=True` nunca responde."""

    def __init__(self, rcode: int = dns.rcode.NOERROR, mudo: bool = False) -> None:
        self.porta = porta_livre()
        self._rcode = rcode
        self._mudo = mudo
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("127.0.0.1", self.porta))
        self._sock.settimeout(0.2)
        self._ativo = True
        threading.Thread(target=self._servir, daemon=True).start()

    def _servir(self) -> None:
        while self._ativo:
            try:
                dados, origem = self._sock.recvfrom(512)
            except socket.timeout:
                continue
            except OSError:
                return
            if self._mudo:
                continue
            consulta = dns.message.from_wire(dados)
            resposta = dns.message.make_response(consulta)
            resposta.set_rcode(self._rcode)
            if self._rcode == dns.rcode.NOERROR:
                resposta.answer.append(
                    dns.rrset.from_text(consulta.question[0].name, 60, "IN", "A", "192.0.2.10")
                )
            self._sock.sendto(resposta.to_wire(), origem)

    def derrubar(self) -> None:
        self._ativo = False
        self._sock.close()


class SmtpFalso:
    """Servidor SMTP minimo. `banner` e a primeira linha; `ehlo` e o codigo devolvido ao EHLO."""

    def __init__(self, banner: str = "220 falso.lab.local ESMTP", ehlo: str = "250 falso.lab.local") -> None:
        self.porta = porta_livre()
        self._banner = banner
        self._ehlo = ehlo
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
            except OSError:
                return
            threading.Thread(target=self._atender, args=(conexao,), daemon=True).start()

    def _atender(self, conexao: socket.socket) -> None:
        with conexao, conexao.makefile("rwb") as arq:
            def dizer(linha: str) -> None:
                arq.write((linha + "\r\n").encode())
                arq.flush()

            dizer(self._banner)
            for bruta in arq:
                comando = bruta.decode(errors="replace").strip().upper()
                if comando.startswith("EHLO") or comando.startswith("HELO"):
                    dizer(self._ehlo)
                elif comando.startswith("QUIT"):
                    dizer("221 tchau")
                    return
                else:
                    dizer("502 comando nao implementado")

    def derrubar(self) -> None:
        self._ativo = False
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass  # o shutdown de socket ouvinte nao existe em todo sistema; o close resolve
        self._sock.close()
