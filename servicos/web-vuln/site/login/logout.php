<?php
session_start();
session_unset();
session_destroy();

// Remover o cookie
setcookie("user_token", "", time() - 3600, "/");

// (aqui havia uma linha de JavaScript dentro do PHP, que dava erro e impedia o logout;
//  o que for do navegador fica no login/js/logout.js)

// Redirecionar para a página de login
header("Location: login.html");
exit();
?>