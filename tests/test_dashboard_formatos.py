"""Funcoes puras do dashboard (P3, tarefa 1): nivel de cada metrica, valores com unidade, limites e horario."""

from __future__ import annotations

import pytest

from plataforma.dashboard import formatos

ALERTAS = [  # como a API devolve: do mais novo para o mais antigo
    {"id": 3, "metrica": "web.disponivel", "nivel_novo": "CRITICO"},
    {"id": 2, "metrica": "web.disponivel", "nivel_novo": "ATENCAO"},
    {"id": 1, "metrica": "db.qps", "nivel_novo": "ATENCAO"},
]


# ---------------------------------------------------------------- nivel atual de cada metrica


def test_nivel_atual_e_o_do_alerta_mais_novo():
    assert formatos.nivel_por_metrica(ALERTAS) == {"web.disponivel": "CRITICO", "db.qps": "ATENCAO"}


def test_sabotagem_alerta_antigo_nao_sobrescreve_o_novo():
    # Se a funcao pegasse o ultimo da lista (o mais antigo), web.disponivel viraria ATENCAO.
    assert formatos.nivel_por_metrica(ALERTAS)["web.disponivel"] != "ATENCAO"


def test_nivel_exibido_cobre_os_quatro_casos():
    niveis = formatos.nivel_por_metrica(ALERTAS)
    com_regra = {"web.disponivel", "web.latencia_ms", "db.qps"}
    assert formatos.nivel_exibido("web.disponivel", True, niveis, com_regra) == "CRITICO"
    assert formatos.nivel_exibido("web.latencia_ms", True, niveis, com_regra) == "OK"      # regra sem alerta
    assert formatos.nivel_exibido("web.rps", True, niveis, com_regra) == formatos.INFORMATIVA  # sem regra
    assert formatos.nivel_exibido("web.latencia_ms", False, niveis, com_regra) == "SEM_DADOS"


def test_todo_nivel_tem_icone_de_cor_diferente():
    icones = [formatos.icone(n) for n in ("OK", "ATENCAO", "CRITICO", "SEM_DADOS", formatos.INFORMATIVA)]
    assert icones[:3] == ["🟢", "🟡", "🔴"]
    assert len(set(icones)) == len(icones)


def test_sabotagem_nivel_desconhecido_nao_vira_verde():
    assert formatos.icone("QUALQUER") != formatos.icone("OK")


# ---------------------------------------------------------------- valores com unidade


@pytest.mark.parametrize(("valor", "unidade", "esperado"), [
    (1, "0/1", "no ar"),
    (0, "0/1", "fora do ar"),
    (12.5, "ms", "12,5 ms"),
    (1234.567, "MB", "1.234,57 MB"),
    (3.0, "%", "3 %"),
    (0.004, "/s", "0 /s"),
])
def test_formatar_valor_com_unidade(valor, unidade, esperado):
    assert formatos.formatar_valor(valor, unidade) == esperado


def test_sabotagem_valor_sem_unidade_e_acusado():
    assert formatos.formatar_valor(250, "ms").endswith(" ms")
    assert formatos.formatar_valor(250, "ms") != "250"


# ---------------------------------------------------------------- limites e horario


def test_descrever_limites_maior_e_menor():
    assert formatos.descrever_limites({"operador": ">", "atencao": 500, "critico": 2000}, "ms") == \
        "Atenção > 500 ms · Crítico > 2.000 ms"
    assert formatos.descrever_limites({"operador": "<", "atencao": 95, "critico": 80}, "%") == \
        "Atenção < 95 % · Crítico < 80 %"


def test_descrever_limites_de_metrica_informativa():
    assert formatos.descrever_limites(None, "req/s") == "Métrica informativa (sem regra de alerta)"


def test_hora_legivel_e_vazia_sem_ts():
    texto = formatos.hora(1_795_036_800)
    assert len(texto) == len("dd/mm/aaaa hh:mm:ss") and texto[2] == "/" and texto[13] == ":"
    assert formatos.hora(None) == "—"
