import pytest

from plataforma.infra.sondas import sonda_http, sonda_tcp
from tests.falsos.servicos_falsos import TcpFalso, WebFalso, porta_livre


@pytest.mark.parametrize("status, esperado", [(200, 1.0), (404, 1.0), (500, 0.0), (503, 0.0)])
def test_sonda_http_pelo_codigo_de_resposta(status, esperado):
    web = WebFalso(status=status)
    try:
        medida = sonda_http(f"http://127.0.0.1:{web.porta}/", timeout_s=2)
    finally:
        web.derrubar()
    assert medida["disponivel"] == esperado and medida["latencia_ms"] >= 0


def test_sabotagem_sonda_http_sem_servidor_acusa_fora_do_ar():
    assert sonda_http(f"http://127.0.0.1:{porta_livre()}/", timeout_s=1)["disponivel"] == 0.0


def test_sonda_tcp_no_ar_e_fora_do_ar():
    tcp = TcpFalso()
    assert sonda_tcp("127.0.0.1", tcp.porta, 1)["disponivel"] == 1.0
    tcp.derrubar()
    assert sonda_tcp("127.0.0.1", tcp.porta, 1)["disponivel"] == 0.0
