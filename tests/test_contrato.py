import pytest

from plataforma.contrato.metricas import ErroContrato, validar_lote

VALIDO = {"ts": 1795036800, "amostras": [{"servico": "web", "metrica": "web.latencia_ms", "valor": 42.7}]}


def test_lote_valido_e_aceito():
    lote = validar_lote(VALIDO)
    assert lote.ts == 1795036800 and lote.amostras[0].valor == 42.7


@pytest.mark.parametrize(
    "sabotagem",
    [
        {"ts": 1795036800, "amostras": [{"servico": "web", "metrica": "web.inventada", "valor": 1}]},
        {"ts": 1795036800, "amostras": [{"servico": "db", "metrica": "web.latencia_ms", "valor": 1}]},
        {"ts": 1795036800, "amostras": [{"servico": "web", "metrica": "web.latencia_ms", "valor": "42"}]},
        {"ts": 1795036800, "amostras": [{"servico": "web", "metrica": "web.latencia_ms", "valor": float("nan")}]},
        {"ts": "ontem", "amostras": VALIDO["amostras"]},
        {"ts": 1795036800, "amostras": []},
        [],
    ],
)
def test_sabotagem_lote_fora_do_contrato_e_recusado(sabotagem):
    with pytest.raises(ErroContrato):
        validar_lote(sabotagem)
