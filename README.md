# Plataforma de Monitoramento para DevOps

Trabalho final da disciplina **Redes de Computadores e Internet** — Instituto Brasileiro de Ensino, Desenvolvimento e Pesquisa (IDP).

Professora: Lorena Borges
Autora: Bianca de Araújo Santana

## Sobre o projeto

Plataforma web que monitora serviços de rede (servidor web, banco de dados, DNS e SMTP), exibe dashboards com métricas de disponibilidade e desempenho, envia alertas por e-mail em três níveis (verde, amarelo e vermelho) e detecta eventos de segurança, como picos de tráfego, tentativas de brute-force, alterações de configuração e vulnerabilidades conhecidas.

## Estrutura do repositório

```
plataforma/      Código que roda na VM da plataforma
  coletor/       Telemetria: coleta de métricas de cada serviço
  api/           Backend de ingestão e armazenamento das métricas
  alertas/       Regras de alerta e notificação por e-mail
  seguranca/     Monitoramentos de segurança
  frontend/      Dashboards (visão consolidada e por serviço)
servicos/        Configurações dos serviços monitorados
  banco/         Banco de dados
  web-vuln/      Aplicação web vulnerável (PHP)
  dns/           Servidor DNS
  smtp/          Servidor de e-mail (Postfix)
docs/            Documentação
  runbooks/      Procedimentos de rotina
  playbooks/     Resposta a incidentes
testes/          Roteiros e evidências de testes
relatorio/       Documento final (PDF, ABNT)
```

## Como executar

Ver `docs/guia-instalacao.md` (em construção).

## Status

Em desenvolvimento. O acompanhamento das entregas está em `CHECKLIST.md`.
