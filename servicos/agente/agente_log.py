"""Leitura incremental de arquivo de log: a cada chamada, so as linhas que chegaram desde a anterior.

Guarda a posicao (em bytes) onde parou. Cuida de tres situacoes reais:
- o arquivo foi rotacionado/recriado (ficou menor que a posicao ou trocou de inode): volta ao inicio;
- o arquivo sumiu: devolve lista vazia e, quando voltar, le desde o inicio;
- a ultima linha ainda esta sendo escrita (sem \\n no fim): espera a proxima leitura.
"""

from __future__ import annotations

import sys
from pathlib import Path


class LeitorIncremental:
    def __init__(self, caminho: Path, desde_o_inicio: bool = False) -> None:
        self.caminho = Path(caminho)
        self._posicao = 0
        self._inode: int | None = None
        if not desde_o_inicio and self.caminho.is_file():
            # comeca do fim: o historico antigo nao e contado como se fosse agora
            info = self.caminho.stat()
            self._posicao, self._inode = info.st_size, info.st_ino

    def linhas_novas(self) -> list[str]:
        try:
            info = self.caminho.stat()
        except FileNotFoundError:
            self._posicao, self._inode = 0, None
            return []
        if info.st_ino != self._inode or info.st_size < self._posicao:
            self._posicao, self._inode = 0, info.st_ino   # rotacionado ou recriado

        with self.caminho.open("rb") as f:
            f.seek(self._posicao)
            bloco = f.read()
        fim = bloco.rfind(b"\n")
        if fim < 0:
            return []                                     # nenhuma linha completa ainda
        self._posicao += fim + 1
        texto = bloco[:fim].decode("utf-8", errors="replace")
        return [linha for linha in texto.split("\n") if linha.strip()]


def avisar(mensagem: str) -> None:
    """Aviso no terminal do agente (stderr), para nenhum problema passar calado."""
    print(f"[agente] {mensagem}", file=sys.stderr, flush=True)
