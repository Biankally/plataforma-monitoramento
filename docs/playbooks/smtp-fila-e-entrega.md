# SMTP: fila, entrega e erros

Métricas: `smtp.taxa_entrega_pct`, `smtp.fila`, `smtp.latencia_envio_s`, `smtp.rejeicoes`, `smtp.timeouts`,
`smtp.taxa_erro_pct`, `smtp.emails_min`.

## Sintoma
- Entrega: ATENÇÃO < 95 %, CRÍTICO < 80 % (`sent` / (`sent` + `deferred` + `bounced`) na janela).
- Fila: > 20 / > 100 mensagens. Atraso de envio (`delay=` do log): > 5 / > 30 s.
- Rejeições por janela: > 5 / > 20. Timeouts por janela: > 1 / > 5. Taxa de erro: > 5 % / > 20 %.
- Volume: > 60 / > 200 e-mails por minuto (envio em massa, possível spam ou abuso do "esqueci a senha").

## Diagnóstico
1. A fila: `dc exec smtp postqueue -p` (motivo de cada mensagem adiada) e `dc exec smtp postcat -q <id>` para ver uma.
2. Log: `dc logs smtp | grep -E 'status=(deferred|bounced)|NOQUEUE|timeout'`.
3. Entrega só para `@lab.local`: todo e-mail para esse domínio cai na caixa única `/var/mail/lab`; erro aqui aponta para
   o `main.cf` ou para disco cheio.
4. Rejeições (`NOQUEUE: reject`): origem e regra. Muitas de um mesmo IP = tentativa de relay.
5. Volume alto: o site está disparando e-mails? Compare com tentativas em `login.php`/`forgotpassword.php`
   (`access.log`) e veja `web.rps`.

## Ação
- Fila travada: corrija a causa (disco, `main.cf`) e force a reentrega: `dc exec smtp postqueue -f`.
- Fila de lixo: `dc exec smtp postsuper -d ALL deferred` (só depois de confirmar que são mensagens de teste).
- Abuso/relay: confirme `mynetworks` no `main.cf` (sem relay aberto) e registre a origem.
- Alteração de `main.cf` inesperada: veja `seguranca-configuracao-alterada.md`.
