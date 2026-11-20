-- Banco do site Receitas Praticas (container db). Roda sozinho na PRIMEIRA subida do container
-- (pasta montada em /docker-entrypoint-initdb.d). Para rodar de novo: docker compose down -v.
-- Baseado no "Banco - ReceitaPraticas.sql" do site original, ja com os ALTER TABLE aplicados
-- e com as colunas/tabelas que o codigo usa e o script original nao criava.
-- Todos os dados abaixo sao INVENTADOS. As senhas sao hashes de textos aleatorios que ninguem sabe.

CREATE DATABASE IF NOT EXISTS cadastro_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cadastro_db;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(100) NOT NULL DEFAULT '',
    email VARCHAR(100) NOT NULL UNIQUE,
    telefone VARCHAR(15),
    senha VARCHAR(255) NOT NULL,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    ativo TINYINT(1) DEFAULT 1,
    token_verificacao VARCHAR(255) NULL,
    email_verificado TINYINT(1) DEFAULT 0,
    reset_token VARCHAR(64) NULL,          -- usado por login/forgotpassword.php
    reset_token_expiry DATETIME NULL       -- e por login/resetpassword.php
);

CREATE TABLE IF NOT EXISTS recuperacao_senha (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_expiracao DATETIME NOT NULL,
    utilizado TINYINT(1) DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Receitas favoritas (usada por api/get_favorites.php e api/toggle_favorite.php)
CREATE TABLE IF NOT EXISTS favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recipe_url VARCHAR(255) NOT NULL,
    recipe_title VARCHAR(150) NOT NULL DEFAULT '',
    recipe_image VARCHAR(255) NOT NULL DEFAULT '',
    UNIQUE KEY favorito_unico (user_id, recipe_url),
    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE INDEX idx_recuperacao_token ON recuperacao_senha(token);

-- Dados inventados
INSERT INTO usuarios (nome_completo, email, telefone, senha) VALUES
    ('Ana Teste', 'ana@lab.local', '61900000001', '$2y$10$yXKADx4QiJu7c7Cb.31njusyRaAXkh4mP6cd04xtG76oRexINiaoq'),
    ('Bruno Exemplo', 'bruno@lab.local', '61900000002', '$2y$10$NGQCFH0MeaBf6z.p95MYdeYK.JjM18aN3r.uNK8IlWB6soixjs3Wq'),
    ('Carla Ficticia', 'carla@lab.local', '61900000003', '$2y$10$XoV5HLSvuNhpgP34VZ5rQedQcXDWZM.jrLImYCGPyXJL5aInFna5i'),
    ('Diego Modelo', 'diego@lab.local', '61900000004', '$2y$10$9ZlR3gH2bNOx437hyL8d9.1Asr8FNBOvdE8q9JxUACz/ZKJ2TLET.'),
    ('Elisa Amostra', 'elisa@lab.local', '61900000005', '$2y$10$aUT2MqfkZliswbYphpCltubz5aKl1YyjW7wraWS4dJL4ltE8r59Di');

INSERT INTO favorites (user_id, recipe_url, recipe_title, recipe_image) VALUES
    (1, 'ReceitasVegan/coxinha.html', 'Coxinha vegana', 'ReceitasVegan/imgvegan/coxinhas-gluten.jpg'),
    (1, 'ReceitasVeget/falafel.html', 'Falafel com tahini', 'ReceitasVeget/imgvegetariana/falafel com tahini.jpg'),
    (2, 'ReceitasVegan/bolodebanana.html', 'Bolo de banana', 'ReceitasVegan/imgvegan/bolodebanana.jpg'),
    (3, 'ReceitasVeget/quiche.html', 'Quiche de cogumelo', 'ReceitasVeget/imgvegetariana/quiche-de-cogumelo.jpg');
