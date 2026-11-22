# Banco de dados: tamanho e crescimento

Métricas: `db.tamanho_mb`, `db.crescimento_mb_dia`.

## Sintoma
- `db.tamanho_mb` (dados + índices dos bancos de usuário): ATENÇÃO > 2000 MB, CRÍTICO > 4000 MB.
- `db.crescimento_mb_dia` é a **projeção para 24 h** do crescimento medido contra a leitura mais antiga dos últimos
  10 min (precisa de pelo menos 60 s de histórico): ATENÇÃO > 500, CRÍTICO > 2000 MB/dia, e só dispara depois de 3
  amostras seguidas.
- Crescimento rápido sem aumento de uso legítimo é sinal de cadastro em massa (bot), log de aplicação gravado no banco ou
  carga de ataque.

## Diagnóstico
1. Quais tabelas crescem? `dc exec db mysql -uroot -p -e "SELECT table_schema, table_name, ROUND((data_length+index_length)/1048576,1) AS mb FROM information_schema.tables ORDER BY mb DESC LIMIT 10"`.
2. Cresceu de repente? Compare com `web.rps` e com os cadastros (`usuarios` em `init.sql`: muitas linhas novas = bot).
3. Espaço do volume: `docker system df -v` e `host.disco_*` (ver `host-recursos.md`).
4. Há dados temporários? Verifique `recuperacao_senha` (tokens vencidos acumulam).

## Ação
- Cadastro em massa: identifique a origem (`access.log`), bloqueie e limpe as linhas inválidas com o grupo.
- Dados vencidos: remova os tokens expirados de `recuperacao_senha`.
- Se o volume vai encher: faça backup (`mysqldump`) antes de qualquer limpeza e avise o grupo.
- Se o crescimento é legítimo (carga de dados do teste), registre no `docs/LOG.md` e ajuste os limites em `config/regras.toml`.
