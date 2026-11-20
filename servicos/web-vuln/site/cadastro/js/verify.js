document.addEventListener('DOMContentLoaded', function() {
    // Função auxiliar para exibir SweetAlerts
    function showSweetAlert(title, text, type, timer = null, showConfirmButton = true, redirectUrl = null) {
        swal({
            title: title,
            text: text,
            type: type,
            timer: timer, // Tempo em ms para o alerta fechar automaticamente (ou null)
            showConfirmButton: showConfirmButton // Se mostra ou não o botão 'OK'
        }, function() {
            // Callback que é executado após o alerta fechar (seja por timer ou clique)
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        });
    }

    // --- Lógica para o formulário de atualização de informações (ex: na sua conta) ---
    const updateForm = document.getElementById('update-form');
    if (updateForm) {
        updateForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Impede o envio padrão do formulário HTML

            // Idealmente, aqui você enviaria os dados do formulário via AJAX para um script PHP
            // que processaria a atualização no banco de dados e retornaria um JSON (sucesso/erro).
            // Exemplo conceitual (não funcional sem o backend):
            /*
            fetch('/caminho/do/seu_script_update_info.php', {
                method: 'POST',
                body: new FormData(updateForm) // Envia os dados do formulário
            })
            .then(response => response.json()) // Espera uma resposta JSON
            .then(data => {
                if (data.success) {
                    showSweetAlert("Sucesso!", data.message || "Informações atualizadas com sucesso!", "success", 2000, false);
                } else {
                    showSweetAlert("Erro!", data.message || "Não foi possível atualizar as informações.", "error");
                }
            })
            .catch(error => {
                console.error('Erro na requisição:', error);
                showSweetAlert("Erro de Conexão!", "Não foi possível conectar ao servidor. Tente novamente.", "error");
            });
            */

            // Por enquanto, apenas simula o sucesso com SweetAlert
            showSweetAlert("Sucesso!", "Informações atualizadas com sucesso!", "success", 2000, false);
        });
    }

    // --- Lógica para o formulário de atualização de senha ---
    const passwordForm = document.getElementById('password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Impede o envio padrão do formulário HTML

            // Idealmente, aqui você enviaria os dados via AJAX para um script PHP
            // que processaria a atualização da senha.
            // Exemplo conceitual (não funcional sem o backend):
            /*
            fetch('/caminho/do/seu_script_update_senha.php', {
                method: 'POST',
                body: new FormData(passwordForm)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSweetAlert("Senha Atualizada!", data.message || "Sua senha foi atualizada.", "success", 2500, false);
                } else {
                    showSweetAlert("Erro!", data.message || "Não foi possível atualizar a senha.", "error");
                }
            })
            .catch(error => {
                console.error('Erro na requisição:', error);
                showSweetAlert("Erro de Conexão!", "Não foi possível conectar ao servidor.", "error");
            });
            */

            // Por enquanto, apenas simula o sucesso com SweetAlert
            showSweetAlert("Senha Atualizada!", "Sua senha foi atualizada.", "success", 2500, false);
        });
    }

    // --- Lógica para o botão de logout ---
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', function() {
            // Idealmente, aqui você faria uma requisição para um script PHP de logout
            // que encerraria a sessão no servidor.
            /*
            fetch('/caminho/do/seu_script_logout.php')
            .then(response => response.json()) // Se o script de logout retornar um JSON
            .then(data => {
                if (data.success) {
                    showSweetAlert("Sessão Encerrada", "Você saiu da sua conta.", "info", 2000, false, '/receitas_praticas/home.html');
                } else {
                    showSweetAlert("Erro ao Sair!", data.message || "Não foi possível encerrar a sessão.", "error");
                }
            })
            .catch(error => {
                console.error('Erro na requisição:', error);
                showSweetAlert("Erro de Conexão!", "Não foi possível conectar ao servidor.", "error");
            });
            */
            
            // Por enquanto, apenas simula o logout com SweetAlert e redireciona para a home
            showSweetAlert("Sessão Encerrada", "Você saiu da sua conta.", "info", 2000, false, '/receitas_praticas/home.html');
        });
    }
});