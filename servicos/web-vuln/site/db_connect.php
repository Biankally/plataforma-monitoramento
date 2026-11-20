<?php
// Abre a conexao em $conn para as paginas HTML. Se falhar, registra o motivo no log do Apache
// e mostra uma mensagem generica (o motivo real nao vai para o navegador).
require_once __DIR__ . '/db.php';

try {
    $conn = abrir_conexao();
} catch (mysqli_sql_exception $e) {
    error_log('db_connect: falha na conexao com o banco: ' . $e->getMessage());
    http_response_code(503);
    die('Falha na conexão com o banco de dados.');
}
