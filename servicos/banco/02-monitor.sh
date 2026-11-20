#!/bin/bash
# Cria o usuario "monitor" (so leitura) que a plataforma usa para medir o banco.
# Roda sozinho na primeira subida do container db (pasta /docker-entrypoint-initdb.d).
# A senha vem do servicos/.env (MONITOR_DB_SENHA), nunca do codigo.
# Sem "set -u": o entrypoint do MySQL pode rodar este arquivo com "source" e herdaria a opcao.
# Se a senha nao foi definida, o ":?" para a subida do container com a mensagem abaixo.
: "${MONITOR_DB_SENHA:?defina MONITOR_DB_SENHA no servicos/.env}"

if ! mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY '${MONITOR_DB_SENHA}';
-- SELECT: ler tabelas e tamanho do banco; PROCESS: ver conexoes ativas (SHOW PROCESSLIST)
GRANT SELECT ON cadastro_db.* TO 'monitor'@'%';
GRANT PROCESS ON *.* TO 'monitor'@'%';
FLUSH PRIVILEGES;
SQL
then
    echo "02-monitor.sh: ERRO ao criar o usuario monitor (veja a mensagem do mysql acima)" >&2
    exit 1
fi
echo "02-monitor.sh: usuario monitor criado (so leitura)"
