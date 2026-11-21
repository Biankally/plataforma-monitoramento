"""Notificador de alertas por e-mail (camada 2).

Adaptador escolhido no .env pela variavel NOTIFICADOR:
- "arquivo": grava cada e-mail como .txt em NOTIF_DIR (testes e ensaio, sem internet);
- "smtp": envia de verdade (porta 587 com STARTTLS).
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def montar_email(alerta: dict) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = (
        f"[{alerta['nivel_novo']}] {alerta['servico']} — {alerta['metrica']} = {alerta['valor']}"
    )
    msg["From"] = os.environ.get("SMTP_REMETENTE", "monitor@lab.local")
    msg["To"] = os.environ.get("ALERTA_DESTINO", "equipe@lab.local")
    msg.set_content(
        f"Servico: {alerta['servico']}\n"
        f"Metrica: {alerta['metrica']}\n"
        f"Valor: {alerta['valor']} (limite: {alerta.get('limite')})\n"
        f"Nivel: {alerta['nivel_anterior']} -> {alerta['nivel_novo']}\n"
        f"Horario (epoch UTC): {alerta['ts']}\n"
        + (f"Detalhe: {alerta['detalhe']}\n" if alerta.get("detalhe") else "")
    )
    return msg


def enviar(alerta: dict) -> None:
    modo = os.environ.get("NOTIFICADOR", "arquivo")
    msg = montar_email(alerta)
    if modo == "arquivo":
        pasta = Path(os.environ.get("NOTIF_DIR", "notificacoes"))
        pasta.mkdir(parents=True, exist_ok=True)
        nome = f"{alerta['ts']}_{alerta['metrica']}_{alerta['nivel_novo']}.txt"
        (pasta / nome).write_text(msg.as_string(), encoding="utf-8")
    elif modo == "smtp":
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORTA", "587")), timeout=15) as s:
            s.starttls()
            s.login(os.environ["SMTP_USUARIO"], os.environ["SMTP_SENHA"])
            s.send_message(msg)
    else:
        raise ValueError(f"NOTIFICADOR invalido: {modo!r} (use 'arquivo' ou 'smtp')")
