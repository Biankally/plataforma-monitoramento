from pathlib import Path

from tests.camadas import violacoes

RAIZ = Path(__file__).resolve().parents[1]


def test_projeto_respeita_as_camadas():
    assert violacoes(RAIZ / "plataforma") == []


def test_sabotagem_import_proibido_e_acusado(tmp_path):
    (tmp_path / "dominio").mkdir()
    (tmp_path / "dominio" / "regra.py").write_text(
        "from plataforma.api.app import criar_app\n", encoding="utf-8"
    )
    problemas = violacoes(tmp_path)
    assert len(problemas) == 1 and "dominio/regra.py:1" in problemas[0]


def test_sabotagem_import_simples_tambem_e_acusado(tmp_path):
    (tmp_path / "contrato").mkdir()
    (tmp_path / "contrato" / "x.py").write_text("import plataforma.infra.banco\n", encoding="utf-8")
    assert violacoes(tmp_path)
