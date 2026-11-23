# Runbook — ataques de demonstração e teste de isolamento

Os scripts ficam em `testes/` e **só aceitam alvo em 127.0.0.1**. Qualquer outro endereço é recusado antes do primeiro pacote.
Pré-requisito: containers no ar, agente, API, coletor e dashboard rodando (ver `docs/guia-instalacao.md`).

| Ataque | Comando | O que deve aparecer no dashboard |
| --- | --- | --- |
| DDoS (inundação HTTP no web) | `python testes/ataque_ddos.py --segundos 60 --conexoes 50` | Pico de requisições/s no web; evento de DDoS; db, dns e smtp continuam verdes |
| Força bruta no login | `python testes/ataque_brute_force.py --criar-vitima` | Falhas de login por IP: 5 em 60 s = ATENÇÃO, 20 = CRÍTICO, com e-mail |
| Alteração de configuração | `docker compose -f servicos/docker-compose.yml exec smtp sh -c "echo '# alterado' >> /etc/postfix/main.cf"` | Hash diferente da linha de base; desfazer com `... exec smtp sed -i '$d' /etc/postfix/main.cf` |
| Isolamento (regra da professora) | `python testes/teste_isolamento.py --segundos 60` | Ao final, `APROVADO`; evidência em `testes/evidencias/isolamento-*.json` |

- **Força bruta:** a "vítima" é um usuário inventado criado na hora, com uma senha da lista. Por isso o ataque termina com `ENTROU` na tentativa 29.
- **Durante a apresentação:** deixe o dashboard aberto ao lado do terminal do ataque.
