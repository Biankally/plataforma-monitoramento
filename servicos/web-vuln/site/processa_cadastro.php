<?php
require 'conexao.php'; // Inclui o arquivo de conexão

// Recebe dados do formulário HTML
$nome = $_POST['nome'];
$email = $_POST['email'];

try {
    // Prepara e executa a query SQL
    $stmt = $conn->prepare("INSERT INTO usuarios (nome, email) VALUES (?, ?)");
    $stmt->bind_param("ss", $nome, $email);
    $stmt->execute();
    
    echo "Cadastro realizado com sucesso!";
} catch (Exception $e) {
    echo "Erro: " . $e->getMessage();
}
?>