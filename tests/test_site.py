"""Testes do site vulneravel e do banco que rodam sem containers (inclusive no GitHub Actions).

O que garantem:
1. toda conexao com o MySQL passa pelo db.php (que le as variaveis de ambiente);
2. nao sobrou senha, root ou e-mail real no codigo;
3. todo arquivo PHP tem sintaxe valida;
4. o registro de login grava uma linha JSON no formato combinado em docs/ia/pedido-p1.md;
5. o init.sql cria as 3 tabelas e o usuario monitor so pode ler.
Cada verificacao tem um teste de sabotagem logo abaixo.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

import pytest

from tests.varredura_site import BANCO, RAIZ, SITE, conexoes_fora_do_lugar, segredos

PHP = shutil.which("php")
sem_php = pytest.mark.skipif(PHP is None, reason="php nao instalado")


# ---------- 1 e 2: conexoes e segredos ----------

def test_site_copiado():
    assert (SITE / "home.html").is_file()
    assert (SITE / "db.php").is_file()
    assert not (SITE / ".git").exists(), "a pasta .git do site original nao pode vir junto"


def test_toda_conexao_passa_pelo_db_php():
    assert conexoes_fora_do_lugar(SITE) == []


def test_sem_segredos_no_site_nem_no_banco():
    assert segredos(SITE, BANCO) == []


def test_sabotagem_varredura_acusa_conexao_e_segredo(tmp_path):
    (tmp_path / "ruim.php").write_text(
        '<?php $password = "minhasenha"; $c = new mysqli("localhost", "root", $password, "x");\n'
        "define('MAIL_PASSWORD', 'abcd efgh');\n"
        "// contato: fulano@gmail.com\n", encoding="utf-8")
    assert conexoes_fora_do_lugar(tmp_path) == ["ruim.php"]
    motivos = " ".join(segredos(tmp_path))
    for motivo in ["root", "senha escrita", "credencial de e-mail", "gmail"]:
        assert motivo in motivos, f"a varredura nao acusou: {motivo}"


# ---------- 3: sintaxe PHP ----------

@sem_php
def test_php_sem_erro_de_sintaxe():
    erros = []
    for arquivo in sorted(SITE.rglob("*.php")):
        if "vendor" in arquivo.parts:
            continue
        r = subprocess.run([PHP, "-l", str(arquivo)], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            erros.append(f"{arquivo.relative_to(SITE)}: {r.stdout.strip()} {r.stderr.strip()}")
    assert erros == []


# ---------- 4: registro de login ----------

def _registrar(caminho_log, usuario, sucesso):
    """Chama a funcao PHP registrar_tentativa() como o login.php chama."""
    codigo = ("require $argv[1]; registrar_tentativa($argv[2], $argv[3] === '1');")
    ambiente = {**os.environ, "LOGIN_LOG": str(caminho_log)}
    return subprocess.run([PHP, "-r", codigo, str(SITE / "login" / "registro_login.php"),
                           usuario, "1" if sucesso else "0"],
                          capture_output=True, text=True, encoding="utf-8", env=ambiente)


@sem_php
def test_registro_de_login_grava_uma_linha_json_por_tentativa(tmp_path):
    log = tmp_path / "login.log"
    assert _registrar(log, "ana@lab.local", False).returncode == 0
    assert _registrar(log, "ana@lab.local", True).returncode == 0
    linhas = log.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 2
    primeira, segunda = (json.loads(linha) for linha in linhas)
    assert set(primeira) == {"ts", "origem", "usuario", "sucesso"}
    assert isinstance(primeira["ts"], int) and primeira["ts"] > 1_700_000_000
    assert primeira["usuario"] == "ana@lab.local"
    assert primeira["sucesso"] is False and segunda["sucesso"] is True


@sem_php
def test_sabotagem_log_sem_permissao_nao_passa_calado(tmp_path):
    """Se o arquivo de log nao pode ser gravado, o PHP tem que avisar (nada de erro escondido)."""
    r = _registrar(tmp_path / "pasta-que-nao-existe" / "login.log", "ana@lab.local", False)
    assert "nao foi possivel gravar" in (r.stdout + r.stderr)


def test_login_php_registra_sucesso_e_as_duas_falhas():
    codigo = (SITE / "login" / "login.php").read_text(encoding="utf-8")
    assert codigo.count("registrar_tentativa(") == 3, "falta registrar: sucesso, senha errada, e-mail inexistente"


def test_logout_php_sem_javascript_dentro():
    codigo = (SITE / "login" / "logout.php").read_text(encoding="utf-8")
    assert "localStorage" not in codigo


# ---------- 5: banco ----------

def test_init_sql_cria_as_tres_tabelas():
    sql = (BANCO / "init.sql").read_text(encoding="utf-8")
    for tabela in ["usuarios", "recuperacao_senha", "favorites"]:
        assert re.search(rf"CREATE TABLE IF NOT EXISTS {tabela}\b", sql), f"falta a tabela {tabela}"
    for coluna in ["nome_completo", "telefone", "reset_token", "reset_token_expiry"]:
        assert coluna in sql, f"falta a coluna {coluna} (o site usa)"


def test_dados_do_banco_sao_inventados():
    sql = (BANCO / "init.sql").read_text(encoding="utf-8")
    emails = re.findall(r"[\w.+-]+@[\w.-]+", sql)
    assert emails, "o init.sql deveria ter usuarios de exemplo"
    assert all(e.endswith("@lab.local") for e in emails), "so e-mail inventado do dominio lab.local"


def test_usuario_monitor_so_le():
    script = (BANCO / "02-monitor.sh").read_text(encoding="utf-8")
    concessoes = re.findall(r"GRANT\s+(.+?)\s+ON", script, re.IGNORECASE)
    assert concessoes, "o script nao da permissao nenhuma ao monitor"
    for permissao in concessoes:
        assert set(p.strip().upper() for p in permissao.split(",")) <= {"SELECT", "PROCESS"}, \
            f"monitor so pode ler, recebeu: {permissao}"
    assert "MONITOR_DB_SENHA" in script, "a senha do monitor tem que vir do .env"


def test_compose_liga_site_ao_banco_sem_root():
    compose = (RAIZ / "servicos" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "DB_HOST: db" in compose
    assert "./banco:/docker-entrypoint-initdb.d:ro" in compose
    assert "web_logs:/var/log/app" in compose, "o log de login precisa ficar num volume (o agente le depois)"
    assert not re.search(r"DB_USER:\s*root", compose)
