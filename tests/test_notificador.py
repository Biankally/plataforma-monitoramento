"""Notificador em modo arquivo (usado nos testes e nas evidencias): nenhum e-mail pode se perder."""

from __future__ import annotations

from plataforma.infra import notificador


def _alerta(servico, detalhe):
    return dict(ts=1795000000, servico=servico, metrica="seguranca.vulnerabilidade", nivel_anterior="OK",
                nivel_novo="ATENCAO", valor=1.0, limite=None, detalhe=detalhe)


def test_dois_avisos_no_mesmo_segundo_viram_dois_arquivos(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTIFICADOR", "arquivo")
    monkeypatch.setenv("NOTIF_DIR", str(tmp_path))
    notificador.enviar(_alerta("web", "CVE-A"))
    notificador.enviar(_alerta("web", "CVE-B"))     # mesmo segundo, mesma metrica, mesmo nivel
    notificador.enviar(_alerta("dns", "CVE-C"))
    arquivos = sorted(tmp_path.glob("*.txt"))
    assert len(arquivos) == 3, f"um e-mail sobrescreveu outro: {[a.name for a in arquivos]}"
    textos = " ".join(a.read_text(encoding="utf-8") for a in arquivos)
    assert all(cve in textos for cve in ("CVE-A", "CVE-B", "CVE-C"))
