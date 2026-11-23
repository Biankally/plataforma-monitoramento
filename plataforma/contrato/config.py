"""Leitura de configuracao (camada 0).

- Raiz do projeto: encontrada procurando o pyproject.toml, para os scripts
  funcionarem de qualquer pasta.
- Arquivos em config/ (TOML, lido pela biblioteca padrao tomllib).
- Segredos e caminhos no .env (formato CHAVE=valor), nunca no codigo.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


def raiz_do_projeto(inicio: Path | None = None) -> Path:
    atual = (inicio or Path(__file__)).resolve()
    for pasta in (atual, *atual.parents):
        if (pasta / "pyproject.toml").is_file():
            return pasta
    raise FileNotFoundError("pyproject.toml nao encontrado: rode a partir do repositorio")


def carregar_env(arquivo: Path | None = None) -> None:
    """Le o .env e coloca no ambiente o que ainda nao estiver definido."""
    caminho = arquivo or raiz_do_projeto() / ".env"
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def pasta_config() -> Path:
    return Path(os.environ.get("MONITOR_CONFIG_DIR") or raiz_do_projeto() / "config")


def ler_toml(nome: str) -> dict:
    with (pasta_config() / nome).open("rb") as f:
        return tomllib.load(f)


@dataclass(frozen=True)
class ServicoMonitorado:
    nome: str
    tipo: str  # "http" ou "tcp"
    url: str = ""
    host: str = ""
    porta: int = 0
    timeout_s: float = 3.0


def servicos_monitorados() -> list[ServicoMonitorado]:
    dados = ler_toml("servicos.toml")
    return [ServicoMonitorado(**s) for s in dados.get("servico", [])]


def plataforma() -> dict:
    return ler_toml("servicos.toml").get("plataforma", {})


def regras_alerta() -> dict[str, dict]:
    return ler_toml("regras.toml")


def vulnerabilidades_conhecidas() -> list[dict]:
    """Lista de CVEs de config/vulnerabilidades.toml (vazia se o arquivo nao existir)."""
    if not (pasta_config() / "vulnerabilidades.toml").is_file():
        return []
    return list(ler_toml("vulnerabilidades.toml").get("vulnerabilidade", []))
