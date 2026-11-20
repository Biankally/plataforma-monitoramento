<?php
// Conexao unica com o MySQL. Tudo vem de variaveis de ambiente definidas no docker-compose.yml
// (que por sua vez le o servicos/.env). Nenhuma senha fica escrita no codigo.
function abrir_conexao(): mysqli
{
    mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT); // erro vira excecao (nada escondido)
    $conexao = new mysqli(
        getenv('DB_HOST') ?: 'db',
        getenv('DB_USER') ?: '',
        getenv('DB_PASS') ?: '',
        getenv('DB_NAME') ?: 'cadastro_db'
    );
    $conexao->set_charset('utf8mb4');
    return $conexao;
}
