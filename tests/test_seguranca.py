"""Regras de seguranca (dominio puro). Valores calculados a mao."""

import pytest

from plataforma.dominio import seguranca as sg

# historico de 20 amostras: dez 10 e dez 14 -> media 12, desvio populacional 2
HIST = [10.0] * 10 + [14.0] * 10


# ---------------------------------------------------------------- escore z (DDoS)
def test_escore_z_calculado_a_mao():
    # (20 - 12) / 2 = 4
    assert sg.escore_z(HIST, 20.0, piso_desvio=0.5) == pytest.approx(4.0)


def test_escore_z_usa_o_piso_quando_o_desvio_e_menor():
    plano = [10.0] * 30  # desvio 0
    assert sg.escore_z(plano, 20.0, piso_desvio=5.0) == pytest.approx(2.0)  # (20-10)/5


def test_sabotagem_historico_curto_nao_gera_escore():
    assert sg.escore_z([10.0] * (sg.MINIMO_AMOSTRAS - 1), 999.0, piso_desvio=1.0) is None


@pytest.mark.parametrize("valor, nivel", [(17.9, None), (18.0, "ATENCAO"), (21.9, "ATENCAO"), (22.0, "CRITICO")])
def test_trafego_niveis_z3_e_z5(valor, nivel):
    # z = (valor-12)/2: 17.9 -> 2.95 ; 18 -> 3 ; 21.9 -> 4.95 ; 22 -> 5
    ev = sg.avaliar_trafego("web", "web.rps", HIST, valor, piso_desvio=0.5)
    assert (ev.nivel if ev else None) == nivel
    if ev:
        assert ev.tipo == "TRAFEGO" and ev.servico == "web" and ev.origem is None
        assert "web.rps" in ev.detalhe and ev.valor == pytest.approx((valor - 12) / 2)


def test_sabotagem_queda_de_trafego_nao_e_ddos():
    assert sg.avaliar_trafego("web", "web.rps", HIST, 0.0, piso_desvio=0.5) is None


# ---------------------------------------------------------------- forca bruta
@pytest.mark.parametrize("falhas, nivel", [(4, None), (5, "ATENCAO"), (19, "ATENCAO"), (20, "CRITICO"), (500, "CRITICO")])
def test_login_limites_5_e_20(falhas, nivel):
    eventos = sg.avaliar_login({"10.0.0.9": falhas})
    assert [e.nivel for e in eventos] == ([nivel] if nivel else [])
    if nivel:
        e = eventos[0]
        assert (e.tipo, e.servico, e.origem) == ("AUTENTICACAO", "web", "10.0.0.9") and e.valor == falhas


def test_login_cada_ip_e_avaliado_sozinho():
    eventos = sg.avaliar_login({"10.0.0.1": 6, "10.0.0.2": 2, "10.0.0.3": 25})
    assert {(e.origem, e.nivel) for e in eventos} == {("10.0.0.1", "ATENCAO"), ("10.0.0.3", "CRITICO")}


def test_sabotagem_falhas_de_ips_diferentes_nao_se_somam():
    assert sg.avaliar_login({f"10.0.0.{i}": 4 for i in range(1, 30)}) == []


# ---------------------------------------------------------------- hashes
def test_hash_diferente_da_linha_de_base_e_critico():
    base = {"/etc/postfix/main.cf": "aa", "/etc/unbound/unbound.conf": "bb"}
    atual = {"/etc/postfix/main.cf": "xx", "/etc/unbound/unbound.conf": "bb"}
    eventos = sg.avaliar_hashes(atual, base)
    assert len(eventos) == 1
    e = eventos[0]
    assert (e.tipo, e.servico, e.nivel, e.origem) == ("CONFIGURACAO", "smtp", "CRITICO", "/etc/postfix/main.cf")
    assert "aa" in e.detalhe and "xx" in e.detalhe


def test_hash_igual_ou_sem_linha_de_base_ou_arquivo_novo_nao_gera_evento():
    assert sg.avaliar_hashes({"/a": "1"}, {"/a": "1"}) == []
    assert sg.avaliar_hashes({"/a": "1"}, {}) == []
    assert sg.avaliar_hashes({"/novo": "1"}, {"/a": "1"}) == []


@pytest.mark.parametrize("caminho, servico", [
    ("/etc/postfix/main.cf", "smtp"), ("/etc/unbound/unbound.conf", "dns"), ("/etc/mysql/my.cnf", "db"),
    ("/etc/apache2/apache2.conf", "web"), ("/var/www/html/index.php", "web"), ("/etc/passwd", "host"),
])
def test_servico_do_arquivo(caminho, servico):
    assert sg.servico_do_arquivo(caminho) == servico


# ---------------------------------------------------------------- repeticao
@pytest.mark.parametrize("novo, ultimo, emite", [
    ("ATENCAO", None, True), ("CRITICO", None, True), ("CRITICO", "ATENCAO", True),
    ("ATENCAO", "ATENCAO", False), ("ATENCAO", "CRITICO", False), ("CRITICO", "CRITICO", False),
])
def test_so_emite_quando_o_nivel_sobe(novo, ultimo, emite):
    assert sg.deve_emitir(novo, ultimo) is emite


def test_alerta_para_o_notificador_tem_os_campos_que_ele_usa():
    e = sg.EventoSeguranca("AUTENTICACAO", "web", "CRITICO", "10.0.0.9", "25 falhas em 60 s", 25.0, 20.0)
    a = sg.alerta_do_evento(e, 1795036800)
    for campo in ("ts", "servico", "metrica", "nivel_anterior", "nivel_novo", "valor", "limite"):
        assert campo in a
    assert a["metrica"] == "seguranca.autenticacao" and a["nivel_novo"] == "CRITICO" and a["detalhe"]
