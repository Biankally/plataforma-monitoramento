from plataforma.dominio.alertas import Estado, Regra, avaliar, classificar
from plataforma.dominio.taxas import taxa_por_segundo

LATENCIA = Regra("web.latencia_ms", ">", atencao=500, critico=2000)
DISPONIVEL = Regra("web.disponivel", "<", atencao=1, critico=1, atencao_imediata=True)


def rodar(regra, valores):
    estado, niveis = Estado(), []
    for v in valores:
        estado, _ = avaliar(regra, estado, v)
        niveis.append(estado.nivel)
    return niveis


def test_classificacao_pelos_limites():
    assert [classificar(LATENCIA, v) for v in (100, 800, 3000)] == ["OK", "ATENCAO", "CRITICO"]


def test_sobe_so_depois_de_duas_amostras_seguidas():
    assert rodar(LATENCIA, [800, 800]) == ["OK", "ATENCAO"]


def test_sabotagem_pico_isolado_nao_dispara():
    assert rodar(LATENCIA, [3000, 100, 3000, 100]) == ["OK", "OK", "OK", "OK"]


def test_desce_so_depois_de_tres_amostras_normais():
    assert rodar(LATENCIA, [800, 800, 100, 100, 100]) == ["OK", "ATENCAO", "ATENCAO", "ATENCAO", "OK"]


def test_salto_direto_para_critico():
    assert rodar(LATENCIA, [3000, 3000]) == ["OK", "CRITICO"]


def test_disponibilidade_primeira_falha_atencao_segunda_critico():
    assert rodar(DISPONIVEL, [1, 0, 0]) == ["OK", "ATENCAO", "CRITICO"]


def test_mudanca_de_nivel_e_informada_uma_vez():
    estado, mudancas = Estado(), []
    for v in [0, 0, 0, 0]:
        estado, mudou = avaliar(DISPONIVEL, estado, v)
        mudancas.append(mudou)
    assert mudancas == [True, True, False, False]


def test_taxa_a_partir_de_contador():
    assert taxa_por_segundo(10000, 10750, 15) == 50


def test_sabotagem_contador_reiniciado_nao_gera_taxa_negativa():
    assert taxa_por_segundo(10750, 12, 15) is None
