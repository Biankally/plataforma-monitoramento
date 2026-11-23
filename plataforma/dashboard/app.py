"""Dashboard em Streamlit (camada 4). So le dados pela API.

Paginas: visao geral (um cartao por servico), por servico (todas as metricas do catalogo, com unidade,
cor e grafico), alertas (GET /api/alertas) e seguranca (GET /api/seguranca).
Responsivo: as colunas do Streamlit empilham sozinhas em telas estreitas (celular).

Rodar: streamlit run plataforma/dashboard/app.py
(a raiz do projeto entra no sys.path abaixo, para o import funcionar de qualquer pasta)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import requests  # noqa: E402
import streamlit as st  # noqa: E402

from plataforma.contrato import config  # noqa: E402
from plataforma.contrato.metricas import METRICAS, SERVICOS  # noqa: E402
from plataforma.dashboard import formatos  # noqa: E402

config.carregar_env()
API = os.environ.get("MONITOR_API_URL", "http://127.0.0.1:5000")
REGRAS = config.regras_alerta()  # limites de config/regras.toml (so para mostrar na ajuda dos cartoes)
PAGINAS = ["Visão geral", "Por serviço", "Alertas", "Segurança"]
CARTOES_POR_LINHA = 3
LEGENDA = "🟢 OK · 🟡 Atenção · 🔴 Crítico · ⚪ Sem dados · 🔵 Informativa (sem regra de alerta)"
TIPOS_SEGURANCA = {
    "TRAFEGO": "Tráfego anômalo (DDoS)",
    "AUTENTICACAO": "Falhas de login (força bruta)",
    "CONFIGURACAO": "Arquivo de configuração alterado",
    "VULNERABILIDADE": "Vulnerabilidade conhecida",
}


class ApiIndisponivel(Exception):
    """A API nao respondeu ou respondeu algo que nao e JSON."""


def ler(rota: str, **params) -> dict:
    """GET na API. Qualquer falha vira ApiIndisponivel, que cada pagina mostra como erro na tela."""
    try:
        resposta = requests.get(f"{API}{rota}", params=params, timeout=5)
        resposta.raise_for_status()
        return resposta.json()
    except (requests.RequestException, ValueError) as erro:
        raise ApiIndisponivel(f"API indisponível em {API} ({type(erro).__name__})") from erro


def em_linhas(itens: list, tamanho: int) -> list[list]:
    return [itens[i:i + tamanho] for i in range(0, len(itens), tamanho)]


# ---------------------------------------------------------------- paginas


@st.fragment(run_every="15s")
def visao_geral() -> None:
    try:
        dados = ler("/api/status")
        alertas = ler("/api/alertas", limite=5)["alertas"]
    except ApiIndisponivel as erro:
        st.error(str(erro))
        return
    st.caption(f"Última coleta: {formatos.hora(dados['atualizado_em'])} · atualiza a cada 15 s")
    servicos = dados["servicos"]
    for coluna, s in zip(st.columns(len(servicos) or 1), servicos):
        coluna.metric(s["servico"].upper(), formatos.com_icone(s["nivel"]),
                      help=f"Pior métrica: {s['pior_metrica']}" if s["pior_metrica"] else "todas as métricas normais")
    st.subheader("Últimos alertas")
    tabela_alertas(alertas)


@st.fragment(run_every="15s")
def pagina_servico(servico: str) -> None:
    metricas = [m for m in METRICAS if m.startswith(servico + ".")]
    try:
        niveis = formatos.nivel_por_metrica(ler("/api/alertas", limite=1000)["alertas"])
        series = {m: ler("/api/metricas", metrica=m)["pontos"] for m in metricas}
    except ApiIndisponivel as erro:
        st.error(str(erro))
        return
    st.caption("Última hora · atualiza a cada 15 s · passe o mouse no ⓘ para ver a descrição e os limites")
    for linha in em_linhas(metricas, CARTOES_POR_LINHA):
        for coluna, metrica in zip(st.columns(CARTOES_POR_LINHA), linha):
            with coluna, st.container(border=True):
                cartao_metrica(metrica, series[metrica], niveis)


def cartao_metrica(metrica: str, pontos: list[dict], niveis: dict[str, str]) -> None:
    unidade, descricao = METRICAS[metrica]
    nivel = formatos.nivel_exibido(metrica, bool(pontos), niveis, set(REGRAS))
    valor = formatos.formatar_valor(pontos[-1]["valor"], unidade) if pontos else "sem dados"
    ajuda = f"{descricao}. {formatos.descrever_limites(REGRAS.get(metrica), unidade)}"
    st.metric(f"{formatos.icone(nivel)} {metrica} ({unidade})", valor, help=ajuda)
    if len(pontos) > 1:
        st.line_chart({"hora": [datetime.fromtimestamp(p["ts"]) for p in pontos],
                       "valor": [p["valor"] for p in pontos]}, x="hora", y="valor", x_label="", y_label=unidade, height=140)


@st.fragment(run_every="15s")
def pagina_alertas() -> None:
    try:
        alertas = ler("/api/alertas", limite=200)["alertas"]
    except ApiIndisponivel as erro:
        st.error(str(erro))
        return
    st.caption("Cada linha é uma mudança de nível de uma métrica. Toda mudança dispara um e-mail.")
    if alertas:
        criticos, atencoes, emails = st.columns(3)
        criticos.metric("🔴 Para crítico", sum(a["nivel_novo"] == "CRITICO" for a in alertas))
        atencoes.metric("🟡 Para atenção", sum(a["nivel_novo"] == "ATENCAO" for a in alertas))
        emails.metric("📧 E-mails enviados", f"{sum(a['email_enviado'] for a in alertas)} de {len(alertas)}")
    tabela_alertas(alertas)


def tabela_alertas(alertas: list[dict]) -> None:
    if not alertas:
        st.info("Nenhum alerta registrado ainda: todas as métricas seguem no nível em que começaram.")
        return
    linhas = []
    for a in alertas:
        unidade = METRICAS.get(a["metrica"], ("", ""))[0]
        limite = a["limite"]
        linhas.append({
            "Horário": formatos.hora(a["ts"]),
            "Serviço": a["servico"].upper(),
            "Métrica": a["metrica"],
            "De": formatos.com_icone(a["nivel_anterior"]),
            "Para": formatos.com_icone(a["nivel_novo"]),
            "Valor": formatos.formatar_valor(a["valor"], unidade),
            "Limite": "—" if limite is None or unidade == "0/1" else formatos.formatar_valor(limite, unidade),
            "E-mail": "✅" if a["email_enviado"] else "❌",
        })
    st.dataframe(linhas, hide_index=True)


@st.fragment(run_every="15s")
def pagina_seguranca() -> None:
    try:
        dados = ler("/api/seguranca", limite=200)
    except ApiIndisponivel as erro:
        st.error(str(erro))
        return
    eventos, linha_base = dados["eventos"], dados["linha_base"]
    st.caption("Escore z de tráfego (DDoS), falhas de login por IP em 60 s (força bruta), hash de arquivos "
               "de configuração comparado com a linha de base e versão de cada programa comparada com a lista "
               "de CVEs conhecidos (config/vulnerabilidades.toml).")
    for linha in em_linhas(list(TIPOS_SEGURANCA.items()), 2):
        for coluna, (tipo, nome) in zip(st.columns(2), linha):
            coluna.metric(nome, sum(e["tipo"] == tipo for e in eventos))

    st.subheader("Eventos")
    if eventos:
        st.dataframe([{
            "Horário": formatos.hora(e["ts"]),
            "Tipo": e["tipo"],
            "Serviço": e["servico"].upper(),
            "Nível": formatos.com_icone(e["nivel"]),
            "Origem": e["origem"] or "—",
            "Detalhe": e["detalhe"],
        } for e in eventos], hide_index=True)
    else:
        st.info("Nenhum evento de segurança registrado.")

    st.subheader("Versões dos programas (vulnerabilidade conhecida)")
    versoes = dados.get("versoes") or []
    if versoes:
        com_falha = {e["origem"] for e in eventos if e["tipo"] == "VULNERABILIDADE"}
        st.dataframe([{"Serviço": v["servico"].upper(), "Programa": v["programa"], "Versão": v["versao"],
                       "CVE conhecido": "⚠️ sim" if f"{v['programa']} {v['versao']}" in com_falha else "não",
                       "Lida em": formatos.hora(v["ts"])} for v in versoes], hide_index=True)
    else:
        st.info("Nenhuma versão recebida ainda (o agente envia a cada ciclo do coletor).")

    st.subheader("Linha de base dos arquivos de configuração")
    if linha_base:
        st.dataframe([{"Arquivo": b["caminho"], "Hash (SHA-256)": b["hash"][:16] + "…",
                       "Aceito em": formatos.hora(b["desde"])} for b in linha_base], hide_index=True)
    else:
        st.info("Linha de base ainda não definida: com o sistema limpo, rode "
                "`curl -X POST -H \"X-Token: $MONITOR_TOKEN\" <API>/api/seguranca/linha-base`.")


# ---------------------------------------------------------------- montagem da tela

st.set_page_config(page_title="Plataforma de Monitoramento", layout="wide")
st.title("Plataforma de Monitoramento")
st.caption(LEGENDA)
pagina = st.radio("Página", PAGINAS, horizontal=True, key="pagina", label_visibility="collapsed")

if pagina == "Visão geral":
    visao_geral()
elif pagina == "Por serviço":
    servico = st.selectbox("Serviço", SERVICOS, key="servico", format_func=str.upper)
    pagina_servico(servico)
elif pagina == "Alertas":
    pagina_alertas()
else:
    pagina_seguranca()
