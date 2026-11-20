<?php
// api/toggle_favorite.php
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
$recipeUrl = $_POST['url'] ?? ''; // Obtém a URL da receita via POST
$recipeTitle = $_POST['title'] ?? ''; // Obtém o título da receita via POST
$recipeImage = $_POST['image'] ?? ''; // Obtém a imagem da receita via POST

// Validação básica
if (empty($recipeUrl)) {
    echo json_encode(['success' => false, 'message' => 'URL da receita é obrigatória.']);
    $conn->close();
    exit;
}

// Limpa o "./" das URLs e imagens para consistência no banco de dados, se existirem
if (strpos($recipeUrl, './') === 0) {
    $recipeUrl = substr($recipeUrl, 2);
}
if (strpos($recipeImage, './') === 0) {
    $recipeImage = substr($recipeImage, 2);
}

// Verifica se a receita já é favorita para este usuário
$stmt = $conn->prepare("SELECT id FROM favorites WHERE user_id = ? AND recipe_url = ?");
$stmt->bind_param("is", $userId, $recipeUrl);
$stmt->execute();
$result = $stmt->get_result();

$message = '';
$isFavorite = false;

if ($result->num_rows > 0) {
    // Se já é favorito, remove do banco de dados
    $stmt->close();
    $stmt = $conn->prepare("DELETE FROM favorites WHERE user_id = ? AND recipe_url = ?");
    $stmt->bind_param("is", $userId, $recipeUrl);
    $stmt->execute();
    $message = 'removido';
    $isFavorite = false;
} else {
    // Se não é favorito, adiciona ao banco de dados
    $stmt->close();
    $stmt = $conn->prepare("INSERT INTO favorites (user_id, recipe_url, recipe_title, recipe_image) VALUES (?, ?, ?, ?)");
    $stmt->bind_param("isss", $userId, $recipeUrl, $recipeTitle, $recipeImage); // 'isss' para int, string, string, string
    $stmt->execute();
    $message = 'adicionado';
    $isFavorite = true;
}

$stmt->close();
$conn->close();

echo json_encode(['success' => true, 'message' => "Receita {$message} dos favoritos.", 'isFavorite' => $isFavorite]);
?>