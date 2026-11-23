# Runbook — agente de telemetria

- **Programa:** `servicos/agente/agente.py` (roda no Ubuntu do WSL, fora dos containers) · **Porta:** `127.0.0.1:9101`
- **Rota:** `GET /metrics` com o cabeçalho `X-Token: <MONITOR_AGENTE_TOKEN do .env>`. Sem token, a resposta é `401`.
- **Formato:** as mesmas chaves de `tests/falsos/agente_exemplo.json`

| Parte do JSON | De onde vem | Tipo de valor |
| --- | --- | --- |
| `apache` | `http://127.0.0.1:8080/server-status?auto` | contador acumulado |
| `log_web` | `servicos/logs/web/acesso.log` | desde a leitura anterior |
| `unbound` | `docker exec ... unbound-control stats_noreset` | contador acumulado |
| `postfix.fila` | `docker exec ... postqueue -j` | foto do momento |
| `postfix` (resto) | `docker logs` do smtp | desde a leitura anterior |
| `auth` | `servicos/logs/web/login.log` | desde a leitura anterior |
| `containers` | `docker stats --no-stream` | foto do momento |
| `host` | `/proc` do Linux | foto do momento (CPU e disco: média desde a leitura anterior) |
| `hashes` | `docker exec ... sha256sum` dos arquivos de configuração | foto do momento |

- **Campo `null`:** a fonte não respondeu (container parado, por exemplo). O motivo aparece no terminal do agente.
- **"Desde a leitura anterior":** só o coletor deve ler o `/metrics`. Uma leitura manual "rouba" as linhas da janela seguinte.

## Operação
| Ação | Comando (na raiz do projeto, com `.venv` ativo) |
| --- | --- |
| Iniciar | `python servicos/agente/agente.py` |
| Parar | `Ctrl+C` no terminal do agente |
| Reiniciar | `Ctrl+C` e iniciar de novo (os contadores das janelas recomeçam) |
| Verificar | `curl -s -H "X-Token: $(grep ^MONITOR_AGENTE_TOKEN .env \| cut -d= -f2)" http://127.0.0.1:9101/metrics \| python -m json.tool \| head -20` |

## Problemas
| Sintoma | O que fazer |
| --- | --- |
| `MONITOR_AGENTE_TOKEN vazio` | Falta a linha no `.env` da raiz (ver `.env.exemplo`) |
| `Address already in use` | Já existe um agente rodando: feche o outro terminal ou use `--porta` |
| `unbound` ou `postfix` todo `null` | Container parado ou nome diferente de `monitoramento-<serviço>-1`: `docker compose ps` |
| `auth` sempre vazio | O site não está gravando: veja o runbook do web (`login.log`) |
