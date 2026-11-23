"""Vulnerabilidade conhecida por servico (enunciado, secao 5): versao do programa x lista de CVEs."""

from __future__ import annotations

import pytest

from plataforma.contrato import config
from plataforma.dominio import vulnerabilidades as v

CATALOGO = [
    {"servico": "dns", "programa": "unbound", "cve": "CVE-2024-8508", "corrigido_em": "1.21.1",
     "nivel": "ATENCAO", "descricao": "compressao de nomes sem limite (DoS)"},
    {"servico": "web", "programa": "apache", "cve": "CVE-2024-40725", "afeta_desde": "2.4.60",
     "corrigido_em": "2.4.62", "nivel": "CRITICO", "descricao": "vazamento de codigo-fonte"},
    {"servico": "smtp", "programa": "postfix", "cve": "CVE-2023-51764", "ramo": "3.8",
     "corrigido_em": "3.8.5", "nivel": "ATENCAO", "descricao": "SMTP smuggling"},
]


@pytest.mark.parametrize("texto,esperado", [("1.20.0", (1, 20, 0)), ("8.0.40", (8, 0, 40)),
                                            ("2.4.62", (2, 4, 62)), ("3.9", (3, 9, 0))])
def test_versao_vira_numeros_comparaveis(texto, esperado):
    assert v.versao_em_tupla(texto) == esperado


def test_versao_antiga_e_vulneravel_e_a_corrigida_nao():
    entrada = CATALOGO[0]
    assert v.vulneravel("1.20.0", entrada) is True
    assert v.vulneravel("1.21.1", entrada) is False
    assert v.vulneravel("1.22.0", entrada) is False


def test_falha_que_so_afeta_uma_faixa_de_versoes():
    entrada = CATALOGO[1]   # afeta 2.4.60 e 2.4.61 apenas
    assert v.vulneravel("2.4.59", entrada) is False
    assert v.vulneravel("2.4.61", entrada) is True
    assert v.vulneravel("2.4.62", entrada) is False


def test_ramo_diferente_nao_conta():
    entrada = CATALOGO[2]   # so o ramo 3.8 tem a correcao em 3.8.5
    assert v.vulneravel("3.8.4", entrada) is True
    assert v.vulneravel("3.9.0", entrada) is False
    assert v.vulneravel("3.7.12", entrada) is False, "3.7.12 ja tem a correcao do ramo 3.7"


def test_avaliar_gera_um_evento_por_falha_encontrada():
    versoes = {"dns": {"unbound": "1.20.0"}, "web": {"apache": "2.4.65", "php": "8.3.20"},
               "smtp": {"postfix": "3.8.4"}}
    eventos = v.avaliar_versoes(versoes, CATALOGO)
    assert sorted((e.servico, e.nivel) for e in eventos) == [("dns", "ATENCAO"), ("smtp", "ATENCAO")]
    dns = next(e for e in eventos if e.servico == "dns")
    assert dns.tipo == "VULNERABILIDADE"
    assert dns.origem == "unbound 1.20.0"
    assert "CVE-2024-8508" in dns.detalhe and "1.21.1" in dns.detalhe


def test_sabotagem_versao_desconhecida_nao_inventa_falha_nem_quebra():
    versoes = {"dns": {"unbound": None}, "web": {"apache": "versao-estranha"}}
    assert v.avaliar_versoes(versoes, CATALOGO) == []


def test_catalogo_do_projeto_e_valido():
    catalogo = config.vulnerabilidades_conhecidas()
    assert len(catalogo) >= 5
    for entrada in catalogo:
        assert entrada["servico"] in {"web", "db", "dns", "smtp"}
        assert entrada["nivel"] in {"ATENCAO", "CRITICO"}
        assert entrada["cve"].startswith("CVE-")
        v.versao_em_tupla(entrada["corrigido_em"])   # versao legivel
        assert entrada["fonte"].startswith("https://"), f"{entrada['cve']} sem fonte"
