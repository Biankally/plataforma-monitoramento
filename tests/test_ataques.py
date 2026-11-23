"""Testes dos scripts de ataque (testes/), contra servidores falsos: nao precisam de containers."""

from __future__ import annotations

import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import pytest

from tests.falsos.servicos_falsos import WebFalso, porta_livre

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "testes"))

import alvo_local  # noqa: E402
import ataque_brute_force  # noqa: E402
import ataque_ddos  # noqa: E402
import teste_isolamento  # noqa: E402


# ---------- trava de seguranca: so ataca a propria maquina ----------

@pytest.mark.parametrize("url", ["http://127.0.0.1:8080/", "http://localhost:8080/x"])
def test_alvo_local_aceita_a_propria_maquina(url):
    assert alvo_local.garantir(url) == url


@pytest.mark.parametrize("url", ["http://192.168.0.10/", "https://idp.edu.br/", "http://10.0.0.1:8080/",
                                 "http://127.0.0.1.exemplo.com/"])
def test_sabotagem_alvo_fora_da_maquina_e_recusado(url):
    with pytest.raises(SystemExit):
        alvo_local.garantir(url)


# ---------- DDoS (inundacao HTTP) ----------

def test_ddos_manda_requisicoes_e_conta_respostas():
    web = WebFalso()
    try:
        resumo = ataque_ddos.inundar(f"http://127.0.0.1:{web.porta}/", segundos=1.0, conexoes=4, mostrar=False)
    finally:
        web.derrubar()
    assert resumo["requisicoes"] > 20
    assert resumo["por_codigo"] == {"200": resumo["requisicoes"]}
    assert resumo["falhas"] == 0


def test_ddos_conta_falhas_quando_o_alvo_cai():
    resumo = ataque_ddos.inundar(f"http://127.0.0.1:{porta_livre()}/", segundos=0.5, conexoes=2, mostrar=False)
    assert resumo["requisicoes"] == 0 and resumo["falhas"] > 0


# ---------- forca bruta no login ----------

SENHA_CERTA = "dragon"


class _LoginFalso(BaseHTTPRequestHandler):
    tentativas = 0

    def do_POST(self):  # noqa: N802
        tamanho = int(self.headers.get("Content-Length", 0))
        campos = parse_qs(self.rfile.read(tamanho).decode())
        type(self).tentativas += 1
        if campos.get("senha") == [SENHA_CERTA]:
            self.send_response(302)
            self.send_header("Location", "suaconta.php")
            corpo = b""
        else:
            self.send_response(200)
            corpo = "<script>alert('Senha incorreta.')</script>".encode()
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


@pytest.fixture
def login_falso():
    _LoginFalso.tentativas = 0
    porta = porta_livre()
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), _LoginFalso)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{porta}/login.php"
    servidor.shutdown()
    servidor.server_close()


def test_forca_bruta_acha_a_senha_da_lista(login_falso):
    resultado = ataque_brute_force.atacar(login_falso, "vitima@lab.local", ataque_brute_force.LISTA,
                                          por_segundo=0, mostrar=False)
    assert resultado["senha"] == SENHA_CERTA
    assert resultado["tentativas"] == ataque_brute_force.LISTA.index(SENHA_CERTA) + 1


def test_forca_bruta_para_no_limite_sem_achar(login_falso):
    lista = ["a", "b", "c", "d"]
    resultado = ataque_brute_force.atacar(login_falso, "vitima@lab.local", lista, por_segundo=0, mostrar=False)
    assert resultado == {"senha": None, "tentativas": 4}
    assert _LoginFalso.tentativas == 4


# ---------- teste de isolamento ----------

def test_isolamento_aprova_quando_os_outros_respondem():
    sondas = {"db": lambda: True, "dns": lambda: True, "smtp": lambda: True}
    relatorio = teste_isolamento.vigiar(sondas, segundos=0.5, intervalo_s=0.1)
    assert relatorio["aprovado"] is True
    assert all(r["ok"] == r["total"] > 0 for r in relatorio["servicos"].values())


def test_sabotagem_isolamento_reprova_se_um_servico_cai():
    def dns_caindo():
        raise OSError("sem resposta")
    sondas = {"db": lambda: True, "dns": dns_caindo, "smtp": lambda: True}
    relatorio = teste_isolamento.vigiar(sondas, segundos=0.5, intervalo_s=0.1)
    assert relatorio["aprovado"] is False
    assert relatorio["servicos"]["dns"]["ok"] == 0
