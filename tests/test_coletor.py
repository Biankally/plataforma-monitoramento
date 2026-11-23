"""Coletor juntando sondas + agente. As sondas e o agente sao trocados por versoes controladas;
o termometro (test_termometro.py) cobre a cadeia real com servicos falsos."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from plataforma.contrato import config
from plataforma.contrato.metricas import METRICAS, validar_lote
from plataforma.infra import coletor
from plataforma.infra.agente_cliente import ErroAgente

EXEMPLO = json.loads((Path(__file__).parent / "falsos" / "agente_exemplo.json").read_text(encoding="utf-8"))

SERVICOS = [
    config.ServicoMonitorado(nome="web", tipo="http", url="http://x/"),
    config.ServicoMonitorado(nome="db", tipo="mysql", host="h", porta=3307),
    config.ServicoMonitorado(nome="dns", tipo="dns", host="h", porta=1053),
    config.ServicoMonitorado(nome="smtp", tipo="smtp", host="h", porta=2525),
]


class Cenario:
    """Controla o que cada sonda e o agente devolvem, ciclo a ciclo."""

    def __init__(self, monkeypatch, plat=None):
        self.mysql = {"disponivel": 1.0, "latencia_ms": 2.0, "status.Questions": 1000.0,
                      "status.Threads_connected": 5.0, "max_connections": 100.0, "tamanho_mb": 10.0}
        self.dns = {"disponivel": 1.0, "latencia_ms": 1.0}
        self.agente: dict | Exception = EXEMPLO
        self.chamadas_agente = 0
        plat = {"agente_url": "http://agente:9100"} if plat is None else plat
        monkeypatch.setattr(coletor.config, "servicos_monitorados", lambda: SERVICOS)
        monkeypatch.setattr(coletor.config, "plataforma", lambda: plat)
        monkeypatch.setattr(coletor, "sonda_http", lambda url, t: {"disponivel": 1.0, "latencia_ms": 5.0})
        monkeypatch.setattr(coletor, "sonda_mysql", lambda *a, **k: dict(self.mysql))
        monkeypatch.setattr(coletor, "sonda_dns", lambda *a, **k: dict(self.dns))
        monkeypatch.setattr(coletor, "sonda_smtp", lambda *a, **k: {"disponivel": 1.0, "latencia_ms": 4.0})
        monkeypatch.setattr(coletor, "ler_metricas", self._ler)
        monkeypatch.setenv("MONITOR_DB_SENHA", "segredo")
        monkeypatch.setenv("MONITOR_AGENTE_TOKEN", "tok")
        monkeypatch.delenv("MONITOR_AGENTE_URL", raising=False)

    def _ler(self, url, token, timeout_s):
        self.chamadas_agente += 1
        if isinstance(self.agente, Exception):
            raise self.agente
        return self.agente


def valores(lote: dict) -> dict[str, float]:
    return {a["metrica"]: a["valor"] for a in lote["amostras"]}


def test_lote_junta_sondas_e_agente_e_respeita_o_contrato(monkeypatch):
    Cenario(monkeypatch)
    lote = coletor.montar_lote(1795036800)
    validar_lote(lote)  # levanta ErroContrato se algo fugir do catalogo
    v = valores(lote)
    for m in ("web.disponivel", "web.latencia_ms", "db.disponivel", "db.conexoes", "db.uso_conexoes_pct",
              "dns.disponivel", "smtp.disponivel", "web.conexoes_ativas", "web.latencia_p95_ms",
              "smtp.taxa_entrega_pct", "host.cpu_pct", "smtp.fila"):
        assert m in v, m
    assert all(m in METRICAS for m in v)


def test_primeiro_ciclo_nao_tem_taxas_e_o_segundo_tem(monkeypatch):
    c = Cenario(monkeypatch)
    memoria = coletor.Memoria()
    primeiro = valores(coletor.montar_lote(1795036800, memoria))
    assert not {"db.qps", "web.rps", "dns.qps", "smtp.emails_min"} & set(primeiro)

    c.mysql["status.Questions"] = 1150.0
    c.agente = json.loads(json.dumps(EXEMPLO))
    c.agente["ts"] += 15
    c.agente["apache"]["total_accesses"] += 150
    c.agente["unbound"]["total.num.queries"] += 30
    segundo = valores(coletor.montar_lote(1795036815, memoria))
    assert segundo["db.qps"] == pytest.approx(10.0)
    assert segundo["web.rps"] == pytest.approx(10.0)
    assert segundo["dns.qps"] == pytest.approx(2.0)


def test_sabotagem_agente_fora_do_ar_mantem_as_sondas_e_avisa(monkeypatch, capsys):
    c = Cenario(monkeypatch)
    c.agente = ErroAgente("agente inacessivel")
    v = valores(coletor.montar_lote(1795036800))
    assert v["web.disponivel"] == 1.0 and v["db.disponivel"] == 1.0
    assert not {"web.conexoes_ativas", "host.cpu_pct", "smtp.fila"} & set(v)
    assert "agente" in capsys.readouterr().err


def test_sem_agente_configurado_nao_chama_o_agente(monkeypatch):
    c = Cenario(monkeypatch, plat={})
    v = valores(coletor.montar_lote(1795036800))
    assert c.chamadas_agente == 0 and "web.disponivel" in v and "host.cpu_pct" not in v


def test_agente_configurado_por_ambiente(monkeypatch):
    c = Cenario(monkeypatch, plat={})
    monkeypatch.setenv("MONITOR_AGENTE_URL", "http://agente:9100")
    coletor.montar_lote(1795036800)
    assert c.chamadas_agente == 1


def test_sabotagem_agente_configurado_sem_token_acusa(monkeypatch):
    Cenario(monkeypatch)
    monkeypatch.delenv("MONITOR_AGENTE_TOKEN")
    with pytest.raises(RuntimeError, match="MONITOR_AGENTE_TOKEN"):
        coletor.montar_lote(1795036800)


def test_sabotagem_banco_fora_do_ar_nao_vira_baseline(monkeypatch):
    c = Cenario(monkeypatch)
    memoria = coletor.Memoria()
    coletor.montar_lote(1000, memoria)                       # leitura boa
    c.mysql = {"disponivel": 0.0, "latencia_ms": 1.0}        # caiu
    queda = valores(coletor.montar_lote(1015, memoria))
    # db.cpu_pct/db.mem_pct vem do agente (docker stats do container), nao da sonda MySQL: continuam valendo
    assert queda["db.disponivel"] == 0.0 and not any(m.startswith("db.") and m not in
                                                     ("db.disponivel", "db.latencia_ms", "db.cpu_pct", "db.mem_pct")
                                                     for m in queda)
    c.mysql = {"disponivel": 1.0, "latencia_ms": 2.0, "status.Questions": 1300.0, "status.Threads_connected": 5.0,
               "max_connections": 100.0, "tamanho_mb": 10.0}  # voltou
    volta = valores(coletor.montar_lote(1030, memoria))
    assert volta["db.qps"] == pytest.approx(300 / 30)         # usa a ultima leitura boa (ts 1000)


def test_sabotagem_dns_fora_do_ar_entra_na_taxa_de_erro(monkeypatch):
    c = Cenario(monkeypatch)
    memoria = coletor.Memoria()
    coletor.montar_lote(1795036800, memoria)
    c.dns = {"disponivel": 0.0, "latencia_ms": 2000.0}
    c.agente = json.loads(json.dumps(EXEMPLO))
    c.agente["ts"] += 15
    c.agente["unbound"]["total.num.queries"] += 21
    c.agente["unbound"]["num.answer.rcode.SERVFAIL"] += 2
    v = valores(coletor.montar_lote(1795036815, memoria))
    assert v["dns.taxa_erro_pct"] == pytest.approx(3 / 22 * 100, abs=1e-3)  # o lote arredonda a 3 casas


def test_sabotagem_mysql_sem_senha_acusa(monkeypatch):
    Cenario(monkeypatch)
    monkeypatch.delenv("MONITOR_DB_SENHA")
    with pytest.raises(RuntimeError, match="MONITOR_DB_SENHA"):
        coletor.montar_lote(1795036800)


def test_tipo_tcp_continua_funcionando(monkeypatch):
    Cenario(monkeypatch)
    monkeypatch.setattr(coletor.config, "servicos_monitorados",
                        lambda: [config.ServicoMonitorado(nome="db", tipo="tcp", host="h", porta=1)])
    monkeypatch.setattr(coletor, "sonda_tcp", lambda h, p, t: {"disponivel": 1.0, "latencia_ms": 1.0})
    assert valores(coletor.montar_lote(1795036800, coletor.Memoria()))["db.disponivel"] == 1.0


def test_sabotagem_tipo_desconhecido_acusa(monkeypatch):
    Cenario(monkeypatch)
    monkeypatch.setattr(coletor.config, "servicos_monitorados",
                        lambda: [config.ServicoMonitorado(nome="db", tipo="ftp")])
    with pytest.raises(ValueError, match="ftp"):
        coletor.montar_lote(1795036800)


def test_crescimento_do_banco_usa_a_leitura_mais_antiga_do_historico(monkeypatch):
    c = Cenario(monkeypatch, plat={})
    memoria = coletor.Memoria()
    c.mysql["tamanho_mb"] = 10.0
    primeiro = valores(coletor.montar_lote(1000, memoria))
    assert "db.crescimento_mb_dia" not in primeiro           # ainda sem historico
    c.mysql["tamanho_mb"] = 10.0 + 1.0
    v = valores(coletor.montar_lote(1000 + 600, memoria))    # 10 min depois: +1 MB
    assert v["db.crescimento_mb_dia"] == pytest.approx(1.0 / 600 * 86400)


def test_servicos_toml_do_repositorio_so_usa_tipos_que_o_coletor_conhece(monkeypatch):
    """Evita o arquivo de configuracao e o Coletor ficarem fora de sincronia."""
    monkeypatch.delenv("MONITOR_CONFIG_DIR", raising=False)
    servicos = config.servicos_monitorados()
    assert {s.nome for s in servicos} == {"web", "db", "dns", "smtp"}
    chamadas = []
    monkeypatch.setattr(coletor, "sonda_http", lambda *a: chamadas.append("http") or {"disponivel": 1.0, "latencia_ms": 1.0})
    for nome in ("sonda_mysql", "sonda_dns", "sonda_smtp", "sonda_tcp"):
        monkeypatch.setattr(coletor, nome, lambda *a, _n=nome, **k: chamadas.append(_n) or {"disponivel": 1.0, "latencia_ms": 1.0})
    monkeypatch.setenv("MONITOR_DB_SENHA", "x")
    for s in servicos:
        coletor.medir(s)  # tipo desconhecido levantaria ValueError
    assert chamadas == ["http", "sonda_mysql", "sonda_dns", "sonda_smtp"]  # cada tipo chama a sonda certa


# ---------------------------------------------------------------- seguranca: o Coletor repassa login e hashes do agente
class _Resposta:
    def __init__(self, status=201):
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _gravar_posts(monkeypatch, status_seguranca=201):
    posts = []

    def falso(url, json=None, headers=None, timeout=None):
        posts.append((url, json, headers))
        return _Resposta(status_seguranca if url.endswith("/seguranca/leitura") else 201)

    monkeypatch.setattr(coletor.requests, "post", falso)
    return posts


def test_ciclo_envia_o_lote_e_depois_a_leitura_de_seguranca(monkeypatch):
    Cenario(monkeypatch)
    posts = _gravar_posts(monkeypatch)
    coletor.ciclo("http://api", "tok-api", coletor.Memoria())
    assert [u for u, _, _ in posts] == ["http://api/api/ingest", "http://api/api/seguranca/leitura"]
    assert all(h == {"X-Token": "tok-api"} for _, _, h in posts)
    assert posts[1][1] == {"ts": EXEMPLO["ts"], "auth": EXEMPLO["auth"], "hashes": EXEMPLO["hashes"],
                           "versoes": EXEMPLO["versoes"]}


def test_sabotagem_agente_fora_do_ar_nao_envia_seguranca(monkeypatch):
    c = Cenario(monkeypatch)
    c.agente = ErroAgente("fora")
    posts = _gravar_posts(monkeypatch)
    coletor.ciclo("http://api", "t", coletor.Memoria())
    assert [u for u, _, _ in posts] == ["http://api/api/ingest"]


def test_sabotagem_leitura_nao_e_reenviada_no_ciclo_seguinte(monkeypatch):
    c = Cenario(monkeypatch)
    posts = _gravar_posts(monkeypatch)
    memoria = coletor.Memoria()
    coletor.ciclo("http://api", "t", memoria)
    c.agente = ErroAgente("caiu")
    coletor.ciclo("http://api", "t", memoria)
    assert [u.rsplit("/", 1)[-1] for u, _, _ in posts] == ["ingest", "leitura", "ingest"]


def test_agente_sem_auth_nem_hashes_manda_lista_vazia_e_sem_hashes(monkeypatch):
    c = Cenario(monkeypatch)
    c.agente = {"ts": EXEMPLO["ts"], "host": EXEMPLO["host"]}
    posts = _gravar_posts(monkeypatch)
    coletor.ciclo("http://api", "t", coletor.Memoria())
    assert posts[1][1] == {"ts": EXEMPLO["ts"], "auth": []}


def test_sabotagem_api_recusa_a_leitura_de_seguranca_acusa_erro(monkeypatch):
    import requests
    Cenario(monkeypatch)
    _gravar_posts(monkeypatch, status_seguranca=401)
    with pytest.raises(requests.HTTPError):
        coletor.ciclo("http://api", "t", coletor.Memoria())


def test_sem_agente_configurado_nao_chama_a_api_de_seguranca(monkeypatch):
    Cenario(monkeypatch, plat={})
    posts = _gravar_posts(monkeypatch)
    coletor.ciclo("http://api", "t", coletor.Memoria())
    assert [u for u, _, _ in posts] == ["http://api/api/ingest"]
