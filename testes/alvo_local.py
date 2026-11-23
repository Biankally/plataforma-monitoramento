"""Trava de seguranca dos scripts de ataque: so aceitam alvo na propria maquina (127.0.0.1).

Os ataques existem para testar a NOSSA plataforma. Atacar qualquer outro endereco (rede da
faculdade, site de terceiros) e proibido; por isso o script para antes de mandar o 1o pacote.
"""

from __future__ import annotations

import sys
from urllib.parse import urlsplit

PERMITIDOS = {"127.0.0.1", "localhost"}


def garantir(url: str) -> str:
    """Devolve a url se o alvo for a propria maquina; senao encerra o programa com a explicacao."""
    host = (urlsplit(url).hostname or "").lower()
    if host not in PERMITIDOS:
        sys.exit(f"RECUSADO: o alvo '{host}' nao e a propria maquina. Use so 127.0.0.1 (laboratorio).")
    return url
