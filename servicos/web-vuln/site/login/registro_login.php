<?php
// Registra cada tentativa de login em uma linha JSON (formato combinado em docs/ia/pedido-p1.md):
// {"ts": 1795036790, "origem": "IP", "usuario": "email", "sucesso": false}
// O agente le este arquivo para detectar forca bruta. Caminho: variavel LOGIN_LOG.
function registrar_tentativa(string $usuario, bool $sucesso): void
{
    $caminho = getenv('LOGIN_LOG') ?: '/var/log/app/login.log';
    $linha = json_encode([
        'ts' => time(),
        'origem' => $_SERVER['REMOTE_ADDR'] ?? 'desconhecida',
        'usuario' => $usuario,
        'sucesso' => $sucesso,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    // @ evita o aviso duplicado do PHP; a falha e registrada logo abaixo (nao fica escondida)
    if (@file_put_contents($caminho, $linha . "\n", FILE_APPEND | LOCK_EX) === false) {
        error_log("registro_login: nao foi possivel gravar em $caminho");
    }
}
