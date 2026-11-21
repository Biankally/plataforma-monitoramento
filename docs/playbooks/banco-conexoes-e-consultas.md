# Banco de dados: conexões e consultas

Métricas: `db.uso_conexoes_pct`, `db.conexoes_executando`, `db.conexoes_abortadas`, `db.slow_queries_min`,
`db.rollbacks_s`, `db.qps`.

## Sintoma
- Uso de conexões: ATENÇÃO > 70 %, CRÍTICO > 90 % de `max_connections` (acima disso o MySQL recusa conexões novas e o
  site passa a dar 5xx).
- Conexões executando (`Threads_running`): > 20 / > 50 (consultas disputando CPU).
- Conexões abortadas (por janela de 15 s): > 5 / > 20 (senha errada, cliente que cai, tentativa de acesso).
- Consultas lentas por minuto: > 5 / > 30. Rollbacks por segundo: > 1 / > 5. Consultas por segundo: > 300 / > 1000.

## Diagnóstico
1. Quem está conectado? `dc exec db mysql -uroot -p -e 'SHOW FULL PROCESSLIST'` (usuário, origem, tempo, consulta).
2. Consultas lentas: `SHOW GLOBAL STATUS LIKE 'Slow_queries'` e, se o log estiver ligado, o slow log do container.
3. Conexões abortadas: `SHOW GLOBAL STATUS LIKE 'Aborted_%'`; erros de acesso em `dc logs db`.
   Pico de abortadas com `web.taxa_erro_4xx_pct` alto sugere ataque de força bruta ou injeção no site.
4. `db.qps` alto junto com `web.rps` alto: carga legítima ou DDoS no site (`seguranca-ddos.md`).
5. Rollbacks altos: erros na aplicação (veja `dc logs web`) ou deadlocks (`SHOW ENGINE INNODB STATUS`).

## Ação
- Consulta que trava tudo: `KILL <id>`; depois corrija a consulta ou crie o índice.
- Conexões esgotadas por clientes presos: reinicie o `web` (`dc restart web`) para soltá-las; só aumente `max_connections`
  se a memória do container permitir (limite de 1 GB).
- Abortadas por tentativa de acesso: confirme a origem e trate como segurança (`seguranca-forca-bruta.md`).
- Nunca use o usuário `monitor` para consertar: ele só tem `SELECT` e `PROCESS` de propósito.
