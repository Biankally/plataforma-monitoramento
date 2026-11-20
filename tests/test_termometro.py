"""Teste termometro: percorre o sistema inteiro como o usuario rodaria.

API e Coletor rodam em processos separados (sys.executable), contra servicos
falsos. Quando passa, a cadeia coleta -> API -> banco -> alerta -> e-mail -> status funciona.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

from tests.falsos.servicos_falsos import TcpFalso, WebFalso, porta_livre

RAIZ = Path(__file__).resolve().parents[1]
PECAS = ["plataforma.api.app", "plataforma.infra.coletor", "plataforma.infra.banco"]
if not all(importlib.util.find_spec(p) for p in PECAS):
    pytest.skip("pecas do sistema ainda nao existem", allow_module_level=True)

TOKEN = "token-de-teste"


@pytest.fixture
def ambiente(tmp_path):
    web, db, dns, smtp = WebFalso(), TcpFalso(), TcpFalso(), TcpFalso()
    config = tmp_path / "config"
    config.mkdir()
    servicos = [
        f'[[servico]]\nnome = "web"\ntipo = "http"\nurl = "http://127.0.0.1:{web.porta}/"\ntimeout_s = 1\n',
        *(f'[[servico]]\nnome = "{n}"\ntipo = "tcp"\nhost = "127.0.0.1"\nporta = {s.porta}\ntimeout_s = 1\n'
          for n, s in (("db", db), ("dns", dns), ("smtp", smtp))),
    ]
    (config / "servicos.toml").write_text("\n".join(servicos), encoding="utf-8")
    (config / "regras.toml").write_text((RAIZ / "config" / "regras.toml").read_text(encoding="utf-8"),
                                        encoding="utf-8")
    porta_api = porta_livre()
    env = {
        **os.environ,
        "MONITOR_CONFIG_DIR": str(config),
        "MONITOR_DB": str(tmp_path / "metricas.db"),
        "MONITOR_TOKEN": TOKEN,
        "MONITOR_API_URL": f"http://127.0.0.1:{porta_api}",
        "NOTIFICADOR": "arquivo",
        "NOTIF_DIR": str(tmp_path / "emails"),
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
    }
    api = subprocess.Popen([sys.executable, "-m", "plataforma.api", "--porta", str(porta_api)],
                           cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    url = env["MONITOR_API_URL"]
    for _ in range(100):
        try:
            requests.get(f"{url}/api/status", timeout=1)
            break
        except requests.RequestException:
            time.sleep(0.1)
    else:
        api.kill()
        pytest.fail("a API nao subiu: " + api.stderr.read().decode("utf-8", "replace"))
    yield {"url": url, "env": env, "web": web, "emails": tmp_path / "emails"}
    api.terminate()
    api.wait(timeout=10)
    for s in (db, dns, smtp):
        s.derrubar()


def coletar(amb) -> None:
    r = subprocess.run([sys.executable, "-m", "plataforma.infra.coletor", "--uma-vez"],
                       cwd=RAIZ, env=amb["env"], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stderr


def niveis(amb) -> dict[str, str]:
    dados = requests.get(f"{amb['url']}/api/status", timeout=5).json()
    return {s["servico"]: s["nivel"] for s in dados["servicos"]}


def test_ponta_a_ponta_tudo_no_ar(ambiente):
    assert set(niveis(ambiente).values()) == {"SEM_DADOS"}
    coletar(ambiente)
    assert niveis(ambiente) == {"web": "OK", "db": "OK", "dns": "OK", "smtp": "OK"}
    assert requests.get(f"{ambiente['url']}/api/saude", timeout=5).status_code == 200
    serie = requests.get(f"{ambiente['url']}/api/metricas", params={"metrica": "web.latencia_ms"}, timeout=5)
    assert len(serie.json()["pontos"]) == 1


def test_sabotagem_web_cai_alerta_critico_e_email(ambiente):
    coletar(ambiente)
    ambiente["web"].derrubar()
    coletar(ambiente)
    assert niveis(ambiente)["web"] == "ATENCAO"
    coletar(ambiente)
    estado = niveis(ambiente)
    assert estado["web"] == "CRITICO"
    assert {estado[s] for s in ("db", "dns", "smtp")} == {"OK"}  # os outros nao caem junto
    emails = sorted(p.name for p in ambiente["emails"].glob("*.txt"))
    assert any("web.disponivel_ATENCAO" in e for e in emails)
    assert any("web.disponivel_CRITICO" in e for e in emails)
    alertas = requests.get(f"{ambiente['url']}/api/alertas", timeout=5).json()["alertas"]
    assert alertas[0]["nivel_novo"] == "CRITICO" and alertas[0]["email_enviado"] == 1


def test_sabotagem_ingestao_sem_token_ou_fora_do_contrato(ambiente):
    url = f"{ambiente['url']}/api/ingest"
    lote = {"ts": int(time.time()), "amostras": [{"servico": "web", "metrica": "web.disponivel", "valor": 1}]}
    assert requests.post(url, json=lote, timeout=5).status_code == 401
    assert requests.post(url, json=lote, headers={"X-Token": "errado"}, timeout=5).status_code == 401
    ruim = {"ts": lote["ts"], "amostras": [{"servico": "web", "metrica": "web.nao_existe", "valor": 1}]}
    assert requests.post(url, json=ruim, headers={"X-Token": TOKEN}, timeout=5).status_code == 400
    assert requests.post(url, json=lote, headers={"X-Token": TOKEN}, timeout=5).status_code == 201


@pytest.mark.skipif(importlib.util.find_spec("streamlit") is None, reason="streamlit nao instalado")
def test_dashboard_sobe_e_le_a_api(ambiente):
    coletar(ambiente)
    porta = porta_livre()
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(RAIZ / "plataforma" / "dashboard" / "app.py"),
         "--server.headless", "true", "--server.port", str(porta), "--browser.gatherUsageStats", "false"],
        cwd=RAIZ, env=ambiente["env"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(150):
            try:
                if requests.get(f"http://127.0.0.1:{porta}/_stcore/health", timeout=1).text == "ok":
                    break
            except requests.RequestException:
                pass
            time.sleep(0.2)
        else:
            pytest.fail("o dashboard nao subiu")
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    from streamlit.testing.v1 import AppTest

    os.environ["MONITOR_API_URL"] = ambiente["url"]
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    try:
        app = AppTest.from_file(str(RAIZ / "plataforma" / "dashboard" / "app.py"), default_timeout=30).run()
    finally:
        os.environ.pop("MONITOR_API_URL", None)
    assert not app.exception
    assert {m.label for m in app.metric} == {"WEB", "DB", "DNS", "SMTP"}
    assert all("OK" in m.value for m in app.metric)
