document.addEventListener('DOMContentLoaded', async () => {
    const favoritesList = document.getElementById('favorites-container');

    // Função para carregar favoritos do servidor
    async function loadFavoritesFromServer() {
        try {
            const response = await fetch('/receitas_práticas/api/get_favorites.php'); // Requisição ao script PHP
            const data = await response.json();

            if (!data.success && data.message === 'Usuário não logado.') {
                // Usuário não logado, exibe mensagem específica
                favoritesList.innerHTML = `
                    <div class="col-12 text-center my-5">
                        <p class="lead text-muted">Para visualizar e gerenciar suas receitas favoritas, por favor,</p>
                        <a href="../login.html" class="btn btn-primary btn-lg">Faça Login Agora</a>
                    </div>
                `;
                return []; // Retorna lista vazia
            } else if (data.success && data.favorites.length > 0) {
                return data.favorites; // Retorna os favoritos se houver sucesso e favoritos
            } else {
                // Não há favoritos (mas o usuário está logado)
                favoritesList.innerHTML = `
                    <div class="col-12 text-center my-5">
                        <p class="lead text-muted">Você ainda não possui receitas favoritas.</p>
                        <p>Que tal explorar algumas <a href="../receitasvegetarianas.html">receitas vegetarianas</a> ou <a href="../receitasveganas.html">receitas veganas</a>?</p>
                    </div>
                `;
                return [];
            }
        } catch (error) {
            console.error('Erro ao carregar favoritos:', error);
            favoritesList.innerHTML = `
                <div class="col-12 text-center my-5">
                    <p class="lead text-danger">Erro ao carregar favoritos. Tente novamente mais tarde.</p>
                </div>
            `;
            return [];
        }
    }

    // Função para exibir favoritos na lista (renderiza os cards)
    async function displayFavorites() {
        favoritesList.innerHTML = ''; // Limpa a lista existente
        const favorites = await loadFavoritesFromServer(); // Carrega do servidor

        if (favorites.length > 0) {
            favorites.forEach(recipe => {
                const colDiv = document.createElement('div');
                colDiv.className = 'col-md-4 col-sm-6 mb-4'; // Colunas para responsividade

                const cardDiv = document.createElement('div');
                cardDiv.className = 'card h-100 d-flex flex-column'; // Adiciona h-100 e d-flex flex-column

                // Adiciona data attributes para facilitar a remoção
                cardDiv.dataset.recipeUrl = recipe.recipe_url;
                cardDiv.dataset.recipeTitle = recipe.recipe_title;
                cardDiv.dataset.recipeImage = recipe.recipe_image;

                // Cria o link para a receita
                const link = document.createElement('a');
                link.href = recipe.recipe_url; // URL original da receita
                link.className = 'text-decoration-none text-dark d-flex flex-column h-100'; // O link preenche o card

                // Imagem da receita
                const imgContainer = document.createElement('div');
                imgContainer.className = 'card-img';
                const img = document.createElement('img');
                img.src = '../' + recipe.recipe_image; 
                img.alt = recipe.recipe_title;
                img.className = 'card-img-top';
                imgContainer.appendChild(img);
                link.appendChild(imgContainer);

                // Corpo do card (título)
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body text-center flex-grow-1 d-flex flex-column justify-content-end'; // flex-grow-1 para preencher espaço
                const title = document.createElement('h5');
                title.className = 'card-title';
                title.textContent = recipe.recipe_title;
                cardBody.appendChild(title);
                link.appendChild(cardBody);

                cardDiv.appendChild(link); // Adiciona o link completo (img + body) ao cardDiv

                // Botão "Remover dos Favoritos"
                const removeButton = document.createElement('button');
                removeButton.className = 'btn btn-danger btn-sm mt-2 remove-favorite-button'; // Classe para o CSS
                removeButton.textContent = 'Remover dos Favoritos';
                removeButton.dataset.url = recipe.recipe_url; // Guarda a URL para remoção
                cardDiv.appendChild(removeButton); // Adiciona o botão ao cardDiv

                colDiv.appendChild(cardDiv); // Adiciona o card ao div da coluna
                favoritesList.appendChild(colDiv); // Adiciona a coluna à lista de favoritos
            });

            // Adiciona listener para os botões de remoção
            document.querySelectorAll('.remove-favorite-button').forEach(button => {
                button.addEventListener('click', async (event) => {
                    const recipeUrlToRemove = event.target.dataset.url;
                    const cardToRemove = event.target.closest('.card'); // Encontra o card pai
                    const recipeTitleToRemove = cardToRemove.dataset.recipeTitle; // Obtém o título para a mensagem

                    try {
                        const formData = new FormData();
                        formData.append('url', recipeUrlToRemove);

                        const response = await fetch('/receitas_práticas/api/toggle_favorite.php', {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();

                        if (result.success) {
                            alert(`"${recipeTitleToRemove}" foi removido dos seus favoritos.`);
                            displayFavorites(); // Recarrega a lista após a remoção
                        } else {
                            alert('Erro ao remover dos favoritos: ' + result.message);
                            if (result.message === 'Usuário não logado.') {
                                window.location.href = '../login.html'; // Redireciona se a API disser que não está logado
                            }
                        }
                    } catch (error) {
                        console.error('Erro na requisição de remoção:', error);
                        alert('Ocorreu um erro ao remover a receita dos favoritos.');
                    }
                });
            });

        } else {
            // Mensagem de "não há favoritos" ou "faça login" já foi tratada em loadFavoritesFromServer()
        }
    }

    // Chama a função para exibir favoritos ao carregar a página
    displayFavorites();
});