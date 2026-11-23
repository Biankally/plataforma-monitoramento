# Runbook — web (Apache + PHP + site Receitas Práticas)

- **Container:** `monitoramento-web-1` · **Porta:** `127.0.0.1:8080` · **Limites:** 1 CPU, 512 MB, 200 processos
- **Site:** `servicos/web-vuln/site/`, montado só leitura em `/var/www/html/receitas_práticas/`
- **Logs:** `servicos/logs/web/login.log` e `servicos/logs/web/acesso.log`
  - `login.log`: uma linha JSON por tentativa: `{"ts": 1795036790, "origem": "IP", "usuario": "email", "sucesso": false}`
  - `acesso.log`: uma linha por requisição: `código tempo_em_microssegundos` (ex.: `200 1830`)

Todos os comandos são rodados dentro de `servicos/`.

| Ação | Comando |
| --- | --- |
| Iniciar | `docker compose up -d web` |
| Parar | `docker compose stop web` |
| Reiniciar | `docker compose restart web` |
| Reconstruir (mudou `Dockerfile` ou `.conf`) | `docker compose up -d --build web` |
| Estado | `docker compose ps web` |

## Verificar
```bash
curl -sI http://127.0.0.1:8080/ | head -1                          # HTTP/1.1 302 (redireciona para o site)
curl -s "http://127.0.0.1:8080/server-status?auto" | head -3       # Total Accesses, ...
tail -3 logs/web/login.log                                         # últimas tentativas de login
docker compose logs --tail 20 web                                  # erros do Apache/PHP
```

## Problemas
| Sintoma | O que fazer |
| --- | --- |
| "Falha na conexão com o banco de dados" | `docker compose ps db`; se o db estiver Up, veja `docker compose logs web` (o motivo real fica lá) |
| `login.log` não cresce | `docker compose exec web ls -l /var/log/app` (dono tem que ser `www-data`); reinicie o web |
| `/server-status` dá 403 | Acesso fora das redes liberadas em `web-vuln/apache-status.conf` |
| Site lento durante ataque | Esperado: o web bateu no teto de 1 CPU. Os outros serviços não podem ser afetados (`testes/teste_isolamento.py`) |
