<?php
session_start(); // <<<--- Mantenha esta linha como a primeiríssima do arquivo

// Conexão com o banco de dados (variáveis de ambiente, ver ../db.php)
require '../db_connect.php';
// Registro de cada tentativa em /var/log/app/login.log (usado para detectar força bruta)
require __DIR__ . '/registro_login.php';

// Coleta os dados do POST
$email = $_POST['email'] ?? '';
$senha = $_POST['senha'] ?? '';

// Prepara a consulta SQL para evitar injeção de SQL
$sql = "SELECT id, nome_completo, email, telefone, senha FROM usuarios WHERE email = ?"; // <<<--- Adicionei 'id' aqui
$stmt = $conn->prepare($sql);
if (!$stmt) {
    echo "<script>alert('Erro na preparação da consulta SQL: " . addslashes($conn->error) . "'); 
    window.history.back();</script>";
    exit;
}

$stmt->bind_param("s", $email); // 's' indica que o parâmetro é uma string
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    $row = $result->fetch_assoc();
    // Verifica a senha usando password_verify
    if (password_verify($senha, $row['senha'])) {
        // Autenticação bem-sucedida
        registrar_tentativa($email, true);

        // --- AJUSTE CRUCIAL AQUI ---
        $_SESSION['user_id'] = $row['id']; // Armazena o ID do usuário na sessão
        // --- FIM DO AJUSTE CRUCIAL ---

        $_SESSION['user'] = [
            'name' => $row['nome_completo'],
            'email' => $row['email'],
            'phone' => $row['telefone']
        ];
        $_SESSION['usuario_logado'] = true;

        // Criar e configurar o cookie de token de sessão (expira em 30 dias)
        // Nota: Este cookie 'user_token' é um exemplo e sua lógica de validação
        // em outros scripts para "lembrar-me" pode precisar ser ajustada
        // para buscar o usuário pelo token se você o estiver usando para isso.
        $token = bin2hex(random_bytes(64));
        setcookie('user_token', $token, time() + (86400 * 30), "/"); // Expira em 30 dias

        // Redireciona para suaconta.php
        header("Location: suaconta.php");
        exit(); // Sempre chame exit() após um header("Location")
    } else {
        // Senha incorreta
        registrar_tentativa($email, false);
        echo "<script>alert('Senha incorreta.'); window.history.back();</script>";
    }
} else {
    // Email não encontrado
    registrar_tentativa($email, false);
    echo "<script>alert('Email não encontrado.'); window.history.back();</script>";
}

// Fecha o statement e a conexão com o banco de dados
$stmt->close();
$conn->close();
?>