# Playbooks de alerta

Um playbook por tipo de alerta. Cada um tem **Sintoma** (o que disparou e o que significa), **Diagnóstico** (o que olhar,
em ordem) e **Ação** (o que fazer). Os comandos assumem a raiz do repositório e o `docker-compose.yml` em `servicos/`;
abreviação usada: `dc` = `docker compose -f servicos/docker-compose.yml`.

| Alerta | Métricas | Playbook |
| --- | --- | --- |
| Serviço fora do ar | `web.disponivel`, `db.disponivel`, `dns.disponivel`, `smtp.disponivel` | [servico-indisponivel.md](servico-indisponivel.md) |
| Latência alta | `web.latencia_ms`, `web.latencia_p95_ms`, `db.latencia_ms`, `dns.latencia_ms`, `smtp.latencia_ms` | [latencia-alta.md](latencia-alta.md) |
| Erros HTTP | `web.taxa_erro_4xx_pct`, `web.taxa_erro_5xx_pct`, `web.conexoes_ativas` | [erros-http.md](erros-http.md) |
| Banco: conexões e consultas | `db.uso_conexoes_pct`, `db.conexoes_executando`, `db.conexoes_abortadas`, `db.slow_queries_min`, `db.rollbacks_s`, `db.qps` | [banco-conexoes-e-consultas.md](banco-conexoes-e-consultas.md) |
| Banco: crescimento | `db.tamanho_mb`, `db.crescimento_mb_dia` | [banco-crescimento.md](banco-crescimento.md) |
| DNS: erros e volume | `dns.taxa_erro_pct`, `dns.qps` | [dns-erros-e-volume.md](dns-erros-e-volume.md) |
| SMTP: fila e entrega | `smtp.taxa_entrega_pct`, `smtp.fila`, `smtp.latencia_envio_s`, `smtp.rejeicoes`, `smtp.timeouts`, `smtp.taxa_erro_pct`, `smtp.emails_min` | [smtp-fila-e-entrega.md](smtp-fila-e-entrega.md) |
| Recursos da máquina | `host.cpu_pct`, `host.mem_pct`, `host.disco_io_kbs`, `host.disco_latencia_ms`, `db.cpu_pct`, `db.mem_pct` | [host-recursos.md](host-recursos.md) |
| Segurança: DDoS | evento `TRAFEGO` (`web.rps`, `dns.qps`) | [seguranca-ddos.md](seguranca-ddos.md) |
| Segurança: força bruta | evento `AUTENTICACAO` | [seguranca-forca-bruta.md](seguranca-forca-bruta.md) |
| Segurança: configuração alterada | evento `CONFIGURACAO` | [seguranca-configuracao-alterada.md](seguranca-configuracao-alterada.md) |
| Segurança: vulnerabilidade conhecida | evento `VULNERABILIDADE` | [seguranca-vulnerabilidade.md](seguranca-vulnerabilidade.md) |

Níveis: **ATENÇÃO** = vale olhar logo; **CRÍTICO** = usuário já é afetado ou o risco é imediato. Os limites exatos estão em
`config/regras.toml` e na seção 5 de `docs/arquitetura.md`. Depois de resolver, o alerta volta a OK sozinho quando a
métrica ficar 3 amostras seguidas dentro do limite (45 s com ciclo de 15 s).

Os nomes de container (`web`, `db`, `dns`, `smtp`) são os do `servicos/docker-compose.yml`.
