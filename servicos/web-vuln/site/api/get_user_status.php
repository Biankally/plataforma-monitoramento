<?php

session_start(); // Inicia a sessão PHP para acessar variáveis de sessão
header('Content-Type: application/json'); // Define o cabeçalho para indicar que a resposta é JSON

// Verifica se o 'user_id' está definido na sessão (indicando que o usuário está logado)
if (isset($_SESSION['user_id'])) { // IMPORTANTE: Certifique-se que seu script de login define $_SESSION['user_id']
    echo json_encode(['loggedIn' => true, 'userId' => $_SESSION['user_id']]);
} else {
    echo json_encode(['loggedIn' => false]);
}
?>