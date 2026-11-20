document.addEventListener('DOMContentLoaded', () => {
    const favoriteButtons = document.querySelectorAll('.favorite-button');
    let isLoggedIn = false; // Flag para o status de login
    let userFavorites = []; // Cache local dos favoritos do usuário logado

    // Função para verificar o status de login no servidor e buscar favoritos
    async function checkLoginStatusAndLoadFavorites() {
        try {
            // Tenta buscar o status do usuário no servidor
            const response = await fetch('/receitas_práticas/api/get_user_status.php');
            const data = await response.json();

            isLoggedIn = data.loggedIn;

            if (isLoggedIn) {
                // Se logado, busca os favoritos do servidor
                const favoritesResponse = await fetch('/receitas_práticas/api/get_favorites.php');
                const favoritesData = await favoritesResponse.json();
                if (favoritesData.success) {
                    userFavorites = favoritesData.favorites;
                } else {
                    console.error('Erro ao carregar favoritos do servidor:', favoritesData.message);
                    userFavorites = []; // Limpa se houver erro
                }
            } else {
                userFavorites = []; // Não logado, sem favoritos
            }
        } catch (error) {
            console.error('Erro ao verificar status de login ou carregar favoritos:', error);
            isLoggedIn = false;
            userFavorites = [];
        }
        // Atualiza o estado de TODOS os botões após verificar o login e favoritos
        updateAllButtonsState();
    }

    // Função para atualizar o texto e estado visual de um botão individual
    function updateButtonVisualState(button, isFavorite) {
        button.classList.remove('btn-secondary', 'btn-warning', 'btn-light'); // Remove todas as classes de cor anteriores
        if (isFavorite) {
            button.textContent = '⭐ Favoritado';
            button.classList.add('btn-warning'); // Cor para favoritado (amarelo Bootstrap, ou sua customização)
        } else {
            button.textContent = '⭐ Marcar como favorito';
            button.classList.add('btn-secondary'); // Cor para não favoritado (cinza Bootstrap, ou sua customização)
        }
    }

    // Função para atualizar o estado de todos os botões na página
    function updateAllButtonsState() {
        favoriteButtons.forEach(button => {
            const card = button.closest('.card');
            let recipeUrl = card.dataset.recipeUrl;

            // Limpar o "./" da URL para consistência com o banco de dados
            if (recipeUrl && recipeUrl.startsWith('./')) {
                recipeUrl = recipeUrl.substring(2);
            }

            // Verifica se a receita está nos favoritos do usuário logado
            const isFavorite = userFavorites.some(fav => fav.recipe_url === recipeUrl);

            updateButtonVisualState(button, isFavorite);

            if (!isLoggedIn) {
                button.disabled = true; // Desabilita o botão se não estiver logado
                button.textContent = ' Faça login para favoritar'; // Texto claro
                button.classList.remove('btn-secondary', 'btn-warning'); // Remove cores
                button.classList.add('btn', 'btn-light'); // Estilo neutro ( Bootstrap btn-light)
                button.style.cursor = 'not-allowed'; // Mudar cursor
                button.title = 'Faça login para adicionar esta receita aos favoritos.'; // Tooltip
            } else {
                button.disabled = false; // Habilita o botão se estiver logado
                button.style.cursor = 'pointer'; // Mudar cursor
                button.title = ''; // Limpa o tooltip
            }
        });
    }

    // Adiciona evento de clique aos botões de favorito
    favoriteButtons.forEach(button => {
        button.addEventListener('click', async (event) => {
            // Se o botão estiver desabilitado (não logado), exibe alerta e redireciona
            if (event.target.disabled) {
                alert('É necessário efetuar o login para favoritar receitas. Você será redirecionado para a página de login.');
                window.location.href = '../login.html'; // Redireciona para a página de login
                return; // Impede a execução do restante da função
            }

            const card = event.target.closest('.card');
            let recipeUrl = card.dataset.recipeUrl;
            let recipeImage = card.dataset.recipeImage;
            const recipeTitle = card.dataset.recipeTitle;

            // Limpar o "./" da URL e da imagem antes de enviar ao backend
            if (recipeUrl && recipeUrl.startsWith('./')) {
                recipeUrl = recipeUrl.substring(2);
            }
            if (recipeImage && recipeImage.startsWith('./')) {
                recipeImage = recipeImage.substring(2);
            }

            try {
                const formData = new FormData(); // Usar FormData para enviar dados POST
                formData.append('url', recipeUrl);
                formData.append('title', recipeTitle);
                formData.append('image', recipeImage);

                const response = await fetch('/receitas_práticas/api/toggle_favorite.php', {
                    method: 'POST',
                    body: formData // Envia o FormData
                });

                const result = await response.json(); // Analisa a resposta JSON do PHP

                if (result.success) {
                    alert(result.message);
                    // Atualiza o cache local de favoritos e o estado visual
                    await checkLoginStatusAndLoadFavorites(); // Re-carrega favoritos após toggle
                } else {
                    alert('Erro: ' + result.message);
                    if (result.message === 'Usuário não logado.') {
                        window.location.href = '../login.html'; // Redireciona se a API disser que não está logado
                    }
                }
            } catch (error) {
                console.error('Erro ao favoritar/desfavoritar:', error);
                alert('Ocorreu um erro ao processar sua solicitação.');
            }
        });
    });

    // Chama a função ao carregar a página para definir o estado inicial dos botões
    checkLoginStatusAndLoadFavorites();
});