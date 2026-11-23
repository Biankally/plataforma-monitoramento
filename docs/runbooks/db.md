# Runbook — db (MySQL 8.0)

- **Container:** `monitoramento-db-1` · **Porta:** `127.0.0.1:3307` · **Limites:** 1 CPU, 1 GB, 300 processos
- **Banco:** `cadastro_db` (tabelas `usuarios`, `recuperacao_senha`, `favorites`)
- **Usuários:** `root` (só administração), `site` (o site), `monitor` (só leitura, para a plataforma). Senhas em `servicos/.env`.
- **Criação:** `servicos/banco/init.sql` e `02-monitor.sh` rodam **só na primeira subida** (volume `db_dados` vazio).

Todos os comandos são rodados dentro de `servicos/`.

| Ação | Comando |
| --- | --- |
| Iniciar | `docker compose up -d db` |
| Parar | `docker compose stop db` |
| Reiniciar | `docker compose restart db` |
| Recriar do zero (**apaga os dados do laboratório**) | `docker compose down -v && docker compose up -d` |
| Estado | `docker compose ps db` |

## Verificar
```bash
docker compose logs --tail 20 db | grep -i "ready for connections"
# entrar como monitor (pede a senha MONITOR_DB_SENHA do servicos/.env):
docker compose exec db mysql -umonitor -p cadastro_db -e "SELECT COUNT(*) FROM usuarios; SHOW GLOBAL STATUS LIKE 'Threads_connected';"
```

## Problemas
| Sintoma | O que fazer |
| --- | --- |
| Tabelas não existem | O volume é antigo: o `init.sql` só roda em volume novo. Recrie do zero |
| `Access denied for user 'monitor'` | `MONITOR_DB_SENHA` mudou depois da criação. Recrie do zero ou altere a senha como root |
| Container reinicia sem parar | `docker compose logs db`; senha com aspas ou `$` no `.env` quebra o script: use só letras e números |
| Porta 3307 ocupada | Outro MySQL rodando; pare ou troque a porta no compose **e** no `config/servicos.toml` |
