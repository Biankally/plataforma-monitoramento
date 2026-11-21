"""Valores calculados a mao. Leitura atual ts=1015, anterior ts=1000 (15 s antes), base ts=415 (10 min antes).

  db.qps            = (10150-10000)/15      = 10
  db.rollbacks_s    = (10-7)/15             = 0,2
  db.conexoes_abortadas = 5-2               = 3
  db.slow_queries_min = (7-4)/(15/60)       = 12
  db.uso_conexoes_pct = 30/151*100          = 19,8675
  db.crescimento_mb_dia = (50,5-50,0)/600 s * 86400 = 72
"""

import copy

import pytest

from plataforma.contrato.metricas import METRICAS
from plataforma.dominio.derivadas_db import derivar_db

ATUAL = {"ts": 1015, "disponivel": 1.0, "latencia_ms": 3.0, "status.Questions": 10150.0,
         "status.Com_rollback": 10.0, "status.Aborted_connects": 5.0, "status.Slow_queries": 7.0,
         "status.Threads_connected": 30.0, "status.Threads_running": 2.0, "status.Threads_cached": 3.0,
         "max_connections": 151.0, "tamanho_mb": 50.5}
ANTERIOR = {"ts": 1000, "status.Questions": 10000.0, "status.Com_rollback": 7.0,
            "status.Aborted_connects": 2.0, "status.Slow_queries": 4.0, "tamanho_mb": 50.0}
BASE = {"ts": 415, "tamanho_mb": 50.0}


def _v(atual=ATUAL, anterior=ANTERIOR, base=BASE):
    return {a.metrica: a.valor for a in derivar_db(atual, anterior, base)}


def test_valores_calculados_a_mao():
    esperado = {"db.qps": 10, "db.rollbacks_s": 0.2, "db.conexoes_abortadas": 3, "db.slow_queries_min": 12,
                "db.conexoes": 30, "db.conexoes_executando": 2, "db.threads_cache": 3,
                "db.uso_conexoes_pct": 30 / 151 * 100, "db.tamanho_mb": 50.5, "db.crescimento_mb_dia": 72}
    v = _v()
    assert v.keys() == esperado.keys()
    for m, x in esperado.items():
        assert v[m] == pytest.approx(x), m


def test_amostras_pertencem_ao_catalogo():
    for a in derivar_db(ATUAL, ANTERIOR, BASE):
        assert a.metrica in METRICAS and a.servico == "db"


def test_sem_leitura_anterior_so_saem_valores_instantaneos():
    v = _v(anterior=None, base=None)
    assert set(v) == {"db.conexoes", "db.conexoes_executando", "db.threads_cache",
                      "db.uso_conexoes_pct", "db.tamanho_mb"}


def test_sabotagem_contador_que_diminuiu_nao_gera_taxa():
    ant = copy.deepcopy(ANTERIOR)
    ant["status.Questions"], ant["status.Slow_queries"], ant["status.Aborted_connects"] = 99999.0, 99999.0, 99999.0
    v = _v(anterior=ant)
    assert not {"db.qps", "db.slow_queries_min", "db.conexoes_abortadas"} & set(v)
    assert v["db.rollbacks_s"] == pytest.approx(0.2)


def test_sabotagem_crescimento_exige_pelo_menos_60_s_de_historico():
    assert "db.crescimento_mb_dia" not in _v(base={"ts": 1000 - 30, "tamanho_mb": 50.0})
    assert "db.crescimento_mb_dia" in _v(base={"ts": 1015 - 60, "tamanho_mb": 50.0})


def test_sabotagem_max_connections_zero_nao_divide_por_zero():
    atual = {**ATUAL, "max_connections": 0.0}
    assert "db.uso_conexoes_pct" not in _v(atual=atual)


def test_sabotagem_banco_fora_do_ar_nao_gera_nada():
    assert derivar_db({"ts": 1015, "disponivel": 0.0, "latencia_ms": 3.0}, ANTERIOR, BASE) == []


def test_nao_altera_as_leituras():
    a, b, c = copy.deepcopy(ATUAL), copy.deepcopy(ANTERIOR), copy.deepcopy(BASE)
    derivar_db(a, b, c)
    assert (a, b, c) == (ATUAL, ANTERIOR, BASE)
