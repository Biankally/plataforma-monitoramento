# Plataforma de Monitoramento para DevOps

Trabalho final da disciplina **Redes de Computadores e Internet** — Instituto Brasileiro de Ensino,
Desenvolvimento e Pesquisa (IDP). Professora: Lorena Borges.

## O que é
Uma plataforma que vigia 4 serviços de rede (servidor web, banco de dados, DNS e SMTP), mostra
dashboards com as métricas, envia alertas por e-mail em três níveis (verde, amarelo e vermelho) e detecta
eventos de segurança (picos de tráfego, tentativas de senha, alteração de configuração e vulnerabilidades).

## Como rodar
Primeira vez: siga o [`docs/guia-instalacao.md`](docs/guia-instalacao.md) (ou o [`COMECE_AQUI.md`](COMECE_AQUI.md) para só rodar os testes). Depois:

```bash
source .venv/bin/activate
cd servicos && docker compose up -d && cd ..   # os 4 serviços vigiados
python servicos/agente/agente.py               # agente na porta 9101
python -m plataforma.api                       # API na porta 5000
python -m plataforma.infra.coletor             # coleta a cada 15 s
streamlit run plataforma/dashboard/app.py      # dashboard na porta 8501
pytest                                         # testes (MONITOR_INFRA=1 para os de infraestrutura)
```

## Estrutura

```
plataforma/          a plataforma (Python), em camadas
  contrato/          camada 0: nomes das métricas, formato dos dados, configuração
  dominio/           camada 1: regras de alerta e cálculos (Python puro)
  infra/             camada 2: coletor, sondas, cliente do agente, banco SQLite, e-mail
  api/               camada 3: API Flask
  dashboard/         camada 4: dashboard Streamlit
servicos/            o que é vigiado (containers com limite de CPU, memória e processos)
  docker-compose.yml os 4 containers: web, db, dns, smtp
  web-vuln/          site Receitas Práticas (alvo dos ataques) e configuração do Apache
  banco/             criação do banco (init.sql) e do usuário monitor
  dns/  smtp/        configuração do Unbound e do Postfix
  agente/            agente de telemetria (porta 9101)
  logs/              logs do site lidos pelo agente (fora do Git)
config/              endereços dos serviços e limites de alerta
tests/               testes automáticos (pytest)
testes/              scripts de ataque, teste de isolamento e evidências
docs/                LOG, guia de instalação, runbooks, playbooks, pedidos por pessoa
relatorio/           documento final em PDF (ABNT)
```

Regras para quem usa IA: [`AGENTS.md`](AGENTS.md). Entregas: [`CHECKLIST.md`](CHECKLIST.md).
