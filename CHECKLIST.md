# Checklist de entregas — Plataforma de Monitoramento para DevOps

Cada item indica **onde** a entrega deve estar no repositório. A cada push, conferir e marcar `[x]`.

Legenda: `[ ]` pendente · `[x]` entregue · `(?)` aguardando confirmação da professora

---

## 1. Entregas obrigatórias (enunciado, seção 2)

- [x] Front-end responsivo com dashboard **por serviço** — `plataforma/dashboard/`
- [x] Front-end com **visão consolidada** (todos os serviços) — `plataforma/dashboard/`
- [x] Backend de **ingestão** de métricas — `plataforma/api/app.py`
- [x] **Armazenamento** de métricas — `plataforma/infra/banco.py`
- [x] Regras de alerta — `plataforma/dominio/alertas.py`, `config/regras.toml`
- [x] Canal de notificação por **e-mail** — `plataforma/infra/notificador.py`
- [x] Documentação: **arquitetura** — `docs/arquitetura.md`
- [x] Documentação: **runbooks** — `docs/runbooks/`
- [x] Documentação: **playbooks de incidentes** — `docs/playbooks/`
- [x] Documentação: **guia de instalação** — `docs/guia-instalacao.md`
- [ ] **Testes** de navegação e uso da plataforma — `testes/`
- [ ] Documento final em **PDF (ABNT)** — `relatorio/`
- [ ] Apresentação do dashboard em sala

## 2. Requisitos passados em sala (quadro)

- [ ] Plataforma em **VM própria** (VM-P); serviços em **containers isolados** na VM-S — `docs/arquitetura.md`
- [x] Coleta por **telemetria**: plataforma → serviços — `plataforma/infra/coletor.py`
- [x] Banco de dados: MySQL, SQLite ou PostgreSQL — `servicos/banco/`
- [x] Aplicação **web vulnerável em PHP** (site Receitas Práticas) — `servicos/web-vuln/`
- [x] DNS com **Unbound ou BIND** — `servicos/dns/`
- [x] SMTP com **Postfix** — `servicos/smtp/`
- [x] **Arquitetura** bem documentada (ênfase da professora) — `docs/arquitetura.md`
- [ ] **URL do repositório Git** incluída no documento — `relatorio/`

## 3. Métricas por serviço (enunciado, seção 3)

### 3.1 Web Server (HTTP/HTTPS)
- [x] Disponibilidade (UP/DOWN, ping/HTTP status check)
- [x] Requests por segundo (RPS)
- [x] Latência (ms)
- [x] Taxa de erro (4xx, 5xx) e contagem de códigos de erro
- [x] Número de conexões ativas

### 3.2 Banco de Dados
- [x] Disponibilidade
- [x] QPS (queries por segundo)
- [x] Taxa de erros / rollback / transaction failures
- [x] Número de conexões abertas e pools
- [x] Uso de CPU, memória, I/O e latência de disco
- [x] Tamanho do banco e crescimento (GB/dia)
- [x] Número de slow queries

### 3.3 DNS
- [x] Tempo de resposta de resolução (ms)
- [x] Taxa de erros / failed resolutions
- [x] Queries por segundo
- [x] Disponibilidade do servidor de domínio

### 3.4 SMTP
- [x] Taxa de entrega
- [x] Tamanho da fila de e-mails (queue length / backlog)
- [x] Latência de envio
- [x] Taxa de erros (rejeições, timeouts)
- [x] Volume de e-mails por minuto/hora

## 4. Níveis de alerta (enunciado, seção 4)

- [x] Nível 1 — **Verde** (OK): estado normal
- [x] Nível 2 — **Amarelo** (Atenção): degradação + notificação por e-mail
- [x] Nível 3 — **Vermelho** (Crítico): degradado/indisponível + notificação **imediata** por e-mail
- [x] Limites (thresholds) de cada métrica documentados — `docs/arquitetura.md`

## 5. Segurança e monitoramentos extras (enunciado, seção 5)

- [x] Detecção de **anomalias de tráfego** (picos, indicadores de DDoS) — `plataforma/dominio/seguranca.py`
- [x] Detecção de **falhas de autenticação** (logins falhos por conta/IP, brute-force) — `plataforma/dominio/seguranca.py`
- [x] Alerta de **alteração de arquivos de configuração** — `plataforma/dominio/seguranca.py`
- [x] Monitoramento de **vulnerabilidade conhecida por serviço** — `plataforma/dominio/vulnerabilidades.py`, `config/vulnerabilidades.toml`

## 6. Testes (evidências para o documento)

- [ ] Navegação pelo dashboard (consolidado + cada serviço), em PC e celular
- [ ] Simulação de falha de cada serviço → alerta vermelho + e-mail recebido
- [ ] Simulação de degradação → alerta amarelo + e-mail recebido
- [ ] Simulação de pico de tráfego → detecção de anomalia
- [ ] Simulação de brute-force → detecção de falhas de autenticação
- [ ] Alteração de arquivo de configuração → alerta disparado
- [ ] Varredura de vulnerabilidades executada e registrada
- [ ] Prints legíveis, com destaque no que interessa

## 7. Documento ABNT

Normas: NBR 14724:2024 (estrutura), NBR 6023:2018 (referências), NBR 10520:2023 (citações).

- [ ] Capa
- [ ] Folha de rosto
- [ ] Resumo e palavras-chave
- [ ] Listas de ilustrações e de abreviaturas/siglas
- [ ] Sumário
- [ ] Introdução (contexto, objetivos, justificativa)
- [ ] Referencial teórico (monitoramento, quatro sinais de ouro, protocolos HTTP/DNS/SMTP, resposta a incidentes)
- [ ] Arquitetura da solução (diagrama + explicação)
- [ ] Implementação (cada componente)
- [ ] Testes e resultados
- [ ] Conclusão
- [ ] Referências (NBR 6023)
- [ ] Apêndices (runbooks, playbooks, guia de instalação)
- [ ] URL do repositório Git
- [ ] Formatação conferida contra a NBR 14724:2024 (fonte, margens, espaçamento, paginação)

## 8. Segurança do próprio repositório

- [x] Arquivo `.env` (senhas, ex.: SMTP) listado no `.gitignore` e **nunca** enviado
- [x] Nenhuma senha, token ou chave privada em nenhum arquivo do repositório
- [x] README explicando o projeto e como rodar

## 9. Garantia de execução (regras do projeto)

- [x] Teste de camadas (`tests/test_camadas.py`) com sabotagem
- [x] Teste termômetro de ponta a ponta (`tests/test_termometro.py`) com sabotagem
- [ ] GitHub Actions verde em todo push
- [x] Teste de isolamento: ataque ao `web` sem derrubar `db`, `dns` e `smtp` (regra da professora)
- [ ] Ensaio final: clonar numa pasta nova, instalar só pelo README e rodar a demonstração

## 10. Decisões com a professora (resolvidas)

- [x] Infraestrutura livre (VMs ou containers), desde que um ataque não derrube outros serviços
- [x] Grupo em trio permitido
- [x] Repositório privado com a professora como colaboradora (falta o usuário dela no GitHub)
- [ ] Aplicação vulnerável: usar o site do grupo (avisar a professora)
