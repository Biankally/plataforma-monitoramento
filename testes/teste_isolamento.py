"""Teste de isolamento (regra da professora): atacar o web NAO pode derrubar db, dns e smtp.

Durante o ataque DDoS ao web, uma sonda por servico roda a cada segundo, com o protocolo de
verdade (aperto de mao do MySQL, consulta DNS, EHLO do SMTP). Aprovado se cada servico
respondeu em pelo menos 95% das vezes. O resultado vai para testes/evidencias/ (anexo do relatorio).

Uso (no WSL, com os containers no ar):
    python testes/teste_isolamento.py --segundos 60 --conexoes 50
"""

from __future__ import annotations

import argparse
import json
import smtplib
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import dns.exception
import dns.resolver

import ataque_ddos

MINIMO_OK = 0.95
EVIDENCIAS = Path(__file__).resolve().parent / "evidencias"


def vigiar(sondas: dict[str, Callable[[], bool]], segundos: float, intervalo_s: float = 1.0) -> dict:
    """Chama cada sonda a cada intervalo e conta quantas vezes respondeu (com o tempo de resposta)."""
    servicos = {nome: {"ok": 0, "total": 0, "pior_ms": 0.0} for nome in sondas}
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        for nome, sonda in sondas.items():
            inicio = time.monotonic()
            try:
                respondeu = bool(sonda())
            except (OSError, smtplib.SMTPException, dns.exception.DNSException):
                respondeu = False   # sonda que falha conta como servico fora do ar
            ms = (time.monotonic() - inicio) * 1000
            r = servicos[nome]
            r["total"] += 1
            r["ok"] += respondeu
            r["pior_ms"] = round(max(r["pior_ms"], ms), 1)
        time.sleep(intervalo_s)
    aprovado = all(r["total"] and r["ok"] / r["total"] >= MINIMO_OK for r in servicos.values())
    return {"aprovado": aprovado, "servicos": servicos}


# ---------- sondas de verdade (portas do servicos/docker-compose.yml) ----------

def sonda_db(host: str = "127.0.0.1", porta: int = 3307) -> bool:
    """O MySQL manda um pacote de saudacao com o byte 10 (versao do protocolo) na 5a posicao."""
    with socket.create_connection((host, porta), timeout=3) as s:
        s.settimeout(3)
        return s.recv(5)[4:5] == b"\x0a"


def sonda_dns(host: str = "127.0.0.1", porta: int = 1053) -> bool:
    r = dns.resolver.Resolver(configure=False)
    r.nameservers, r.port, r.lifetime = [host], porta, 3
    return r.resolve("teste.lab.local", "A")[0].to_text() == "192.0.2.10"


def sonda_smtp(host: str = "127.0.0.1", porta: int = 2525) -> bool:
    with smtplib.SMTP(host, porta, timeout=3) as smtp:
        return smtp.ehlo()[0] == 250


def testar(segundos: float, conexoes: int) -> dict:
    """Ataca o web numa thread e vigia os outros 3 servicos ao mesmo tempo."""
    resultado_ataque: dict = {}
    ataque = threading.Thread(daemon=True, target=lambda: resultado_ataque.update(
        ataque_ddos.inundar(ataque_ddos.ALVO_PADRAO, segundos, conexoes, mostrar=False)))
    ataque.start()
    relatorio = vigiar({"db": sonda_db, "dns": sonda_dns, "smtp": sonda_smtp}, segundos)
    ataque.join()
    return {**relatorio, "ataque_web": resultado_ataque}


def main() -> int:
    p = argparse.ArgumentParser(description="DDoS no web enquanto vigia db, dns e smtp")
    p.add_argument("--segundos", type=float, default=60)
    p.add_argument("--conexoes", type=int, default=50)
    args = p.parse_args()
    print(f"Atacando o web por {args.segundos:.0f} s e vigiando db, dns e smtp...")
    relatorio = {"quando": datetime.now().isoformat(timespec="seconds"), **testar(args.segundos, args.conexoes)}
    for nome, r in relatorio["servicos"].items():
        print(f"  {nome:5s} respondeu {r['ok']}/{r['total']}  (pior tempo {r['pior_ms']} ms)")
    print(f"  web   recebeu {relatorio['ataque_web']['rps']} req/s")
    print("APROVADO: o ataque ao web nao derrubou os outros" if relatorio["aprovado"] else "REPROVADO")
    EVIDENCIAS.mkdir(exist_ok=True)
    arquivo = EVIDENCIAS / f"isolamento-{datetime.now():%Y%m%d-%H%M%S}.json"
    arquivo.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Evidencia salva em {arquivo}")
    return 0 if relatorio["aprovado"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
