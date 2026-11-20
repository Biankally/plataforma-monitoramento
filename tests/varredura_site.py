"""Varredura do site vulneravel (servicos/web-vuln/site) e do banco (servicos/banco).

Duas perguntas, cada uma uma funcao que devolve a lista de problemas (lista vazia = tudo certo):
- conexoes_fora_do_lugar: alguem abre conexao com o MySQL fora do arquivo unico db.php?
- segredos: sobrou senha, usuario root ou e-mail real escrito no codigo?
A pasta vendor/ (biblioteca PHPMailer, codigo de terceiros) fica de fora.
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SITE = RAIZ / "servicos" / "web-vuln" / "site"
BANCO = RAIZ / "servicos" / "banco"

EXTENSOES_TEXTO = {".php", ".html", ".js", ".css", ".sql", ".sh", ".json"}

# Cada padrao e um jeito de vazar segredo ou dado real que ja apareceu no site original.
PADROES_PROIBIDOS = {
    "e-mail do gmail": re.compile(r"[\w.+-]+@gmail\.com", re.IGNORECASE),
    "servidor smtp do gmail": re.compile(r"smtp\.gmail\.com", re.IGNORECASE),
    "usuario root do MySQL": re.compile(r"""["']root["']"""),
    "credencial de e-mail escrita no codigo": re.compile(
        r"""define\(\s*["']MAIL_(USERNAME|PASSWORD)["']\s*,\s*["'][^"']+["']"""),
    "senha escrita no codigo": re.compile(r"""\$(password|senha|pass)\s*=\s*["'][^"']+["']""",
                                          re.IGNORECASE),
}


def arquivos_texto(pasta: Path) -> list[Path]:
    """Arquivos de texto da pasta, sem a vendor/."""
    return sorted(p for p in pasta.rglob("*")
                  if p.is_file() and p.suffix.lower() in EXTENSOES_TEXTO and "vendor" not in p.parts)


def conexoes_fora_do_lugar(pasta: Path) -> list[str]:
    """Arquivos PHP que criam conexao com o banco sem ser o db.php."""
    problemas = []
    for arquivo in arquivos_texto(pasta):
        if arquivo.suffix != ".php" or arquivo.name == "db.php":
            continue
        if "new mysqli" in arquivo.read_text(encoding="utf-8", errors="replace"):
            problemas.append(str(arquivo.relative_to(pasta)))
    return problemas


def segredos(*pastas: Path) -> list[str]:
    """Linhas com senha, root ou e-mail real. Formato: 'arquivo:linha: motivo'."""
    problemas = []
    for pasta in pastas:
        for arquivo in arquivos_texto(pasta):
            texto = arquivo.read_text(encoding="utf-8", errors="replace")
            for numero, linha in enumerate(texto.splitlines(), start=1):
                for motivo, padrao in PADROES_PROIBIDOS.items():
                    if padrao.search(linha):
                        problemas.append(f"{arquivo.relative_to(pasta)}:{numero}: {motivo}")
    return problemas
