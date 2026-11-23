"""Dashboard (P3, tarefa 1): paginas por servico, alertas e seguranca, contra uma API de verdade.

A API (criar_app) roda numa thread com um banco temporario e recebe dados pelas mesmas rotas
que o Coletor usa. O dashboard roda no AppTest do Streamlit e le essa API por HTTP, como no uso real.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
import requests

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from plataforma.api.app import criar_app  # noqa: E402
from plataforma.contrato.metricas import METRICAS  # noqa: E402
from tests.falsos.servicos_falsos import porta_livre  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "plataforma" / "dashboard" / "app.py"
TOKEN = "token-de-teste"
H = {"X-Token": TOKEN}
NORMAL = {"web.disponivel": 1, "web.latencia_ms": 12.5, "db.disponivel": 1, "dns.disponivel": 1,
          "smtp.disponivel": 1}


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.delenv("MONITOR_CONFIG_DIR", raising=False)
    monkeypatch.setenv("NOTIFICADOR", "arquivo")
    monkeypatch.setenv("NOTIF_DIR", str(tmp_path / "emails"))
    servidor = make_server("127.0.0.1", porta_livre(), criar_app(tmp_path / "m.db", TOKEN), threaded=True)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{servidor.server_port}"
    monkeypatch.setenv("MONITOR_API_URL", url)
    monkeypatch.setenv("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    yield url
    servidor.shutdown()


def enviar(url: str, ts: int, valores: dict[str, float]) -> None:
    amostras = [{"servico": m.split(".")[0], "metrica": m, "valor": v} for m, v in valores.items()]
    r = requests.post(f"{url}/api/ingest", json={"ts": ts, "amostras": amostras}, headers=H, timeout=5)
    assert r.status_code == 201, r.text


def web_caiu(url: str) -> None:
    """Um ciclo normal e dois com o web fora do ar: alerta ATENCAO e depois CRITICO."""
    agora = int(time.time())
    enviar(url, agora - 30, NORMAL)
    enviar(url, agora - 15, {**NORMAL, "web.disponivel": 0})
    enviar(url, agora, {**NORMAL, "web.disponivel": 0})


def abrir(pagina: str | None = None, servico: str | None = None) -> AppTest:
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    if pagina:
        app.radio(key="pagina").set_value(pagina).run()
    if servico:
        app.selectbox(key="servico").set_value(servico).run()
    assert not app.exception, app.exception
    return app


def textos(app: AppTest) -> str:
    partes = [e.value for tipo in ("title", "header", "subheader", "markdown", "caption", "info", "error",
                                   "warning", "success") for e in getattr(app, tipo)]
    partes += [f"{m.label} {m.value}" for m in app.metric]
    partes += [d.value.to_string() for d in app.dataframe]
    return "\n".join(str(p) for p in partes)


# ---------------------------------------------------------------- visao geral


def test_visao_geral_mostra_cada_servico_com_cor(api):
    web_caiu(api)
    app = abrir()
    valores = {m.label: m.value for m in app.metric}
    assert valores["WEB"] == "🔴 CRITICO"
    assert all(valores[s] == "🟢 OK" for s in ("DB", "DNS", "SMTP"))


def test_visao_geral_preve_o_servico_host(api):
    enviar(api, int(time.time()), {**NORMAL, "host.cpu_pct": 40.0})
    assert "HOST" in {m.label for m in abrir().metric}


# ---------------------------------------------------------------- pagina por servico


@pytest.mark.parametrize("servico", ["web", "db", "dns", "smtp", "host"])
def test_pagina_do_servico_lista_todas_as_metricas_do_catalogo_com_unidade(api, servico):
    web_caiu(api)
    app = abrir("Por serviço", servico)
    rotulos = [m.label for m in app.metric]
    for metrica, (unidade, _descricao) in METRICAS.items():
        if metrica.startswith(servico + "."):
            assert any(metrica in r and f"({unidade})" in r for r in rotulos), f"faltou {metrica} ({unidade})"


def test_pagina_do_servico_mostra_valor_e_cor_de_cada_metrica(api):
    web_caiu(api)
    app = abrir("Por serviço", "web")
    por_rotulo = {m.label: m.value for m in app.metric}
    disponivel = next(r for r in por_rotulo if "web.disponivel" in r)
    latencia = next(r for r in por_rotulo if "web.latencia_ms (" in r)
    rps = next(r for r in por_rotulo if "web.rps" in r)
    assert disponivel.startswith("🔴") and por_rotulo[disponivel] == "fora do ar"
    assert latencia.startswith("🟢") and por_rotulo[latencia] == "12,5 ms"
    assert rps.startswith("⚪") and por_rotulo[rps] == "sem dados"  # o agente ainda nao mandou


def test_sabotagem_metrica_sem_dados_nao_aparece_como_ok(api):
    enviar(api, int(time.time()), NORMAL)
    app = abrir("Por serviço", "db")
    qps = next(m for m in app.metric if "db.qps" in m.label)
    assert not qps.label.startswith("🟢") and qps.value == "sem dados"


# ---------------------------------------------------------------- alertas


def test_pagina_de_alertas_lista_as_mudancas_de_nivel(api):
    web_caiu(api)
    texto = textos(abrir("Alertas"))
    assert "web.disponivel" in texto
    assert "🔴 CRITICO" in texto and "🟡 ATENCAO" in texto
    assert "✅" in texto  # e-mail enviado


def test_pagina_de_alertas_sem_alertas_avisa(api):
    enviar(api, int(time.time()), NORMAL)
    assert "Nenhum alerta" in textos(abrir("Alertas"))


# ---------------------------------------------------------------- seguranca


def test_pagina_de_seguranca_mostra_eventos_e_linha_de_base(api):
    agora = int(time.time())
    falhas = [{"ts": agora - i, "origem": "10.0.0.9", "usuario": "admin@lab.local", "sucesso": False}
              for i in range(6)]
    r = requests.post(f"{api}/api/seguranca/leitura", headers=H, timeout=5,
                      json={"ts": agora, "auth": falhas, "hashes": {"/etc/postfix/main.cf": "a" * 64}})
    assert r.status_code == 201
    assert requests.post(f"{api}/api/seguranca/linha-base", headers=H, timeout=5).status_code == 200
    texto = textos(abrir("Segurança"))
    assert "AUTENTICACAO" in texto and "10.0.0.9" in texto and "🟡 ATENCAO" in texto
    assert "/etc/postfix/main.cf" in texto


def test_pagina_de_seguranca_sem_eventos_avisa(api):
    assert "Nenhum evento" in textos(abrir("Segurança"))


# ---------------------------------------------------------------- API fora do ar


@pytest.mark.parametrize("pagina", [None, "Por serviço", "Alertas", "Segurança"])
def test_sabotagem_api_fora_do_ar_mostra_erro_sem_quebrar(monkeypatch, pagina):
    monkeypatch.setenv("MONITOR_API_URL", f"http://127.0.0.1:{porta_livre()}")  # ninguem escuta aqui
    app = abrir(pagina)
    assert any("API indisponível" in e.value for e in app.error)
