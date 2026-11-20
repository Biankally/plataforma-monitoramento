<?php
require '../db_connect.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $token = filter_var($_POST['token'], FILTER_SANITIZE_STRING);
    $email = filter_var($_POST['email'], FILTER_SANITIZE_EMAIL);
    $new_password = $_POST['new_password'];
    $confirm_password = $_POST['confirm_password'];

    if ($new_password !== $confirm_password) {
        echo "<script>alert('As senhas não coincidem.'); window.location.href='resetpass.php?token=" . urlencode($token) . "';</script>";
        exit();
    }

    if (strlen($new_password) < 6) {
        echo "<script>alert('A senha deve ter pelo menos 6 caracteres.'); window.location.href='resetpass.php?token=" . urlencode($token) . "';</script>";
        exit();
    }

    $stmt = $conn->prepare("SELECT id FROM usuarios WHERE email = ? AND reset_token = ? AND reset_token_expiry > NOW()");
    $stmt->bind_param("ss", $email, $token);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows === 0) {
        echo "<script>alert('Token inválido ou expirado. Solicite um novo código.'); window.location.href='forgotpass.html';</script>";
        exit();
    }

    $user = $result->fetch_assoc();
    $hashed_password = password_hash($new_password, PASSWORD_DEFAULT);

    $stmt = $conn->prepare("UPDATE usuarios SET password = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?");
    $stmt->bind_param("si", $hashed_password, $user['id']);
    if ($stmt->execute()) {
        echo "<script>
            Swal.fire({
                icon: 'success',
                title: 'Senha alterada!',
                text: 'Sua senha foi redefinida com sucesso.',
                confirmButtonText: 'OK'
            }).then(() => {
                window.location.href='../login/suaconta.php';
            });
        </script>";
    } else {
        error_log("Erro ao atualizar senha: " . $stmt->error);
        echo "<script>alert('Erro ao redefinir a senha. Tente novamente.'); window.location.href='resetpass.php?token=" . urlencode($token) . "';</script>";
    }
} else {
    header("Location: forgotpass.html");
    exit();
}

$conn->close();
?>