# Pedido P1 — Infraestrutura e Segurança (branches `a/...`)

Cole este arquivo na IA junto com o `AGENTS.md`. Faça uma tarefa por vez, na ordem.

## Contexto
A VM-S roda os 4 serviços vigiados em containers (Docker Compose), cada um com limite de CPU, memória e
processos. Regra da professora: um ataque a um serviço **não pode derrubar os outros**. O agente de telemetria
roda na VM-S e entrega estatísticas internas para a plataforma.

## Tarefas
| # | Arquivo(s) | O que fazer | Pronto quando | Prazo |
| --- | --- | --- | --- | --- |
| 1 | `servicos/docker-compose.yml` | Containers `web` (Apache + PHP), `db` (MySQL 8.0), `dns` (Unbound), `smtp` (Postfix), cada um com `cpus`, `mem_limit` e `pids_limit`. Logs em volumes compartilhados com o agente | `docker compose up -d` sobe os 4; `docker stats` mostra os limites | 20/11 22h |
| 2 | `servicos/web-vuln/` | Site Receitas Práticas adaptado: conexão via variáveis de ambiente (host `db`, usuário próprio, sem `root`); `login.php` grava cada tentativa (data, IP, e-mail, sucesso) em `/var/log/app/login.log`, uma linha JSON; corrigir o `logout.php` | Login certo e errado geram 1 linha cada no log; nenhuma senha no código | 21/11 12h |
| 3 | `servicos/banco/init.sql` | `cadastro_db` com `usuarios`, `recuperacao_senha` e `favorites` (`id`, `user_id`, `recipe_url`, `recipe_title`, `recipe_image`); usuário `monitor` só leitura; dados **inventados** | Container `db` novo já sobe com as 3 tabelas | 21/11 12h |
| 4 | `servicos/dns/unbound.conf` | Zona local `lab.local` com `teste.lab.local`; `extended-statistics: yes`; `remote-control` em 127.0.0.1 | `dig @IP teste.lab.local` responde | 21/11 12h |
| 5 | `servicos/smtp/` | Postfix aceitando e-mail na porta 25 (rede interna) | `postqueue -j` funciona; e-mail de teste vai para o log | 21/11 20h |
| 6 | `servicos/agente/agente.py` + `tests/test_agente.py` | Servidor HTTP (biblioteca padrão `http.server`) na porta 9101: `GET /metrics` com `X-Token` devolve JSON **com as mesmas chaves** de `tests/falsos/agente_exemplo.json`; lê logs só das linhas novas (guarda a posição); calcula SHA-256 dos arquivos de configuração | Teste compara as chaves com o exemplo; sem token = 401; sabotagem: log rotacionado não quebra | 22/11 12h |
| 7 | `testes/ataque_ddos.py`, `testes/ataque_brute_force.py`, `testes/teste_isolamento.py` | Scripts de ataque rodados **do WSL**, só contra o container `web` | Durante o ataque, `db`, `dns` e `smtp` continuam OK no dashboard | 22/11 20h |
| 8 | `docs/guia-instalacao.md`, `docs/runbooks/*.md` | Guia do zero (VMs, rede host-only, Docker, `.env`) e um runbook por serviço (iniciar, parar, verificar, reiniciar) | Outra pessoa instala seguindo só o guia | 23/11 20h |

## Interfaces que você entrega (não mude sem combinar)
- Endereços e portas: os de `config/servicos.toml` (WSL + Docker Desktop, só em 127.0.0.1: web 8080, db 3307, dns 1053, smtp 2525, agente 9101).
- JSON do agente: exatamente as chaves de `tests/falsos/agente_exemplo.json`.
- Log de login: uma linha JSON por tentativa: `{"ts": 1795036790, "origem": "IP", "usuario": "email", "sucesso": false}`.
