<?php
// ATENÇÃO: Estas linhas são para depuração e devem ser removidas em produção.
error_reporting(E_ALL);
ini_set('display_errors', 1);

require '../db_connect.php'; // Certifique-se de que este caminho está correto para db_connect.php

error_log("resetpassword.php acessado. Método: " . $_SERVER['REQUEST_METHOD']);

// --- Lógica para REQUISIÇÕES POST (quando o formulário é enviado via JavaScript) ---
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Define o cabeçalho para JSON APENAS para requisições POST
    header('Content-Type: application/json'); 

    error_log("resetpassword.php: Entrou no bloco POST.");
    error_log("resetpassword.php: Dados POST recebidos: " . print_r($_POST, true));

    // Coleta os dados do POST (vindo do seu resetpass.js)
    $emailConfirm = $_POST['email_confirm'] ?? '';
    $newPassword = $_POST['password'] ?? '';
    $confirmPassword = $_POST['confirm_password'] ?? '';
    $token = $_POST['token'] ?? ''; // O token deve vir do campo hidden do formulário via POST

    // Validações básicas no servidor
    if (empty($emailConfirm) || empty($newPassword) || empty($confirmPassword) || empty($token)) {
        error_log("resetpassword.php: Erro de validação: campos vazios.");
        echo json_encode(["status" => "error", "message" => "Todos os campos são obrigatórios."]);
        exit();
    }

    if ($newPassword !== $confirmPassword) {
        error_log("resetpassword.php: Erro de validação: senhas não coincidem.");
        echo json_encode(["status" => "error", "message" => "As senhas não coincidem."]);
        exit();
    }

    if (strlen($newPassword) < 6) { // Exemplo: senha mínima de 6 caracteres
        error_log("resetpassword.php: Erro de validação: senha muito curta.");
        echo json_encode(["status" => "error", "message" => "A nova senha deve ter pelo menos 6 caracteres."]);
        exit();
    }

    // Verifica se o token é válido e não expirou, e se o email corresponde
    $stmt = $conn->prepare("SELECT id, email FROM usuarios WHERE reset_token = ? AND reset_token_expiry > NOW() AND email = ?");
    
    if ($stmt === false) {
        error_log("resetpassword.php: Erro na preparação da query SQL (SELECT token): " . $conn->error);
        echo json_encode(["status" => "error", "message" => "Erro interno do servidor ao verificar token."]);
        exit();
    }
    
    $stmt->bind_param("ss", $token, $emailConfirm);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows === 0) {
        error_log("resetpassword.php: Erro: Token inválido, expirado ou email incorreto no DB.");
        echo json_encode(["status" => "error", "message" => "Token inválido ou expirado, ou email incorreto."]);
        exit();
    }
    
    $user = $result->fetch_assoc();
    $userId = $user['id'];

    // Gera o hash da nova senha de forma segura
    $hashedPassword = password_hash($newPassword, PASSWORD_DEFAULT);

    // Atualiza a senha no banco de dados e limpa o token de reset
    $stmt = $conn->prepare("UPDATE usuarios SET senha = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?");
    
    if ($stmt === false) {
        error_log("resetpassword.php: Erro na preparação da query SQL (UPDATE senha): " . $conn->error);
        echo json_encode(["status" => "error", "message" => "Erro interno do servidor ao redefinir senha."]);
        exit();
    }
    
    $stmt->bind_param("si", $hashedPassword, $userId);

    if ($stmt->execute()) {
        error_log("resetpassword.php: Senha redefinida com sucesso para o usuário ID: " . $userId);
        echo json_encode(["status" => "success", "message" => "Sua senha foi redefinida com sucesso!", "redirect" => "/receitas_práticas/login/suaconta.php"]); // Caminho absoluto corrigido
    } else {
        error_log("resetpassword.php: Erro ao atualizar senha para o usuário ID: " . $userId . " - " . $conn->error);
        echo json_encode(["status" => "error", "message" => "Erro ao redefinir a senha. Por favor, tente novamente."]);
    }
    exit(); // Finaliza a execução do script PHP após a resposta JSON do POST

}

// --- Lógica para REQUISIÇÕES GET (quando a página é carregada pela primeira vez via link de e-mail) ---
error_log("resetpassword.php: Não é POST. Verificando se é GET com token.");
// Remove qualquer Content-Type anterior para que o navegador interprete como HTML
header_remove('Content-Type'); 

if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['token'])) {
    error_log("resetpassword.php: Entrou no bloco GET com token.");
    $token = $_GET['token'];
    
    // Busca o usuário pelo token e verifica validade
    $stmt = $conn->prepare("SELECT id, email FROM usuarios WHERE reset_token = ? AND reset_token_expiry > NOW()");
    
    if ($stmt === false) {
        error_log("resetpassword.php: Erro na preparação da query SQL (SELECT GET token): " . $conn->error);
        echo '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Erro Interno</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css"></head><body><script src="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.all.min.js"></script><script>';
        echo "document.addEventListener('DOMContentLoaded', function() {";
        echo "Swal.fire({
                icon: 'error',
                title: 'Erro!',
                text: 'Ocorreu um erro interno. Por favor, tente mais tarde.',
                confirmButtonText: 'OK'
            }).then(() => {
                window.location.href='forgotpass.html';
            });";
        echo "});";
        echo '</body></html>';
        exit();
    }

    $stmt->bind_param("s", $token);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows === 0) {
        error_log("resetpassword.php: GET com token inválido/expirado.");
        echo '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Token Inválido</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css"></head><body><script src="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.all.min.js"></script><script>';
        echo "document.addEventListener('DOMContentLoaded', function() {";
        echo "Swal.fire({
                icon: 'error',
                title: 'Erro!',
                text: 'Token inválido ou expirado. Solicite um novo código.',
                confirmButtonText: 'OK'
            }).then(() => {
                window.location.href='forgotpass.html';
            });";
        echo "});";
        echo '</body></html>';
        exit();
    }
    
    $user = $result->fetch_assoc();
    ?>
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Redefinir Senha - Receitas Práticas</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <!-- CAMINHO DO SEU CSS CORRIGIDO AQUI -->
        <link rel="stylesheet" type="text/css" href="./esqueceusenha/resetpass.css"> 
        <!-- Inclua SweetAlert2 CSS aqui para qualquer mensagem de erro antes do script JS personalizado -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css">
    </head>
    <body>
        <main class="reset-password-page">
            <div class="container">
                <h2 class="text-center mb-4">Redefinir Senha</h2>
                <form id="resetPasswordForm"> 
                    <input type="hidden" name="token" id="token" value="<?php echo htmlspecialchars($token); ?>">
                    
                    <div class="form-group">
                        <label for="email_confirm">Confirme seu e-mail:</label>
                        <input type="email" class="form-control" id="email_confirm" name="email_confirm" value="<?php echo htmlspecialchars($user['email']); ?>" required readonly>
                    </div>
                    <div class="form-group">
                        <label for="password">Nova Senha:</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <label for="confirm_password">Confirme a Nova Senha:</label>
                        <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                    </div>
                    <button type="submit" class="btn btn-danger-custom">Redefinir Senha</button>
                </form>
            </div>
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.all.min.js"></script>
        <script src="./js/resetpass.js"></script> 
    </body>
    </html>
    <?php
    exit();
}

error_log("resetpassword.php: Redirecionando para forgotpass.html (sem POST ou GET com token válido).");
header("Location: forgotpass.html");
exit();
?>
