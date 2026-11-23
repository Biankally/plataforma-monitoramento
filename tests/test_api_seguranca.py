"""Seguranca na API: leitura do agente (login e hashes), linha de base, DDoS no ingest e e-mail."""

from __future__ import annotations

import pytest

from plataforma.api.app import criar_app

TOKEN = "token-de-teste"
H = {"X-Token": TOKEN}
T0 = 1_795_000_000


@pytest.fixture
def cli(tmp_path, monkeypatch):
    monkeypatch.delenv("MONITOR_CONFIG_DIR", raising=False)
    monkeypatch.setenv("NOTIFICADOR", "arquivo")
    monkeypatch.setenv("NOTIF_DIR", str(tmp_path / "emails"))
    cliente = criar_app(tmp_path / "m.db", TOKEN).test_client()
    cliente.emails = tmp_path / "emails"
    return cliente


def falha(ts, ip="10.0.0.9", usuario="admin@lab.local"):
    return {"ts": ts, "origem": ip, "usuario": usuario, "sucesso": False}


def leitura(cli, ts, auth=(), hashes=None, headers=H):
    corpo = {"ts": ts, "auth": list(auth)}
    if hashes is not None:
        corpo["hashes"] = hashes
    return cli.post("/api/seguranca/leitura", json=corpo, headers=headers)


def eventos(cli, **params):
    return cli.get("/api/seguranca", query_string=params).get_json()["eventos"]


def emails(cli):
    return sorted(p.name for p in cli.emails.glob("*.txt")) if cli.emails.exists() else []


# ---------------------------------------------------------------- protecao da rota


def test_leitura_exige_token(cli):
    assert leitura(cli, T0, headers={}).status_code == 401
    assert leitura(cli, T0, headers={"X-Token": "errado"}).status_code == 401
    assert cli.post("/api/seguranca/linha-base").status_code == 401
    assert cli.post("/api/seguranca/linha-base", headers={"X-Token": "errado"}).status_code == 401


@pytest.mark.parametrize("corpo", [
    [], {"auth": []}, {"ts": "x", "auth": []}, {"ts": -1}, {"ts": T0, "auth": "x"},
    {"ts": T0, "auth": [1]}, {"ts": T0, "auth": [{"ts": T0, "origem": "1.1.1.1"}]},
    {"ts": T0, "auth": [{"ts": T0, "origem": "1.1.1.1", "usuario": "u", "sucesso": "nao"}]},
    {"ts": T0, "hashes": []}, {"ts": T0, "hashes": {"/a": 1}},
])
def test_sabotagem_leitura_fora_do_formato_da_400(cli, corpo):
    r = cli.post("/api/seguranca/leitura", json=corpo, headers=H)
    assert r.status_code == 400 and "erro" in r.get_json()


# ---------------------------------------------------------------- forca bruta
def test_forca_bruta_atencao_critico_e_sem_repeticao(cli):
    assert leitura(cli, T0, [falha(T0 - i) for i in range(4)]).status_code == 201
    assert eventos(cli) == []                                           # 4 falhas: nada

    leitura(cli, T0 + 1, [falha(T0)])                                   # 5a falha na janela
    ev = eventos(cli)
    assert [(e["tipo"], e["nivel"], e["origem"], e["servico"]) for e in ev] == \
        [("AUTENTICACAO", "ATENCAO", "10.0.0.9", "web")]
    assert any("seguranca.autenticacao_ATENCAO" in n for n in emails(cli))

    leitura(cli, T0 + 16)                                               # mesmo nivel, sem novas falhas: nao repete
    assert len(eventos(cli)) == 1

    leitura(cli, T0 + 20, [falha(T0 + 17 + i % 3) for i in range(15)])  # 20 falhas em 60 s
    assert [e["nivel"] for e in eventos(cli)] == ["CRITICO", "ATENCAO"]  # mais novo primeiro
    assert any("seguranca.autenticacao_CRITICO" in n for n in emails(cli))

    leitura(cli, T0 + 35, [falha(T0 + 30)])                             # continua critico: sem novo aviso
    assert len(eventos(cli)) == 2


def test_forca_bruta_volta_a_avisar_depois_do_cooldown(cli):
    leitura(cli, T0, [falha(T0) for _ in range(5)])
    leitura(cli, T0 + 400, [falha(T0 + 399) for _ in range(5)])
    assert [e["nivel"] for e in eventos(cli)] == ["ATENCAO", "ATENCAO"]


def test_sabotagem_falhas_velhas_sucessos_e_ips_diferentes_nao_contam(cli):
    leitura(cli, T0, [falha(T0 - 100) for _ in range(10)])              # fora da janela de 60 s
    leitura(cli, T0 + 1, [{"ts": T0, "origem": "10.0.0.9", "usuario": "u", "sucesso": True} for _ in range(10)])
    leitura(cli, T0 + 2, [falha(T0 + 2, ip=f"10.0.1.{i}") for i in range(30)])  # 1 falha em cada um de 30 IPs
    assert eventos(cli) == []


def test_ips_sao_avaliados_separados(cli):
    leitura(cli, T0, [falha(T0, "10.0.0.1")] * 6 + [falha(T0, "10.0.0.2")] * 2)
    assert [(e["origem"], e["nivel"]) for e in eventos(cli)] == [("10.0.0.1", "ATENCAO")]


def test_email_leva_o_detalhe_do_evento(cli):
    leitura(cli, T0, [falha(T0)] * 6)
    texto = next(cli.emails.glob("*.txt")).read_text(encoding="utf-8")
    assert "6 falhas de login" in texto and "10.0.0.9" in texto and "[ATENCAO]" in texto


# ---------------------------------------------------------------- hashes e linha de base
ARQ = "/etc/postfix/main.cf"


def test_linha_de_base_e_hash_alterado(cli):
    assert cli.post("/api/seguranca/linha-base", headers=H).status_code == 409   # ainda sem leitura
    leitura(cli, T0, hashes={ARQ: "a" * 64, "/etc/unbound/unbound.conf": "b" * 64})
    assert eventos(cli) == []                                                    # sem linha de base, sem evento
    assert cli.get("/api/seguranca").get_json()["linha_base"] == []

    r = cli.post("/api/seguranca/linha-base", headers=H)
    assert r.status_code == 200 and r.get_json() == {"arquivos": 2}
    assert len(cli.get("/api/seguranca").get_json()["linha_base"]) == 2

    leitura(cli, T0 + 15, hashes={ARQ: "a" * 64, "/etc/unbound/unbound.conf": "b" * 64})
    assert eventos(cli) == []                                                    # igual: nada

    leitura(cli, T0 + 30, hashes={ARQ: "c" * 64, "/etc/unbound/unbound.conf": "b" * 64})
    ev = eventos(cli)
    assert [(e["tipo"], e["nivel"], e["servico"], e["origem"]) for e in ev] == \
        [("CONFIGURACAO", "CRITICO", "smtp", ARQ)]
    assert any("seguranca.configuracao_CRITICO" in n for n in emails(cli))

    leitura(cli, T0 + 45, hashes={ARQ: "c" * 64, "/etc/unbound/unbound.conf": "b" * 64})
    assert len(eventos(cli)) == 1                                                # mesmo hash alterado: nao repete

    leitura(cli, T0 + 60, hashes={ARQ: "d" * 64, "/etc/unbound/unbound.conf": "b" * 64})
    assert len(eventos(cli)) == 2                                                # mudou de novo: avisa

    cli.post("/api/seguranca/linha-base", headers=H)                             # aceitar o novo estado
    leitura(cli, T0 + 75, hashes={ARQ: "d" * 64, "/etc/unbound/unbound.conf": "b" * 64})
    assert len(eventos(cli)) == 2


def test_sabotagem_arquivo_novo_nao_gera_evento_e_linha_de_base_nao_muda_sozinha(cli):
    leitura(cli, T0, hashes={ARQ: "a" * 64})
    cli.post("/api/seguranca/linha-base", headers=H)
    leitura(cli, T0 + 15, hashes={ARQ: "a" * 64, "/etc/novo.conf": "z" * 64})
    assert eventos(cli) == []
    assert [b["caminho"] for b in cli.get("/api/seguranca").get_json()["linha_base"]] == [ARQ]


# ---------------------------------------------------------------- DDoS no ingest
def lote(ts, rps, qps=None):
    amostras = [{"servico": "web", "metrica": "web.rps", "valor": rps}]
    if qps is not None:
        amostras.append({"servico": "dns", "metrica": "dns.qps", "valor": qps})
    return {"ts": ts, "amostras": amostras}


def enviar(cli, ts, rps, qps=None):
    r = cli.post("/api/ingest", json=lote(ts, rps, qps), headers=H)
    assert r.status_code == 201, r.get_json()


def aquecer(cli, n=30, rps=10.0):
    for i in range(n):
        enviar(cli, T0 + i * 15, rps + (1 if i % 2 else -1), qps=5.0 + (1 if i % 2 else -1))


def test_ddos_pico_gera_evento_e_email_uma_vez(cli):
    aquecer(cli)
    enviar(cli, T0 + 30 * 15, 11.0)                                  # normal
    assert eventos(cli) == []
    enviar(cli, T0 + 31 * 15, 500.0)                                 # pico
    ev = eventos(cli)
    assert [(e["tipo"], e["nivel"], e["servico"]) for e in ev] == [("TRAFEGO", "CRITICO", "web")]
    assert "web.rps" in ev[0]["detalhe"]
    assert any("seguranca.trafego_CRITICO" in n for n in emails(cli))
    enviar(cli, T0 + 32 * 15, 520.0)                                 # ataque continua: sem novo aviso
    assert len(eventos(cli)) == 1


def test_ddos_tambem_vigia_as_consultas_dns(cli):
    aquecer(cli)
    enviar(cli, T0 + 30 * 15, 10.0, qps=400.0)
    assert [(e["servico"], e["tipo"]) for e in eventos(cli)] == [("dns", "TRAFEGO")]


def test_sabotagem_sem_historico_suficiente_nao_acusa_ddos(cli):
    aquecer(cli, n=10)
    enviar(cli, T0 + 10 * 15, 5000.0)
    assert eventos(cli) == []


def test_sabotagem_lote_sem_rps_continua_valendo(cli):
    r = cli.post("/api/ingest", headers=H, json={"ts": T0, "amostras": [
        {"servico": "web", "metrica": "web.disponivel", "valor": 1}]})
    assert r.status_code == 201 and eventos(cli) == []


# ---------------------------------------------------------------- consulta
def test_get_seguranca_respeita_o_limite_e_ordem(cli):
    for i in range(3):
        leitura(cli, T0 + i * 1000, [falha(T0 + i * 1000, ip=f"10.0.0.{i + 1}")] * 5)
    todos = eventos(cli)
    assert [e["origem"] for e in todos] == ["10.0.0.3", "10.0.0.2", "10.0.0.1"]
    assert len(eventos(cli, limite=2)) == 2
    assert cli.get("/api/seguranca", query_string={"limite": "x"}).status_code == 400


def test_sabotagem_o_ponto_atual_nao_entra_no_proprio_historico(cli):
    """Historico 4 e 16 alternados (media 10, desvio 6): 39 req/s da z = (39-10)/6 = 4,83.
    Se o proprio ponto entrasse no historico, media e desvio subiriam e o z cairia para cerca de 3,6."""
    for i in range(30):
        enviar(cli, T0 + i * 15, 4.0 if i % 2 else 16.0)
    enviar(cli, T0 + 30 * 15, 39.0)
    (ev,) = eventos(cli)
    assert ev["nivel"] == "ATENCAO" and "z = 4.8" in ev["detalhe"]


# ---------- vulnerabilidade conhecida por servico ----------

def test_versao_vulneravel_gera_evento_uma_vez_e_aparece_na_consulta(cli):
    versoes = {"dns": {"unbound": "1.20.0"}, "web": {"apache": "2.4.65"}}
    r = cli.post("/api/seguranca/leitura", json={"ts": T0, "auth": [], "versoes": versoes}, headers=H)
    assert r.status_code == 201
    vulns = [e for e in eventos(cli) if e["tipo"] == "VULNERABILIDADE"]
    assert [e["servico"] for e in vulns] == ["dns"]
    assert "CVE-2024-8508" in vulns[0]["detalhe"]
    cli.post("/api/seguranca/leitura", json={"ts": T0 + 15, "auth": [], "versoes": versoes}, headers=H)
    assert len([e for e in eventos(cli) if e["tipo"] == "VULNERABILIDADE"]) == 1, "o aviso nao pode repetir a cada ciclo"
    dados = cli.get("/api/seguranca").get_json()
    assert {"servico": "dns", "programa": "unbound", "versao": "1.20.0"} in [
        {k: x[k] for k in ("servico", "programa", "versao")} for x in dados["versoes"]]
    assert len(emails(cli)) == 1, "o evento tem que sair por e-mail (uma vez)"


@pytest.mark.parametrize("versoes", [["1.0"], {"dns": "1.20.0"}, {"dns": {"unbound": 120}}])
def test_sabotagem_versoes_fora_do_formato_da_400(cli, versoes):
    r = cli.post("/api/seguranca/leitura", json={"ts": T0, "auth": [], "versoes": versoes}, headers=H)
    assert r.status_code == 400
