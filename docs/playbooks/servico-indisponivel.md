# Serviço fora do ar

Métricas: `web.disponivel`, `db.disponivel`, `dns.disponivel`, `smtp.disponivel` (valor 0).

## Sintoma
- 1ª falha: **ATENÇÃO**; 2ª falha seguida (30 s): **CRÍTICO** e e-mail.
- Como cada sonda testa o protocolo, "fora do ar" quer dizer que o serviço **não respondeu direito**, mesmo que a porta
  esteja aberta: web respondeu HTTP 5xx ou nada; banco não executou `SELECT 1`; DNS não devolveu resposta com dados
  (NXDOMAIN, SERVFAIL, REFUSED e timeout contam); SMTP não deu banner 220 ou EHLO 250.
- Os outros serviços devem continuar OK. Se vários caírem juntos, suspeite do Docker ou da máquina (ver `host-recursos.md`).

## Diagnóstico
1. O container existe e está rodando? `dc ps` (procure `Exited`, `Restarting` ou `unhealthy`).
2. Por que parou? `dc logs --tail 100 <servico>` (procure erro de configuração, falta de memória ou `Killed`).
   `docker inspect <container> --format '{{.State.OOMKilled}}'` diz se o kernel matou por memória.
3. A porta responde de fora? `curl -I http://127.0.0.1:8080/` (web); `mysql -h 127.0.0.1 -P 3307 -u monitor -p -e 'SELECT 1'`
   (banco); `dig @127.0.0.1 -p 1053 teste.lab.local` (DNS); `nc 127.0.0.1 2525` e digite `EHLO teste` (SMTP).
4. Por serviço:
   - **web:** `dc logs web` (erro do PHP/Apache); o banco está no ar? (site sem banco devolve 500).
   - **db:** `dc logs db` (disco cheio, `max_connections`, volume corrompido); o `init.sql` só roda em volume novo.
   - **dns:** `dc exec dns unbound-checkconf` (erro de sintaxe no `unbound.conf`).
   - **smtp:** `dc exec smtp postfix check`; `dc logs smtp`.
5. A alteração foi recente? Veja também se houve alerta de `CONFIGURACAO` (`seguranca-configuracao-alterada.md`).

## Ação
- Container parado: `dc up -d <servico>` e confirme que a métrica volta a 1 em até 2 ciclos.
- Configuração quebrada: restaure o arquivo (git ou linha de base de segurança) e reinicie com `dc restart <servico>`.
- Morto por memória: confira o limite em `servicos/docker-compose.yml` e a causa (ataque? consulta pesada?) antes de aumentar.
- Não apague volumes (`down -v`) sem avisar o grupo: perde o banco do site.
- Se foi um teste de ataque do laboratório, registre horário e causa em `docs/LOG.md`.
