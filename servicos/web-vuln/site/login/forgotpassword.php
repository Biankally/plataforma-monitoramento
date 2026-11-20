<?php
require '../db_connect.php';
require '../vendor/autoload.php'; // Carrega o PHPMailer

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];

    // Inicia a saída HTML para garantir que o SweetAlert2 possa ser carregado
    echo '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Processando...</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css"></head><body>';
    echo '<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.all.min.js"></script>';

    // Verifica se o email existe
    $stmt = $conn->prepare("SELECT id, email FROM usuarios WHERE email = ?");
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows === 0) {
        echo "<script>";
        echo "document.addEventListener('DOMContentLoaded', function() {";
        echo "Swal.fire({
                icon: 'error',
                title: 'E-mail não encontrado!',
                text: 'O e-mail digitado não está cadastrado.',
                confirmButtonText: 'OK'
            }).then(() => {
                window.location.href='forgotpass.html';
            });";
        echo "});";
        echo "</script>";
        echo '</body></html>';
        exit();
    }

    $user = $result->fetch_assoc();
    
    // Gera um token seguro
    $token = bin2hex(random_bytes(32));
    $expiry = date("Y-m-d H:i:s", time() + 3600); // Expira em 1 hora

    // Armazena o token no banco de dados
    $stmt = $conn->prepare("UPDATE usuarios SET reset_token = ?, reset_token_expiry = ? WHERE id = ?");
    $stmt->bind_param("ssi", $token, $expiry, $user['id']);
    $stmt->execute();

    // Configura o PHPMailer
    $mail = new PHPMailer(true);

try {
    
    require '../login/config/mail_config.php'; 

    // Configurações do servidor SMTP
    $mail->isSMTP();
    $mail->Host = MAIL_HOST;
    $mail->Port = MAIL_PORT;
    // No laboratório o Postfix aceita sem usuário/senha; autenticação e TLS só se configurados no .env
    $mail->SMTPAuth = MAIL_USERNAME !== '';
    $mail->Username = MAIL_USERNAME;
    $mail->Password = MAIL_PASSWORD;
    $mail->SMTPSecure = MAIL_TLS ? PHPMailer::ENCRYPTION_STARTTLS : '';
    $mail->SMTPAutoTLS = MAIL_TLS;
    
    $mail->CharSet = 'UTF-8';

    // Remetente e destinatário
    $mail->setFrom(MAIL_FROM, 'Receitas Práticas');
    $mail->addAddress($email);

    // Conteúdo do e-mail
    $mail->isHTML(true);
    $mail->Subject = 'Redefinição de Senha - Receitas Práticas'; 
    $resetLink = "http://" . $_SERVER['HTTP_HOST'] . "/receitas_práticas/login/resetpassword.php?token=$token";
    
    // Conteúdo HTML do e-mail com estilos inline e um botão
    $mail->Body = '
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Redefinição de Senha</title>
        <style>
            /* Estilos para o corpo do e-mail */
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            h2 {
                color: #dc3545; /* Vermelho */
                text-align: center;
                margin-bottom: 25px;
            }
            p {
                margin-bottom: 15px;
            }
            /* A cor do texto do botão será forçada inline no link */
            .button {
                display: inline-block;
                background-color: #dc3545; /* Vermelho */
                padding: 12px 25px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                text-align: center;
                margin-top: 20px;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                font-size: 0.8em;
                color: #777777;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Redefinição de Senha</h2>
            <p>Olá,</p>
            <p>Recebemos uma solicitação para redefinir a senha da sua conta no Receitas Práticas.</p>
            <p>Para redefinir sua senha, clique no botão abaixo:</p>
            <p style="text-align: center;">
                <!-- AQUI ESTÁ A MUDANÇA: style="color: #ffffff;" adicionado diretamente no link -->
                <a href="' . $resetLink . '" class="button" style="color: #ffffff;">Redefinir Senha</a>
            </p>
            <p>Se o botão não funcionar, você pode copiar e colar o seguinte link em seu navegador:</p>
            <p><a href="' . $resetLink . '">' . $resetLink . '</a></p>
            <p>Este link é válido por 1 hora.</p>
            <p>Se você não solicitou esta redefinição de senha, por favor, ignore este e-mail.</p>
            <div class="footer">
                <p>Atenciosamente,<br>Equipe Receitas Práticas</p>
            </div>
        </div>
    </body>
    </html>';

    $mail->AltBody = "Para redefinir sua senha, copie e cole o seguinte link em seu navegador: $resetLink (link válido por 1 hora)";

    if($mail->send()) {
        echo "<script>";
        echo "document.addEventListener('DOMContentLoaded', function() {";
        echo "Swal.fire({
                icon: 'success',
                title: 'E-mail enviado!',
                text: 'Verifique sua caixa de entrada e a pasta de spam.',
                confirmButtonText: 'OK'
            }).then(() => {
                window.location.href='../login/suaconta.php';
            });";
        echo "});";
        echo "</script>";
    } else {
        throw new Exception("Falha no envio");
    }

} catch (Exception $e) {
    error_log("Erro no PHPMailer: " . $e->getMessage() . " - " . $mail->ErrorInfo);
    
    echo "<script>";
    echo "document.addEventListener('DOMContentLoaded', function() {";
    echo "Swal.fire({
            icon: 'error',
            title: 'Erro no envio!',
            text: 'Ocorreu um problema ao enviar o e-mail. Por favor, tente novamente mais tarde.',
            confirmButtonText: 'Entendi'
        }).then(() => {
            window.location.href='forgotpass.html';
        });";
    echo "});";
    echo "</script>";
}
    echo '</body></html>';
} else {
    header("Location: forgotpass.html");
    exit();
}
?>
