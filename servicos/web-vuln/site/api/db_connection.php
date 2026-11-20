<?php
// Conexao para as rotas da pasta api/ (respondem JSON).
require_once __DIR__ . '/../db.php';

try {
    $conn = abrir_conexao();
} catch (mysqli_sql_exception $e) {
    error_log('api/db_connection: falha na conexao com o banco: ' . $e->getMessage());
    http_response_code(503);
    header('Content-Type: application/json');
    die(json_encode(['success' => false, 'message' => 'Erro de conexão com o banco de dados.']));
}
