# Segurança: arquivo de configuração alterado

Evento `CONFIGURACAO` em `GET /api/seguranca` (`origem` = caminho do arquivo, sempre **CRÍTICO**).

## Sintoma
- O hash (SHA-256) de um arquivo vigiado pelo agente é diferente da **linha de base**. O detalhe mostra os 12 primeiros
  caracteres do hash atual e do hash da linha de base. O serviço do evento é inferido do caminho (`/etc/postfix/main.cf` → smtp).
- Avisa uma vez por mudança de hash. Só vale para arquivos que já estavam na linha de base: arquivo novo ou ausente não
  gera evento.
- Sem linha de base não há evento.

## Diagnóstico
1. A mudança foi legítima? Pergunte ao grupo e confira `git log` / `docs/LOG.md` do período.
2. O que mudou? Compare com a versão do repositório: `dc exec <servico> cat <arquivo> | diff - servicos/<servico>/<arquivo>`
   (por exemplo `servicos/smtp/main.cf`, `servicos/dns/unbound.conf`).
3. Quem e quando? `dc exec <servico> ls -l --time-style=full-iso <arquivo>` e os logs do serviço.
4. O serviço continua funcionando? Veja os alertas de disponibilidade do serviço afetado.

## Ação
- **Mudança indevida:** restaure o arquivo do repositório, reinicie o serviço (`dc restart <servico>`), confirme que a
  disponibilidade segue OK e registre o incidente em `docs/LOG.md` (possível invasão no relatório).
- **Mudança legítima:** aceite o novo estado como linha de base, com o sistema limpo e depois de uma leitura do agente:
  `curl -X POST -H "X-Token: $MONITOR_TOKEN" http://127.0.0.1:5000/api/seguranca/linha-base`
  (a linha de base substitui os hashes de **todos** os arquivos; confira antes se mais nada mudou).
- Se foi teste do laboratório (P1 simula alteração de configuração), restaure e refaça a linha de base.
