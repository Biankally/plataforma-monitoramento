"""Valores esperados calculados a mao a partir de tests/falsos/agente_exemplo.json.

Leitura atual: ts 1795036800. Leitura anterior (15 s antes): 15000 acessos,
8400 consultas DNS, 1 SERVFAIL, 0 REFUSED. Logo, na janela de 15 s:
  rps = (15230-15000)/15 = 15,3333      dns.qps = (8421-8400)/15 = 1,4
  dns.taxa_erro = (2 SERVFAIL + 0 REFUSED)/21 = 9,5238 %
  smtp.emails_min = 12 enviados / (15/60 min) = 48
Janela do log web (61 linhas): 4xx = 4/61 = 6,5574 %; 5xx = 2/61 = 3,2787 %.
p95 de [950, 1830, 2210] us = posicao ceil(0,95*3) = 3 -> 2210 us = 2,21 ms.
smtp.taxa_entrega = 12/(12+1+0) = 92,3077 %; smtp.taxa_erro = (0+0)/13 = 0 %.
"""

import copy
import json
from pathlib import Path

import pytest

from plataforma.contrato.metricas import METRICAS
from plataforma.dominio.derivadas import derivar

EXEMPLO = json.loads((Path(__file__).parent / "falsos" / "agente_exemplo.json").read_text(encoding="utf-8"))


def _anterior():
    ant = copy.deepcopy(EXEMPLO)
    ant["ts"] = EXEMPLO["ts"] - 15
    ant["apache"]["total_accesses"] = 15000
    ant["unbound"]["total.num.queries"] = 8400
    ant["unbound"]["num.answer.rcode.SERVFAIL"] = 1
    return ant


def _valores(atual, anterior, **kw):
    return {a.metrica: a.valor for a in derivar(atual, anterior, **kw)}


def test_valores_calculados_a_mao():
    v = _valores(EXEMPLO, _anterior())
    esperado = {
        "web.rps": 230 / 15,
        "web.conexoes_ativas": 4,
        "web.taxa_erro_4xx_pct": 4 / 61 * 100,
        "web.taxa_erro_5xx_pct": 2 / 61 * 100,
        "web.req_4xx": 4,
        "web.req_5xx": 2,
        "web.latencia_p95_ms": 2.21,
        "dns.qps": 1.4,
        "dns.taxa_erro_pct": 2 / 21 * 100,
        "smtp.fila": 0,
        "smtp.taxa_entrega_pct": 12 / 13 * 100,
        "smtp.latencia_envio_s": 0.8,
        "smtp.rejeicoes": 0,
        "smtp.timeouts": 0,
        "smtp.taxa_erro_pct": 0,
        "smtp.emails_min": 48,
        "host.cpu_pct": 12.5,
        "host.mem_pct": 48.1,
        "host.disco_io_kbs": 120.0,
        "host.disco_latencia_ms": 2.1,
        "db.cpu_pct": 3.0,
        "db.mem_pct": 30.2,
    }
    assert v.keys() == esperado.keys()
    for metrica, valor in esperado.items():
        assert v[metrica] == pytest.approx(valor), metrica


def test_toda_amostra_pertence_ao_catalogo_e_ao_servico_certo():
    for a in derivar(EXEMPLO, _anterior()):
        assert a.metrica in METRICAS
        assert a.servico == a.metrica.split(".")[0]


def test_sem_leitura_anterior_so_saem_metricas_que_nao_dependem_de_taxa():
    v = _valores(EXEMPLO, None)
    for taxa in ("web.rps", "dns.qps", "dns.taxa_erro_pct", "smtp.emails_min"):
        assert taxa not in v
    assert v["web.conexoes_ativas"] == 4 and v["host.cpu_pct"] == 12.5 and v["smtp.taxa_entrega_pct"] > 0


def test_sabotagem_contador_que_diminuiu_nao_gera_taxa():
    """Servico reiniciou: o contador voltou a zero. Nada de taxa negativa."""
    ant = _anterior()
    ant["apache"]["total_accesses"] = 99999
    ant["unbound"]["total.num.queries"] = 99999
    v = _valores(EXEMPLO, ant)
    assert "web.rps" not in v and "dns.qps" not in v and "dns.taxa_erro_pct" not in v


def test_sabotagem_intervalo_zero_ou_negativo_nao_gera_taxa():
    for ts in (EXEMPLO["ts"], EXEMPLO["ts"] + 10):
        ant = _anterior()
        ant["ts"] = ts
        v = _valores(EXEMPLO, ant)
        assert "web.rps" not in v and "smtp.emails_min" not in v


def test_sabotagem_log_sem_linhas_nao_inventa_percentuais():
    atual = copy.deepcopy(EXEMPLO)
    atual["log_web"] = {"total": 0, "por_codigo": {}, "tempo_servidor_us": []}
    v = _valores(atual, _anterior())
    for m in ("web.taxa_erro_4xx_pct", "web.taxa_erro_5xx_pct", "web.latencia_p95_ms"):
        assert m not in v
    assert v["web.req_4xx"] == 0 and v["web.req_5xx"] == 0


def test_sabotagem_mais_erros_5xx_sobem_a_taxa():
    atual = copy.deepcopy(EXEMPLO)
    atual["log_web"] = {"total": 100, "por_codigo": {"200": 50, "502": 30, "503": 20}, "tempo_servidor_us": [1]}
    v = _valores(atual, _anterior())
    assert v["web.taxa_erro_5xx_pct"] == 50 and v["web.req_5xx"] == 50 and v["web.taxa_erro_4xx_pct"] == 0


def test_p95_de_lista_grande():
    atual = copy.deepcopy(EXEMPLO)
    atual["log_web"]["tempo_servidor_us"] = [i * 1000 for i in range(1, 101)]  # 1..100 ms
    assert _valores(atual, None)["web.latencia_p95_ms"] == 95.0


def test_smtp_taxa_erro_com_rejeicoes_e_timeouts():
    atual = copy.deepcopy(EXEMPLO)
    atual["postfix"].update(sent=7, deferred=0, bounced=0, rejeicoes=2, timeouts=1)
    v = _valores(atual, None)
    assert v["smtp.taxa_erro_pct"] == pytest.approx(30.0)
    assert v["smtp.taxa_entrega_pct"] == 100.0


def test_smtp_sem_nenhum_evento_nao_inventa_taxas():
    atual = copy.deepcopy(EXEMPLO)
    atual["postfix"].update(sent=0, deferred=0, bounced=0, rejeicoes=0, timeouts=0, delay_medio_s=None)
    v = _valores(atual, _anterior())
    for m in ("smtp.taxa_entrega_pct", "smtp.taxa_erro_pct", "smtp.latencia_envio_s"):
        assert m not in v
    assert v["smtp.emails_min"] == 0 and v["smtp.fila"] == 0


def test_secao_ausente_so_omite_as_metricas_dela():
    atual = copy.deepcopy(EXEMPLO)
    del atual["unbound"]
    v = _valores(atual, _anterior())
    assert not any(m.startswith("dns.") for m in v) and "web.rps" in v and "smtp.fila" in v


def test_falhas_da_sonda_dns_entram_na_taxa_de_erro():
    # 21 consultas, 2 SERVFAIL, +1 falha da sonda: 3 erros em 22
    v = _valores(EXEMPLO, _anterior(), falhas_sonda_dns=1)
    assert v["dns.taxa_erro_pct"] == pytest.approx(3 / 22 * 100)


def test_nao_altera_as_leituras_recebidas():
    atual, ant = copy.deepcopy(EXEMPLO), _anterior()
    ant_copia = copy.deepcopy(ant)
    derivar(atual, ant)
    assert atual == EXEMPLO and ant == ant_copia


def test_cpu_e_memoria_do_container_do_banco():
    """Enunciado 3.2: uso de CPU e memoria do banco (o agente le do docker stats)."""
    v = _valores(EXEMPLO, None)
    assert v["db.cpu_pct"] == 3.0 and v["db.mem_pct"] == 30.2


def test_sabotagem_container_do_banco_sem_dado_omite_as_metricas():
    atual = copy.deepcopy(EXEMPLO)
    atual["containers"]["db"] = {"cpu_pct": None, "mem_pct": None}
    v = _valores(atual, None)
    assert "db.cpu_pct" not in v and "db.mem_pct" not in v
