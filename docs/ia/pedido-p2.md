# Pedido P2 — Telemetria e Backend (branches `b/...`)

Cole este arquivo na IA junto com o `AGENTS.md`. Faça uma tarefa por vez, na ordem.

## Contexto
O esqueleto já roda de ponta a ponta (`tests/test_termometro.py`): Coletor → API → banco → alertas → e-mail.
Hoje as sondas de banco, DNS e SMTP só testam se a porta abre. Sua parte é medir de verdade todas as métricas
do catálogo em `plataforma/contrato/metricas.py` e completar os alertas e a segurança.

## Tarefas
| # | Arquivo(s) | O que fazer | Pronto quando | Prazo |
| --- | --- | --- | --- | --- |
| 1 | `plataforma/infra/sondas.py` + `tests/test_sondas.py` | `sonda_mysql` (PyMySQL: `SELECT 1` + `SHOW GLOBAL STATUS`), `sonda_dns` (dnspython: consulta A a `teste.lab.local`), `sonda_smtp` (smtplib: banner, EHLO, QUIT). Novos `tipo` em `config/servicos.toml` | Cada sonda tem teste com servidor falso e caso de sabotagem (servidor fora do ar = `disponivel` 0) | 21/11 12h |
| 2 | `plataforma/infra/agente_cliente.py` | Lê `GET /metrics` do agente com `X-Token` e devolve o dicionário | Teste com servidor falso servindo `tests/falsos/agente_exemplo.json` | 21/11 20h |
| 3 | `plataforma/dominio/derivadas.py` | Converte o JSON do agente (leitura atual + anterior) em amostras do catálogo: `web.rps`, `web.taxa_erro_*`, `web.latencia_p95_ms`, `dns.qps`, `dns.taxa_erro_pct`, `smtp.*`, `host.*` (usa `dominio/taxas.py`) | Teste com duas leituras de exemplo dá os valores calculados à mão | 21/11 20h |
| 4 | `plataforma/infra/coletor.py` | Juntar sondas + agente num lote só | Termômetro continua verde | 22/11 12h |
| 5 | `config/regras.toml` | Regras de todas as métricas com limite da seção 8 da arquitetura | Teste carrega todas as regras sem erro | 22/11 12h |
| 6 | `plataforma/dominio/seguranca.py` + rotas em `plataforma/api/app.py` | Escore z (DDoS), falhas de login por IP em 60 s (5 = ATENÇÃO, 20 = CRÍTICO), hash diferente da linha de base; grava em `evento_seguranca`; `GET /api/seguranca` e `POST /api/seguranca/linha-base` | Teste de cada regra com caso de sabotagem; e-mail sai pelo notificador | 22/11 20h |
| 7 | `docs/arquitetura.md`, `docs/playbooks/*.md` | Arquitetura final em Markdown e um playbook por tipo de alerta (sintoma, diagnóstico, ação) | Revisado por P3 | 23/11 20h |

## Interfaces (não mude sem combinar)
- Nomes de métrica: só os de `METRICAS` em `plataforma/contrato/metricas.py`. Métrica nova = combinar no grupo.
- Rotas existentes da API e formato das respostas: `GET /api/status`, `/api/metricas`, `/api/alertas`, `/api/saude`.
- Assinaturas de `plataforma/dominio/alertas.py` (`avaliar`, `classificar`, `Regra`, `Estado`).
