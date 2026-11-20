<?php
// api/get_favorites.php
session_start();
header('Content-Type: application/json');

// Inclui o arquivo de conexão com o banco de dados
require_once '../api/db_connection.php'; // Caminho relativo da pasta 'api' para 'db_connection.php'

// Verifica se o usuário está logado
if (!isset($_SESSION['user_id'])) {
    echo json_encode(['success' => false, 'message' => 'Usuário não logado.']);
    $conn->close(); // Fecha a conexão em caso de erro
    exit;
}

$userId = $_SESSION['user_id'];

// Prepara e executa a consulta para buscar os favoritos do usuário
$stmt = $conn->prepare("SELECT recipe_url, recipe_title, recipe_image FROM favorites WHERE user_id = ?");
$stmt->bind_param("i", $userId); // 'i' indica que user_id é um inteiro
$stmt->execute();
$result = $stmt->get_result(); // Obtém o resultado da consulta

$favorites = [];
// Itera sobre os resultados e armazena em um array
while ($row = $result->fetch_assoc()) {
    $favorites[] = $row;
}

$stmt->close(); // Fecha o statement
$conn->close(); // Fecha a conexão com o banco de dados

echo json_encode(['success' => true, 'favorites' => $favorites]);
?>