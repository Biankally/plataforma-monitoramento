# Latência alta

Métricas: `web.latencia_ms`, `web.latencia_p95_ms`, `db.latencia_ms`, `dns.latencia_ms`, `smtp.latencia_ms`.

## Sintoma
- Limites (ATENÇÃO / CRÍTICO): web 500 / 2000 ms; p95 do tempo de servidor 300 / 1000 ms; banco 100 / 1000 ms;
  DNS 100 / 500 ms; SMTP 1000 / 5000 ms.
- `*.latencia_ms` é o tempo da sonda (de fora). `web.latencia_p95_ms` é o percentil 95 do tempo que o servidor gastou,
  lido do log. Latência da sonda alta com p95 normal aponta para a rede ou para a fila de conexões, não para o PHP.
- O serviço ainda responde; se parar de responder, vira `servico-indisponivel.md`.

## Diagnóstico
1. Há pico de tráfego? Veja `web.rps`, `web.conexoes_ativas`, `dns.qps` no dashboard e eventos `TRAFEGO` em
   `GET /api/seguranca` (ver `seguranca-ddos.md`).
2. A máquina está sobrecarregada? `host.cpu_pct`, `host.mem_pct`, `host.disco_latencia_ms` (ver `host-recursos.md`).
3. Container no limite? `docker stats --no-stream`: CPU colada no limite do container indica estrangulamento.
4. **web:** o tempo está no banco? Compare com `db.latencia_ms` e `db.slow_queries_min`.
5. **db:** `dc exec db mysql -uroot -p -e 'SHOW FULL PROCESSLIST'` (consultas longas) e `db.uso_conexoes_pct`.
6. **dns:** `dc exec dns unbound-control stats_noreset | grep -E 'total.num|recursion'` (muitas consultas recursivas lentas).
7. **smtp:** `dc exec smtp postqueue -p` (fila grande deixa o diálogo lento) e `dc logs smtp | grep -i -E 'timeout|slow'`.

## Ação
- Se for tráfego anormal, trate como ataque (`seguranca-ddos.md`).
- Consulta presa no banco: `KILL <id>` (do `SHOW PROCESSLIST`) e investigue a consulta.
- Container estrangulado por limite: avalie subir o limite no `docker-compose.yml` só se a carga for legítima.
- Reinicie o serviço só como último recurso e anote no `docs/LOG.md`.
