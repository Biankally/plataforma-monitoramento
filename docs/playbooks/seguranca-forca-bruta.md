# Segurança: força bruta no login

Evento `AUTENTICACAO` em `GET /api/seguranca` (serviço web, `origem` = IP).

## Sintoma
- Falhas de login do mesmo IP em 60 s: **ATENÇÃO** a partir de 5, **CRÍTICO** a partir de 20. Cada IP é avaliado
  sozinho (muitas tentativas espalhadas por IPs diferentes não somam; veja o detalhe nos logs).
- A fonte é o log `/var/log/app/login.log` do site, uma linha JSON por tentativa (`ts`, `origem`, `usuario`, `sucesso`).
- Aviso novo só se o nível subir ou depois de 5 min.
- Pode vir com `web.taxa_erro_4xx_pct` e `db.conexoes_abortadas` altos.

## Diagnóstico
1. Veja as tentativas: `dc exec web tail -n 200 /var/log/app/login.log | grep '"sucesso": false'`.
2. Que usuários são tentados? Um só (alvo) ou vários (enumeração: o site mostra mensagens diferentes para "e-mail não
   encontrado" e "senha incorreta", fraqueza mantida de propósito)?
3. Houve **sucesso** depois de muitas falhas do mesmo IP? Então a conta pode ter sido comprometida.
4. O IP é do laboratório (script de ataque de P1) ou desconhecido?

## Ação
- Registre IP, usuários e horário em `docs/LOG.md`.
- Conta comprometida: troque a senha do usuário no banco e invalide `reset_token`.
- Bloqueio do IP: firewall do host (P1). O site não limita tentativas (fraqueza intencional do alvo): no relatório,
  documente a mitigação recomendada (limite de tentativas, atraso progressivo, CAPTCHA, mensagem única de erro).
- Se foi teste do laboratório, confirme que o alerta chegou por e-mail e guarde as evidências.
