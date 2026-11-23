# Runbook — smtp (Postfix)

- **Container:** `monitoramento-smtp-1` · **Porta:** `127.0.0.1:2525` · **Limites:** 0,5 CPU, 256 MB, 100 processos
- **Configuração:** `servicos/smtp/main.cf`: aceita só da rede interna; todo e-mail para `@lab.local` cai na caixa `/var/mail/lab`
- **Log:** saída do container (`docker compose logs smtp`), com uma linha `status=sent|deferred|bounced` por entrega

Todos os comandos são rodados dentro de `servicos/`.

| Ação | Comando |
| --- | --- |
| Iniciar | `docker compose up -d smtp` |
| Parar | `docker compose stop smtp` |
| Reiniciar | `docker compose restart smtp` |
| Reconstruir (mudou o `main.cf`) | `docker compose up -d --build smtp` |

## Verificar
```bash
python -c "import smtplib; s=smtplib.SMTP('127.0.0.1',2525,timeout=5); print(s.ehlo()[0]); s.sendmail('a@lab.local',['ana@lab.local'],'Subject: teste\n\nok'); s.quit()"
docker compose logs --tail 5 smtp | grep status=          # status=sent
docker compose exec smtp postqueue -j                     # fila (vazio = fila zerada)
docker compose exec smtp ls /var/mail/lab/new             # e-mails entregues
```

## Problemas
| Sintoma | O que fazer |
| --- | --- |
| `Relay access denied` | O remetente está fora de `mynetworks`; no laboratório, envie só de dentro da máquina |
| Fila crescendo (`postqueue -j`) | Destino fora de `lab.local` não é entregue (não há internet de saída); `docker compose exec smtp postsuper -d ALL` limpa a fila |
| "Erro no envio" no esqueci a senha | `docker compose ps smtp`; veja `docker compose logs web` (o PHPMailer registra o motivo) |
