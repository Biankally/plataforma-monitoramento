# Plataforma de Monitoramento para DevOps

Trabalho final da disciplina **Redes de Computadores e Internet** — Instituto Brasileiro de Ensino,
Desenvolvimento e Pesquisa (IDP). Professora: Lorena Borges.

## O que é
Uma plataforma que vigia 4 serviços de rede (servidor web, banco de dados, DNS e SMTP), mostra
dashboards com as métricas, envia alertas por e-mail em três níveis (verde, amarelo e vermelho) e detecta
eventos de segurança (picos de tráfego, tentativas de senha, alteração de configuração e vulnerabilidades).

## Como rodar
Primeira vez: siga o [`COMECE_AQUI.md`](COMECE_AQUI.md). Depois:

```bash
source .venv/bin/activate
python -m plataforma.api                    # API na porta 5000
python -m plataforma.infra.coletor          # coleta a cada 15 s
streamlit run plataforma/dashboard/app.py   # dashboard na porta 8501
pytest                                      # testes
```

## Estrutura

```
plataforma/
  contrato/    camada 0: nomes das métricas, formato dos dados, configuração
  dominio/     camada 1: regras de alerta e cálculos (Python puro)
  infra/       camada 2: coletor, sondas, banco SQLite, e-mail
  api/         camada 3: API Flask
  dashboard/   camada 4: dashboard Streamlit
servicos/      VM-S: containers vigiados (web-vuln, banco, dns, smtp) e agente
config/        endereços dos serviços e limites de alerta
tests/         testes automáticos (camadas, termômetro, unitários)
testes/        roteiro e evidências dos testes nas VMs
docs/          arquitetura, guia de instalação, runbooks, playbooks, pedidos de IA
relatorio/     documento final em PDF (ABNT)
```

Regras para quem usa IA: [`AGENTS.md`](AGENTS.md). Entregas: [`CHECKLIST.md`](CHECKLIST.md).
