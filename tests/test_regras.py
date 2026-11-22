"""Testes das regras de alerta em config/regras.toml (tarefa 5 do P2).

Garante que o arquivo carrega sem erro, que toda regra aponta para uma metrica
do catalogo, que os limites fazem sentido e que cada metrica do catalogo ou
tem regra ou esta na lista de "somente informativas" (com motivo).
"""

import tomllib

from plataforma.contrato.config import regras_alerta
from plataforma.contrato.metricas import METRICAS
from plataforma.dominio.alertas import Estado, avaliar, classificar, regra_de_dict

# Metricas que aparecem no dashboard mas nao tem limite proprio. Cada uma
# tem um motivo; se uma delas ganhar regra, tire-a daqui.
SOMENTE_INFORMATIVAS: dict[str, str] = {
    "web.rps": "pico de trafego e tratado pela deteccao de anomalia (escore z) em seguranca.py",
    "web.req_4xx": "contagem bruta; o limite esta na taxa web.taxa_erro_4xx_pct",
    "web.req_5xx": "contagem bruta; o limite esta na taxa web.taxa_erro_5xx_pct",
    "db.qps": "volume normal depende da carga; pico tratado por anomalia",
    "db.conexoes": "o limite esta em db.uso_conexoes_pct (proporcao de max_connections)",
    "db.threads_cache": "informativa, sem limite util",
    "dns.qps": "volume normal depende da carga; pico tratado por anomalia",
    "smtp.rejeicoes": "contagem bruta; o limite esta em smtp.taxa_erro_pct",
    "smtp.timeouts": "contagem bruta; o limite esta em smtp.taxa_erro_pct",
    "smtp.emails_min": "volume normal depende da carga; pico tratado por anomalia",
    "host.disco_io_kbs": "volume de I/O sem limite fixo; o limite esta em host.disco_latencia_ms",
}


def verificar_regras(regras: dict) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia = regras boas)."""
    problemas = []
    for metrica, dados in regras.items():
        if metrica not in METRICAS:
            problemas.append(f"{metrica}: metrica fora do catalogo")
            continue
        try:
            regra = regra_de_dict(metrica, dados)
        except (TypeError, ValueError) as erro:
            problemas.append(f"{metrica}: regra invalida ({erro})")
            continue
        if regra.operador == ">" and regra.critico < regra.atencao:
            problemas.append(f"{metrica}: com '>' o critico ({regra.critico}) nao pode ser menor que a atencao ({regra.atencao})")
        if regra.operador == "<" and regra.critico > regra.atencao:
            problemas.append(f"{metrica}: com '<' o critico ({regra.critico}) nao pode ser maior que a atencao ({regra.atencao})")
    return problemas


def test_arquivo_carrega_e_todas_as_regras_sao_validas():
    regras = regras_alerta()
    assert regras, "regras.toml vazio"
    assert verificar_regras(regras) == []


def test_toda_metrica_do_catalogo_tem_regra_ou_motivo_para_nao_ter():
    com_regra = set(regras_alerta())
    sem_regra = set(METRICAS) - com_regra - set(SOMENTE_INFORMATIVAS)
    assert sorted(sem_regra) == []


def test_lista_de_informativas_nao_tem_metrica_inventada_nem_com_regra():
    regras = set(regras_alerta())
    assert [m for m in SOMENTE_INFORMATIVAS if m not in METRICAS] == []
    assert sorted(m for m in SOMENTE_INFORMATIVAS if m in regras) == []


def test_disponibilidade_dos_quatro_servicos_alerta_na_primeira_falha():
    regras = regras_alerta()
    for servico in ("web", "db", "dns", "smtp"):
        regra = regra_de_dict(f"{servico}.disponivel", regras[f"{servico}.disponivel"])
        assert regra.atencao_imediata, servico
        estado, _ = avaliar(regra, Estado(), 0)
        assert estado.nivel == "ATENCAO", servico
        estado, _ = avaliar(regra, estado, 0)
        assert estado.nivel == "CRITICO", servico


def test_valor_saudavel_de_cada_regra_fica_em_ok():
    """Um valor claramente bom (longe dos limites) nunca pode alertar."""
    regras = regras_alerta()
    for metrica, dados in regras.items():
        regra = regra_de_dict(metrica, dados)
        bom = 1 if metrica.endswith(".disponivel") else (0 if regra.operador == ">" else 100)
        assert classificar(regra, bom) == "OK", f"{metrica} com valor {bom}"


def test_valor_ruim_de_cada_regra_chega_a_critico():
    regras = regras_alerta()
    for metrica, dados in regras.items():
        regra = regra_de_dict(metrica, dados)
        if regra.operador == ">":
            ruim = regra.critico + 1
        else:
            ruim = regra.critico - 1
        assert classificar(regra, ruim) == "CRITICO", metrica


# --- Sabotagens: o verificador precisa acusar regra estragada -----------------

def _ler(texto: str) -> dict:
    return tomllib.loads(texto)


def test_sabotagem_metrica_inventada_e_acusada():
    ruins = _ler('["web.inventada"]\noperador = ">"\natencao = 1\ncritico = 2\n')
    assert any("fora do catalogo" in p for p in verificar_regras(ruins))


def test_sabotagem_critico_menor_que_atencao_e_acusado():
    ruins = _ler('["web.latencia_ms"]\noperador = ">"\natencao = 2000\ncritico = 500\n')
    assert any("critico" in p for p in verificar_regras(ruins))
    ruins = _ler('["smtp.taxa_entrega_pct"]\noperador = "<"\natencao = 80\ncritico = 95\n')
    assert any("critico" in p for p in verificar_regras(ruins))


def test_sabotagem_operador_ou_campo_invalido_e_acusado():
    ruins = _ler('["web.latencia_ms"]\noperador = "="\natencao = 1\ncritico = 2\n')
    assert any("invalida" in p for p in verificar_regras(ruins))
    ruins = _ler('["web.latencia_ms"]\noperador = ">"\natencao = 1\ncritico = 2\nlimite_extra = 3\n')
    assert any("invalida" in p for p in verificar_regras(ruins))
    ruins = _ler('["web.latencia_ms"]\noperador = ">"\natencao = 1\n')
    assert any("invalida" in p for p in verificar_regras(ruins))
