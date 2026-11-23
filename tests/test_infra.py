"""Teste da infraestrutura real (containers da P1).

So roda quando os containers estao no ar e voce pede:  MONITOR_INFRA=1 pytest tests/test_infra.py
Fora disso e pulado (no GitHub Actions nao ha containers).

Sabotagem manual: `docker compose stop db` dentro de servicos/ -> este teste tem que falhar.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import smtplib
import subprocess
import sys
import time
from pathlib import Path

import dns.resolver
import pymysql
import pytest
import requests

from plataforma.contrato import config
from plataforma.infra.coletor import medir
from tests.falsos.servicos_falsos import porta_livre

pytestmark = pytest.mark.skipif(os.environ.get("MONITOR_INFRA") != "1",
                                reason="defina MONITOR_INFRA=1 com os containers no ar")

CONTAINERS = ["web", "db", "dns", "smtp"]
config.carregar_env()   # o coletor le o .env ao iniciar; aqui o teste chama medir() direto
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "servicos" / "agente"))   # para importar agente_fontes


@pytest.mark.parametrize("servico", config.servicos_monitorados(), ids=lambda s: s.nome)
def test_servico_real_responde(servico):
    assert medir(servico)["disponivel"] == 1.0, f"{servico.nome} nao respondeu"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker nao encontrado")
@pytest.mark.parametrize("nome", CONTAINERS)
def test_container_tem_limite_de_recursos(nome):
    r = subprocess.run(["docker", "inspect", f"monitoramento-{nome}-1", "--format", "{{json .HostConfig}}"],
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, f"container monitoramento-{nome}-1 nao encontrado: {r.stderr}"
    host = json.loads(r.stdout)
    assert host["NanoCpus"] > 0, "sem limite de CPU"
    assert host["Memory"] > 0, "sem limite de memoria"
    assert (host.get("PidsLimit") or 0) > 0, "sem limite de processos"


# ---------- site Receitas Praticas e banco (P1, tarefas 2 e 3) ----------
# Sabotagens manuais: `docker compose stop db` -> os testes de login e do monitor falham;
# apagar uma chamada registrar_tentativa() do login.php -> o teste do log falha.

SITE_URL = "http://127.0.0.1:8080/receitas_pr%C3%A1ticas"
ENV_SERVICOS = RAIZ / "servicos" / ".env"


def _env_servicos() -> dict[str, str]:
    """Le servicos/.env (CHAVE=valor por linha) sem expor nada na tela."""
    valores = {}
    for linha in ENV_SERVICOS.read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            chave, valor = linha.split("=", 1)
            valores[chave.strip()] = valor.strip()
    return valores


def _docker(*argumentos: str) -> str:
    r = subprocess.run(["docker", *argumentos], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stderr
    return r.stdout


def _linhas_do_log_de_login() -> list[dict]:
    texto = _docker("exec", "monitoramento-web-1", "sh", "-c", "cat /var/log/app/login.log 2>/dev/null || true")
    return [json.loads(linha) for linha in texto.splitlines() if linha.strip()]


def test_site_receitas_no_ar():
    r = requests.get("http://127.0.0.1:8080/", timeout=10)
    assert r.status_code == 200 and "Receitas Práticas" in r.text


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker nao encontrado")
def test_login_certo_e_errado_geram_uma_linha_cada():
    email, senha = f"teste-{secrets.token_hex(4)}@lab.local", secrets.token_hex(8)
    r = requests.post(f"{SITE_URL}/cadastro/cadastro.php", timeout=10, allow_redirects=False,
                      data={"firstname": "Teste", "lastname": "Auto", "email": email, "number": "61900000000",
                            "password": senha, "Confirmpassword": senha})
    assert r.status_code == 302, f"cadastro falhou: {r.text[:200]}"
    antes = len(_linhas_do_log_de_login())

    requests.post(f"{SITE_URL}/login/login.php", data={"email": email, "senha": "errada"}, timeout=10)
    sessao = requests.Session()
    r = sessao.post(f"{SITE_URL}/login/login.php", data={"email": email, "senha": senha}, timeout=10)
    assert email in r.text, "login certo nao chegou em suaconta.php"

    novas = _linhas_do_log_de_login()[antes:]
    assert [(l["usuario"], l["sucesso"]) for l in novas] == [(email, False), (email, True)]


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker nao encontrado")
def test_esqueci_a_senha_entrega_no_smtp():
    contar = ["exec", "monitoramento-smtp-1", "sh", "-c", "ls /var/mail/lab/new 2>/dev/null | wc -l"]
    antes = int(_docker(*contar))
    r = requests.post(f"{SITE_URL}/login/forgotpassword.php", data={"email": "ana@lab.local"}, timeout=30)
    assert "E-mail enviado" in r.text, "o site nao conseguiu enviar pelo container smtp"
    for _ in range(10):  # o Postfix entrega em menos de 1 s, mas pode atrasar
        if int(_docker(*contar)) > antes:
            return
        time.sleep(1)
    pytest.fail("o e-mail nao chegou na caixa /var/mail/lab do container smtp")


def test_usuario_monitor_so_le():
    senha = _env_servicos().get("MONITOR_DB_SENHA")
    assert senha, "defina MONITOR_DB_SENHA no servicos/.env"
    conexao = pymysql.connect(host="127.0.0.1", port=3307, user="monitor", password=senha,
                              database="cadastro_db", connect_timeout=5)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            assert cursor.fetchone()[0] >= 5, "os 5 usuarios inventados do init.sql nao estao no banco"
            with pytest.raises(pymysql.err.OperationalError):  # sabotagem embutida: escrever tem que falhar
                cursor.execute("INSERT INTO favorites (user_id, recipe_url) VALUES (1, 'x')")
    finally:
        conexao.close()


# ---------- DNS e SMTP (P1, tarefas 4 e 5) ----------

def test_dns_resolve_a_zona_do_laboratorio():
    resolvedor = dns.resolver.Resolver(configure=False)
    resolvedor.nameservers, resolvedor.port, resolvedor.lifetime = ["127.0.0.1"], 1053, 3
    assert resolvedor.resolve("teste.lab.local", "A")[0].to_text() == "192.0.2.10"
    with pytest.raises(dns.resolver.NXDOMAIN):  # sabotagem embutida: nome que nao existe
        resolvedor.resolve("nao-existe.lab.local", "A")


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker nao encontrado")
def test_smtp_entrega_e_registra_no_log():
    assert _docker("exec", "monitoramento-smtp-1", "postqueue", "-j") is not None  # comando da fila funciona
    marca = f"teste-{secrets.token_hex(4)}@lab.local"
    with smtplib.SMTP("127.0.0.1", 2525, timeout=10) as smtp:
        smtp.sendmail("nao-responda@lab.local", [marca], f"Subject: teste\n\nteste {marca}")
    for _ in range(10):
        if any(marca in l and "status=sent" in l for l in _docker("logs", "monitoramento-smtp-1").splitlines()):
            return
        time.sleep(1)
    pytest.fail("o envio nao apareceu com status=sent no log do Postfix")


# ---------- agente (P1, tarefa 6) com os containers de verdade ----------

@pytest.mark.skipif(shutil.which("docker") is None, reason="docker nao encontrado")
def test_agente_le_os_containers_de_verdade(tmp_path):
    porta, token = porta_livre(), secrets.token_hex(16)
    processo = subprocess.Popen([sys.executable, str(RAIZ / "servicos" / "agente" / "agente.py"), "--porta", str(porta)],
                                env={**os.environ, "MONITOR_AGENTE_TOKEN": token},
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    url = f"http://127.0.0.1:{porta}/metrics"
    try:
        for _ in range(30):
            try:
                requests.get(url, timeout=1)
                break
            except requests.ConnectionError:
                time.sleep(0.3)
        requests.get(url, headers={"X-Token": token}, timeout=30)          # zera as janelas
        requests.post(f"{SITE_URL}/login/login.php", data={"email": "ninguem@lab.local", "senha": "x"}, timeout=10)
        dados = requests.get(url, headers={"X-Token": token}, timeout=30).json()
    finally:
        processo.terminate()
        erros = processo.communicate(timeout=10)[1]

    assert dados["apache"]["total_accesses"] is not None, f"apache sem dado: {erros}"
    assert dados["log_web"]["total"] >= 1, "o log de acesso nao chegou no agente"
    assert [t["usuario"] for t in dados["auth"]] == ["ninguem@lab.local"]
    assert dados["unbound"]["total.num.queries"] is not None, f"unbound sem dado: {erros}"
    assert isinstance(dados["postfix"]["fila"], int), f"fila sem dado: {erros}"
    assert all(dados["containers"][n]["cpu_pct"] is not None for n in CONTAINERS), f"docker stats: {erros}"
    assert all(h is not None for h in dados["hashes"].values()), f"hash sem dado: {erros}"
    versoes = {f"{s}/{p}": v for s, programas in dados["versoes"].items() for p, v in programas.items()}
    assert all(versoes.values()), f"versao sem dado: {versoes} {erros}"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker nao encontrado")
def test_alterar_configuracao_muda_o_hash():
    import agente_fontes as fontes
    arquivos = {"monitoramento-smtp-1": ["/etc/postfix/main.cf"]}
    original = fontes.hashes(fontes.executar, arquivos)["/etc/postfix/main.cf"]
    _docker("exec", "monitoramento-smtp-1", "sh", "-c", "echo '# alteracao de teste' >> /etc/postfix/main.cf")
    try:
        alterado = fontes.hashes(fontes.executar, arquivos)["/etc/postfix/main.cf"]
    finally:
        _docker("exec", "monitoramento-smtp-1", "sed", "-i", "$d", "/etc/postfix/main.cf")   # desfaz
    assert alterado != original
    assert fontes.hashes(fontes.executar, arquivos)["/etc/postfix/main.cf"] == original, "a restauracao falhou"


# ---------- isolamento (P1, tarefa 7; regra da professora) ----------

def test_ataque_ao_web_nao_derruba_os_outros():
    """15 s de DDoS no web; db, dns e smtp tem que responder em 95% das sondas."""
    sys.path.insert(0, str(RAIZ / "testes"))
    import teste_isolamento
    relatorio = teste_isolamento.testar(segundos=15, conexoes=30)
    assert relatorio["ataque_web"]["requisicoes"] > 0, "o ataque nem chegou no web"
    assert relatorio["aprovado"], f"um servico caiu durante o ataque ao web: {relatorio['servicos']}"
