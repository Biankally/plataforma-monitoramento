import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from plataforma.infra.agente_cliente import ErroAgente, ler_metricas
from tests.falsos.servicos_falsos import porta_livre

EXEMPLO = Path(__file__).parent / "falsos" / "agente_exemplo.json"
TOKEN = "token-de-teste"


class AgenteFalso:
    """Serve GET /metrics exigindo X-Token, como o agente real."""

    def __init__(self, corpo: bytes | None = None, status: int = 200) -> None:
        self.porta = porta_livre()
        self.tokens_recebidos: list = []
        self.caminhos: list = []
        corpo = EXEMPLO.read_bytes() if corpo is None else corpo
        dono = self

        class Manipulador(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                dono.caminhos.append(self.path)
                dono.tokens_recebidos.append(self.headers.get("X-Token"))
                if self.headers.get("X-Token") != TOKEN:
                    self.send_response(401)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                self.send_response(status)
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def log_message(self, *args):
                pass

        self._servidor = ThreadingHTTPServer(("127.0.0.1", self.porta), Manipulador)
        threading.Thread(target=self._servidor.serve_forever, daemon=True).start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.porta}"

    def derrubar(self) -> None:
        self._servidor.shutdown()
        self._servidor.server_close()


@pytest.fixture
def agente():
    a = AgenteFalso()
    yield a
    a.derrubar()


def test_le_o_json_do_agente_com_o_token(agente):
    dados = ler_metricas(agente.url, TOKEN, timeout_s=2)
    assert dados == json.loads(EXEMPLO.read_text(encoding="utf-8"))
    assert agente.caminhos == ["/metrics"] and agente.tokens_recebidos == [TOKEN]


def test_barra_no_fim_da_url_nao_atrapalha(agente):
    assert ler_metricas(agente.url + "/", TOKEN, timeout_s=2)["ts"] == 1795036800


def test_sabotagem_token_errado_acusa_erro(agente):
    with pytest.raises(ErroAgente, match="401"):
        ler_metricas(agente.url, "token-errado", timeout_s=2)


def test_sabotagem_agente_fora_do_ar_acusa_erro():
    with pytest.raises(ErroAgente):
        ler_metricas(f"http://127.0.0.1:{porta_livre()}", TOKEN, timeout_s=1)


@pytest.mark.parametrize("corpo", [b"isto nao e json", b"[1, 2, 3]", b'"texto"'])
def test_sabotagem_resposta_que_nao_e_objeto_json_acusa_erro(corpo):
    a = AgenteFalso(corpo=corpo)
    try:
        with pytest.raises(ErroAgente):
            ler_metricas(a.url, TOKEN, timeout_s=2)
    finally:
        a.derrubar()


def test_sabotagem_erro_500_do_agente_acusa_erro():
    a = AgenteFalso(status=500)
    try:
        with pytest.raises(ErroAgente, match="500"):
            ler_metricas(a.url, TOKEN, timeout_s=2)
    finally:
        a.derrubar()
