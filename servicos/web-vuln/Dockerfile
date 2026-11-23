# Container web: Apache + PHP 8.3 com a extensao mysqli (o site usa mysqli).
FROM php:8.3-apache
RUN docker-php-ext-install mysqli \
 && a2enmod status \
 && mkdir -p /var/log/app \
 && chown www-data:www-data /var/log/app \
 && echo "AddDefaultCharset UTF-8" > /etc/apache2/conf-enabled/zz-charset.conf
# (o site e todo em UTF-8; sem isso o Apache nao avisa e acentos podem aparecer quebrados)
# Pagina de estado do Apache (requisicoes, workers ocupados): so para quem esta na rede interna.
COPY apache-status.conf /etc/apache2/conf-enabled/zz-status.conf
# Log de acesso extra, so com "codigo tempo_em_microssegundos", para o agente calcular erros e p95.
COPY apache-log.conf /etc/apache2/conf-enabled/zz-log.conf
# Raiz do servidor: redireciona para /receitas_práticas/ (o site e montado como volume no compose).
COPY raiz/index.php /var/www/html/index.php
# /var/log/app e uma pasta do WSL (servicos/logs/web) montada no container: na subida, o dono
# passa a ser o usuario do Apache, para o PHP conseguir gravar o login.log.
CMD ["sh", "-c", "chown www-data:www-data /var/log/app && exec apache2-foreground"]
