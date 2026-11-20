document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('resetPasswordForm');

    // Verifica se o formulário existe antes de adicionar o event listener
    if (!form) {
        console.error("Erro: Formulário com ID 'resetPasswordForm' não encontrado.");
        return; // Sai da função se o formulário não for encontrado
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault(); // Previne o envio tradicional do formulário

        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true; // Desabilita o botão para evitar múltiplos envios
        submitButton.textContent = "Alterando..."; // Altera o texto do botão

        const emailConfirm = document.getElementById('email_confirm').value.trim();
        const newPassword = document.getElementById('password').value.trim();
        const confirmPassword = document.getElementById('confirm_password').value.trim();
        // **IMPORTANTE**: Certifique-se de que o campo hidden 'token' existe no seu formulário HTML
        // e que ele tem o id="token". Ele deve conter o token recebido na URL.
        const tokenInput = document.getElementById('token');
        const token = tokenInput ? tokenInput.value : ''; // Pega o valor do token, se o campo existir

        // --- VALIDAÇÕES BÁSICAS NO CLIENT-SIDE ---
        // Verifica se as senhas coincidem
        if (newPassword !== confirmPassword) {
            Swal.fire({
                icon: 'error',
                title: 'Erro de Senha!',
                text: 'As senhas digitadas não coincidem. Por favor, verifique.',
                confirmButtonText: 'OK'
            });
            submitButton.disabled = false;
            submitButton.textContent = "Alterar Senha";
            return; // Interrompe a execução
        }

        // Verifica o tamanho mínimo da senha (ajuste conforme sua política de segurança)
        if (newPassword.length < 6) { 
            Swal.fire({
                icon: 'error',
                title: 'Senha Inválida!',
                text: 'A nova senha deve ter pelo menos 6 caracteres.',
                confirmButtonText: 'OK'
            });
            submitButton.disabled = false;
            submitButton.textContent = "Alterar Senha";
            return; // Interrompe a execução
        }

        // --- ENVIANDO DADOS PARA O SERVIDOR ---
        try {
            // **CAMINHO ABSOLUTO DEFINITIVO:**
            // Com base na sua localização C:\xampp\htdocs\receitas_práticas\login\resetpassword.php
            // O caminho web correto é /receitas_práticas/login/resetpassword.php
            const response = await fetch('/receitas_práticas/login/resetpassword.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    email_confirm: emailConfirm,
                    password: newPassword,
                    confirm_password: confirmPassword,
                    token: token // Enviando o token do campo hidden do formulário
                }),
            });

            // Verifica se a resposta HTTP foi bem-sucedida (status 2xx)
            if (!response.ok) {
                // Se a resposta não for OK, lança um erro com o status HTTP
                throw new Error(`Erro no servidor: ${response.status} ${response.statusText}`);
            }

            // Verifica o tipo de conteúdo da resposta
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                // Se não for JSON, tenta ler o corpo como texto para depuração
                const errorText = await response.text();
                console.error("Resposta do servidor não é JSON. Conteúdo:", errorText);
                throw new Error("Resposta inesperada do servidor. O servidor não retornou JSON.");
            }

            // Converte a resposta para JSON
            const result = await response.json();

            // Lógica para lidar com a resposta JSON do servidor
            if (result.status === 'success') {
                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso!',
                    text: result.message,
                    confirmButtonText: 'OK'
                }).then(() => {
                    window.location.href = result.redirect; // Redireciona para a página indicada pelo servidor
                });
            } else {
                // Exibe a mensagem de erro retornada pelo servidor
                Swal.fire({
                    icon: 'error',
                    title: 'Erro!',
                    text: result.message || 'Ocorreu um erro ao alterar a senha. Tente novamente.', // Mensagem padrão se 'message' estiver vazio
                    confirmButtonText: 'OK'
                });
            }
        } catch (error) {
            // Captura erros de rede ou erros lançados manualmente
            console.error('Erro na requisição ou processamento:', error);
            Swal.fire({
                icon: 'error',
                title: 'Erro inesperado!',
                text: 'Não foi possível completar a sua solicitação. Por favor, tente novamente mais tarde.',
                confirmButtonText: 'Entendi'
            });
        } finally {
            // Restaura o estado do botão
            submitButton.disabled = false;
            submitButton.textContent = "Alterar Senha";
        }
    });
});
