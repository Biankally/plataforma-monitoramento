"""Testes do agente de telemetria (servicos/agente), sem containers.

O Docker e trocado por um executor falso (dicionario comando -> saida), os logs sao arquivos
temporarios e o Apache e um servidor HTTP falso. Assim o teste roda igual no GitHub Actions.
"""

from __future__ import annotations

import ast
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import requests

from tests.falsos.servicos_falsos import porta_livre

RAIZ = Path(__file__).resolve().parent.parent
PASTA_AGENTE = RAIZ / "servicos" / "agente"
sys.path.insert(0, str(PASTA_AGENTE))

import agente  # noqa: E402  (precisa vir depois do sys.path)
import agente_fontes as fontes  # noqa: E402
from agente_log import LeitorIncremental  # noqa: E402

EXEMPLO = json.loads((RAIZ / "tests" / "falsos" / "agente_exemplo.json").read_text(encoding="utf-8"))
TOKEN = "token-de-teste"

STATUS_APACHE = "Total Accesses: 15230\nTotal kBytes: 99\nBusyWorkers: 2\nIdleWorkers: 3\nConnsTotal: 4\n"
STATS_UNBOUND = ("total.num.queries=8421\nnum.answer.rcode.NOERROR=8000\nnum.answer.rcode.SERVFAIL=3\n"
                 "num.answer.rcode.NXDOMAIN=5\nnum.answer.rcode.REFUSED=0\n")
LOG_POSTFIX = [
    "2026-11-20T18:00:01.100000000Z Nov 20 18:00:01 smtp postfix/virtual[1]: A1: to=<ana@lab.local>, "
    "relay=virtual, delay=0.5, delays=0/0/0/0, dsn=2.0.0, status=sent (delivered to maildir)",
    "2026-11-20T18:00:02.200000000Z Nov 20 18:00:02 smtp postfix/smtp[2]: B2: to=<x@longe.com>, "
    "relay=none, delay=1.5, dsn=4.4.1, status=deferred (connect timed out)",
    "2026-11-20T18:00:03.300000000Z Nov 20 18:00:03 smtp postfix/smtpd[3]: NOQUEUE: reject: RCPT from x",
    "2026-11-20T18:00:04.400000000Z Nov 20 18:00:04 smtp postfix/smtpd[3]: timeout after DATA from x",
]


class ExecutorFalso:
    """Faz o papel do comando docker. `respostas` liga um pedaco do comando a uma saida."""

    def __init__(self) -> None:
        self.respostas: dict[str, str] = {
            "stats_noreset": STATS_UNBOUND,
            "postqueue": '{"queue_name": "deferred"}\n{"queue_name": "active"}\n',
            "docker logs": "\n".join(LOG_POSTFIX) + "\n",
            "docker stats": ("monitoramento-web-1\t12.50%\t48.10%\nmonitoramento-db-1\t3.00%\t30.20%\n"
                             "monitoramento-dns-1\t0.10%\t2.00%\nmonitoramento-smtp-1\t0.20%\t3.00%\n"),
            "sha256sum": "9f2c" + "0" * 58 + "aa  /etc/postfix/main.cf\n",
        }
        self.fora_do_ar: set[str] = set()

    def __call__(self, argv: list[str]) -> str:
        comando = " ".join(argv)
        for pedaco in self.fora_do_ar:
            if pedaco in comando:
                raise fontes.ErroFonte(f"falso: {pedaco} fora do ar")
        for pedaco, saida in self.respostas.items():
            if pedaco in comando:
                return saida
        raise fontes.ErroFonte(f"comando nao previsto no teste: {comando}")


class _ApacheFalso(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        corpo = STATUS_APACHE.encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


@pytest.fixture
def ambiente(tmp_path):
    """Sobe Apache falso e o agente com executor falso; devolve (url_do_agente, pastas, executor)."""
    porta_apache = porta_livre()
    apache = ThreadingHTTPServer(("127.0.0.1", porta_apache), _ApacheFalso)
    threading.Thread(target=apache.serve_forever, daemon=True).start()

    logs_web = tmp_path / "web"
    logs_web.mkdir()
    executor = ExecutorFalso()
    ag = agente.Agente(
        url_status=f"http://127.0.0.1:{porta_apache}/server-status?auto",
        log_acesso=logs_web / "acesso.log",
        log_login=logs_web / "login.log",
        executor=executor,
    )
    porta = porta_livre()
    servidor = agente.criar_servidor(ag, TOKEN, "127.0.0.1", porta)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{porta}/metrics", logs_web, executor
    servidor.shutdown()
    servidor.server_close()
    apache.shutdown()
    apache.server_close()


def _ler(url):
    r = requests.get(url, headers={"X-Token": TOKEN}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


# ---------- contrato ----------

def test_json_tem_as_mesmas_chaves_do_exemplo(ambiente):
    url, _, _ = ambiente
    dados = _ler(url)
    assert set(dados) == set(EXEMPLO)
    for secao in ["apache", "log_web", "unbound", "postfix", "host"]:
        assert set(dados[secao]) == set(EXEMPLO[secao]), f"chaves diferentes em '{secao}'"
    for nome in EXEMPLO["containers"]:
        assert set(dados["containers"][nome]) == set(EXEMPLO["containers"][nome])
    assert isinstance(dados["ts"], int)
    assert all(len(h) == 64 for h in dados["hashes"].values() if h is not None)


def test_valores_lidos_das_fontes(ambiente):
    url, _, _ = ambiente
    dados = _ler(url)
    assert dados["apache"] == {"total_accesses": 15230, "conns_total": 4, "busy_workers": 2}
    assert dados["unbound"]["total.num.queries"] == 8421
    assert dados["unbound"]["num.answer.rcode.SERVFAIL"] == 3
    assert dados["containers"]["web"] == {"cpu_pct": 12.5, "mem_pct": 48.1}
    assert dados["postfix"]["fila"] == 2
    assert dados["hashes"]["/etc/postfix/main.cf"].startswith("9f2c")
    assert 0 <= dados["host"]["cpu_pct"] <= 100 and 0 < dados["host"]["mem_pct"] <= 100


def test_postfix_conta_cada_situacao_do_log():
    resumo = fontes.resumir_postfix(LOG_POSTFIX)
    assert resumo == {"sent": 1, "deferred": 1, "bounced": 0, "rejeicoes": 1, "timeouts": 1,
                      "delay_medio_s": 1.0}


def test_log_web_conta_codigos_e_tempos():
    resumo = fontes.resumir_log_web(["200 1830", "200 2210", "404 950", "500 120", "linha quebrada"])
    assert resumo == {"total": 4, "por_codigo": {"200": 2, "404": 1, "500": 1},
                      "tempo_servidor_us": [1830, 2210, 950, 120]}


# ---------- seguranca: token ----------

def test_sem_token_ou_token_errado_recebe_401(ambiente):
    url, _, _ = ambiente
    assert requests.get(url, timeout=10).status_code == 401
    assert requests.get(url, headers={"X-Token": "errado"}, timeout=10).status_code == 401


def test_rota_inexistente_recebe_404(ambiente):
    url, _, _ = ambiente
    assert requests.get(url.replace("/metrics", "/outra"), headers={"X-Token": TOKEN}, timeout=10).status_code == 404


# ---------- logs: so linhas novas ----------

def _tentativa(usuario, sucesso):
    return json.dumps({"ts": 1795036790, "origem": "172.18.0.1", "usuario": usuario, "sucesso": sucesso}) + "\n"


def test_login_entrega_so_as_tentativas_novas(ambiente):
    url, logs_web, _ = ambiente
    log = logs_web / "login.log"
    with log.open("a", encoding="utf-8") as f:
        f.write(_tentativa("ana@lab.local", False) + _tentativa("ana@lab.local", True))
    assert [t["sucesso"] for t in _ler(url)["auth"]] == [False, True]
    assert _ler(url)["auth"] == [], "a segunda leitura repetiu tentativas ja entregues"
    with log.open("a", encoding="utf-8") as f:
        f.write(_tentativa("bruno@lab.local", False))
    assert [t["usuario"] for t in _ler(url)["auth"]] == ["bruno@lab.local"]


def test_sabotagem_log_rotacionado_nao_quebra(tmp_path):
    log = tmp_path / "login.log"
    log.write_text("linha 1\nlinha 2\n", encoding="utf-8")
    leitor = LeitorIncremental(log, desde_o_inicio=True)
    assert leitor.linhas_novas() == ["linha 1", "linha 2"]
    log.write_text("nova\n", encoding="utf-8")          # rotacao: arquivo recomecou menor
    assert leitor.linhas_novas() == ["nova"]
    log.unlink()                                          # arquivo sumiu
    assert leitor.linhas_novas() == []
    log.write_text("voltou\n", encoding="utf-8")
    assert leitor.linhas_novas() == ["voltou"]


def test_linha_pela_metade_espera_o_resto(tmp_path):
    log = tmp_path / "acesso.log"
    log.write_text("200 10\n200 2", encoding="utf-8")
    leitor = LeitorIncremental(log, desde_o_inicio=True)
    assert leitor.linhas_novas() == ["200 10"]
    with log.open("a", encoding="utf-8") as f:
        f.write("0\n")
    assert leitor.linhas_novas() == ["200 20"]


def test_comeca_do_fim_para_nao_contar_historico(tmp_path):
    log = tmp_path / "login.log"
    log.write_text("antiga\n", encoding="utf-8")
    leitor = LeitorIncremental(log)
    assert leitor.linhas_novas() == []


# ---------- fonte fora do ar ----------

def test_sabotagem_fonte_fora_do_ar_vira_null_sem_derrubar_o_agente(ambiente):
    url, _, executor = ambiente
    executor.fora_do_ar = {"stats_noreset", "postqueue", "sha256sum"}
    dados = _ler(url)
    assert set(dados["unbound"]) == set(EXEMPLO["unbound"])
    assert all(v is None for v in dados["unbound"].values())
    assert dados["postfix"]["fila"] is None
    assert dados["hashes"]["/etc/postfix/main.cf"] is None
    assert dados["apache"]["total_accesses"] == 15230, "uma fonte caida nao pode apagar as outras"


def test_hash_muda_quando_a_configuracao_muda(ambiente):
    url, _, executor = ambiente
    antes = _ler(url)["hashes"]["/etc/postfix/main.cf"]
    executor.respostas["sha256sum"] = "1" * 64 + "  /etc/postfix/main.cf\n"
    assert _ler(url)["hashes"]["/etc/postfix/main.cf"] != antes


# ---------- regra do AGENTS.md ----------

def test_agente_nao_importa_a_plataforma():
    for arquivo in PASTA_AGENTE.glob("*.py"):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            nomes = ([a.name for a in no.names] if isinstance(no, ast.Import)
                     else [no.module or ""] if isinstance(no, ast.ImportFrom) else [])
            assert not any(n.split(".")[0] == "plataforma" for n in nomes), f"{arquivo.name} importa plataforma"


def test_consultas_ao_docker_rodam_em_paralelo(tmp_path):
    """O coletor espera no maximo 5 s. Com cada comando levando 0,5 s, em serie seriam ~4,5 s."""
    import time

    class ExecutorLento(ExecutorFalso):
        def __call__(self, argv):
            time.sleep(0.5)
            return super().__call__(argv)

    ag = agente.Agente(url_status="http://127.0.0.1:1/nada", log_acesso=tmp_path / "a.log",
                       log_login=tmp_path / "l.log", executor=ExecutorLento())
    inicio = time.monotonic()
    ag.metricas()
    assert time.monotonic() - inicio < 2.0, "as consultas ao Docker estao rodando uma depois da outra"
