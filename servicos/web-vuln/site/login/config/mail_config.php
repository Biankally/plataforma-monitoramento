<?php
// Envio de e-mail do "esqueci a senha". No laboratorio vai para o container smtp (Postfix),
// porta 25, sem usuario e sem senha. Os valores vem do docker-compose.yml.
define('MAIL_HOST', getenv('MAIL_HOST') ?: 'smtp');
define('MAIL_PORT', (int) (getenv('MAIL_PORT') ?: 25));
define('MAIL_FROM', getenv('MAIL_FROM') ?: 'nao-responda@lab.local');
define('MAIL_USERNAME', getenv('MAIL_USERNAME') ?: '');   // vazio = sem autenticacao
define('MAIL_PASSWORD', getenv('MAIL_PASSWORD') ?: '');
define('MAIL_TLS', getenv('MAIL_TLS') === '1');          // STARTTLS so se pedir
