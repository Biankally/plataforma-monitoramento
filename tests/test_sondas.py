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


# ---------------------------------------------------------------- MySQL (tarefa 1, P2)
import dns.rcode  # noqa: E402

from plataforma.infra import sondas  # noqa: E402
from tests.falsos.dns_smtp_falsos import DnsFalso, SmtpFalso  # noqa: E402


class _CursorFalso:
    def __init__(self, status: dict, variaveis: dict, tamanho_bytes, falha_na_consulta: str | None):
        self._status, self._variaveis, self._tamanho = status, variaveis, tamanho_bytes
        self._falha = falha_na_consulta
        self._linhas: list = []

    def execute(self, sql: str, *args) -> None:
        if self._falha and self._falha in sql:
            import pymysql
            raise pymysql.err.OperationalError(2013, "perdeu a conexao")
        if sql.strip() == "SELECT 1":
            self._linhas = [(1,)]
        elif sql.startswith("SHOW GLOBAL STATUS"):
            self._linhas = list(self._status.items())
        elif sql.startswith("SHOW GLOBAL VARIABLES"):
            self._linhas = list(self._variaveis.items())
        elif "information_schema.tables" in sql:
            self._linhas = [(self._tamanho,)]
        else:
            raise AssertionError(f"consulta inesperada: {sql}")

    def fetchall(self):
        return self._linhas

    def fetchone(self):
        return self._linhas[0]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _ConexaoFalsa:
    def __init__(self, **kw):
        self.kw = kw
        self.fechada = False

    def cursor(self):
        return _CursorFalso(STATUS, VARIAVEIS, 52_428_800, FALHA["sql"])

    def close(self):
        self.fechada = True


STATUS = {"Questions": "10000", "Com_rollback": "7", "Aborted_connects": "2", "Threads_connected": "5",
          "Threads_running": "1", "Threads_cached": "3", "Slow_queries": "4", "Uptime": "99"}
VARIAVEIS = {"max_connections": "151"}
FALHA = {"sql": None}


def test_sonda_mysql_le_select1_e_contadores(monkeypatch):
    FALHA["sql"] = None
    monkeypatch.setattr(sondas.pymysql, "connect", lambda **kw: _ConexaoFalsa(**kw))
    m = sondas.sonda_mysql("127.0.0.1", 3307, "monitor", "segredo", timeout_s=2)
    assert m["disponivel"] == 1.0 and m["latencia_ms"] >= 0
    assert m["status.Questions"] == 10000.0
    assert m["status.Threads_connected"] == 5.0
    assert m["status.Slow_queries"] == 4.0
    assert m["max_connections"] == 151.0
    assert m["tamanho_mb"] == 50.0
    assert "status.Uptime" not in m  # so entram os contadores que o catalogo usa


def test_sonda_mysql_repassa_credenciais_e_timeout(monkeypatch):
    FALHA["sql"] = None
    vistos = {}

    def falso(**kw):
        vistos.update(kw)
        return _ConexaoFalsa(**kw)

    monkeypatch.setattr(sondas.pymysql, "connect", falso)
    sondas.sonda_mysql("h", 3307, "monitor", "segredo", timeout_s=3)
    assert vistos["host"] == "h" and vistos["port"] == 3307 and vistos["user"] == "monitor"
    assert vistos["password"] == "segredo" and vistos["connect_timeout"] == 3


def test_sabotagem_sonda_mysql_sem_servidor_acusa_fora_do_ar():
    m = sondas.sonda_mysql("127.0.0.1", porta_livre(), "monitor", "x", timeout_s=1)
    assert m == {"disponivel": 0.0, "latencia_ms": m["latencia_ms"]}


def test_sabotagem_sonda_mysql_porta_aberta_mas_nao_e_mysql():
    """O defeito da sonda TCP: a porta aceita a conexao e a sonda dizia 'no ar'."""
    tcp = TcpFalso()
    try:
        m = sondas.sonda_mysql("127.0.0.1", tcp.porta, "monitor", "x", timeout_s=1)
    finally:
        tcp.derrubar()
    assert m["disponivel"] == 0.0


def test_sabotagem_sonda_mysql_consulta_falha_acusa_fora_do_ar(monkeypatch):
    monkeypatch.setattr(sondas.pymysql, "connect", lambda **kw: _ConexaoFalsa(**kw))
    FALHA["sql"] = "SELECT 1"
    try:
        m = sondas.sonda_mysql("h", 3307, "monitor", "x", timeout_s=1)
    finally:
        FALHA["sql"] = None
    assert m["disponivel"] == 0.0 and "status.Questions" not in m


# ---------------------------------------------------------------- DNS
def test_sonda_dns_resposta_valida():
    dns_falso = DnsFalso()
    try:
        m = sondas.sonda_dns("127.0.0.1", dns_falso.porta, "teste.lab.local", timeout_s=2)
    finally:
        dns_falso.derrubar()
    assert m["disponivel"] == 1.0 and 0 <= m["latencia_ms"] < 2000


@pytest.mark.parametrize("rcode", [dns.rcode.SERVFAIL, dns.rcode.REFUSED, dns.rcode.NXDOMAIN])
def test_sabotagem_sonda_dns_resposta_de_erro_acusa_fora_do_ar(rcode):
    dns_falso = DnsFalso(rcode=rcode)
    try:
        m = sondas.sonda_dns("127.0.0.1", dns_falso.porta, "teste.lab.local", timeout_s=2)
    finally:
        dns_falso.derrubar()
    assert m["disponivel"] == 0.0


def test_sabotagem_sonda_dns_sem_resposta_acusa_fora_do_ar():
    mudo = DnsFalso(mudo=True)
    try:
        m = sondas.sonda_dns("127.0.0.1", mudo.porta, "teste.lab.local", timeout_s=0.5)
    finally:
        mudo.derrubar()
    assert m["disponivel"] == 0.0 and m["latencia_ms"] >= 400


def test_sabotagem_sonda_dns_servidor_derrubado():
    dns_falso = DnsFalso()
    porta = dns_falso.porta
    dns_falso.derrubar()
    assert sondas.sonda_dns("127.0.0.1", porta, "teste.lab.local", timeout_s=0.5)["disponivel"] == 0.0


# ---------------------------------------------------------------- SMTP
def test_sonda_smtp_dialogo_completo():
    smtp = SmtpFalso()
    try:
        m = sondas.sonda_smtp("127.0.0.1", smtp.porta, timeout_s=2)
    finally:
        smtp.derrubar()
    assert m["disponivel"] == 1.0 and m["latencia_ms"] >= 0


@pytest.mark.parametrize("kw", [
    {"banner": "421 servico indisponivel"},
    {"banner": "554 sem servico"},
    {"ehlo": "550 recusado"},
])
def test_sabotagem_sonda_smtp_banner_ou_ehlo_ruim(kw):
    smtp = SmtpFalso(**kw)
    try:
        m = sondas.sonda_smtp("127.0.0.1", smtp.porta, timeout_s=2)
    finally:
        smtp.derrubar()
    assert m["disponivel"] == 0.0


def test_sabotagem_sonda_smtp_porta_aberta_mas_nao_e_smtp():
    tcp = TcpFalso()
    try:
        m = sondas.sonda_smtp("127.0.0.1", tcp.porta, timeout_s=1)
    finally:
        tcp.derrubar()
    assert m["disponivel"] == 0.0


def test_sabotagem_sonda_smtp_sem_servidor():
    assert sondas.sonda_smtp("127.0.0.1", porta_livre(), timeout_s=1)["disponivel"] == 0.0
