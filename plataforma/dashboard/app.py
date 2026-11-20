"""Dashboard em Streamlit (camada 4). So le dados pela API.

Rodar: streamlit run plataforma/dashboard/app.py
(a raiz do projeto entra no sys.path abaixo, para o import funcionar de qualquer pasta)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import requests  # noqa: E402
import streamlit as st  # noqa: E402

from plataforma.contrato import config  # noqa: E402
from plataforma.contrato.metricas import METRICAS  # noqa: E402

config.carregar_env()
API = os.environ.get("MONITOR_API_URL", "http://127.0.0.1:5000")
CORES = {"OK": "🟢", "ATENCAO": "🟡", "CRITICO": "🔴", "SEM_DADOS": "⚪"}

st.set_page_config(page_title="Plataforma de Monitoramento", layout="wide")
st.title("Plataforma de Monitoramento")


@st.fragment(run_every="15s")
def visao_consolidada() -> None:
    try:
        dados = requests.get(f"{API}/api/status", timeout=5).json()
    except requests.RequestException:
        st.error(f"API indisponivel em {API}")
        return
    colunas = st.columns(len(dados["servicos"]) or 1)
    for coluna, s in zip(colunas, dados["servicos"]):
        coluna.metric(s["servico"].upper(), f"{CORES.get(s['nivel'], '')} {s['nivel']}",
                      help=s["pior_metrica"] or "todas as metricas normais")


@st.fragment(run_every="15s")
def detalhe(servico: str) -> None:
    for metrica in [m for m in METRICAS if m.startswith(servico + ".")]:
        try:
            pontos = requests.get(f"{API}/api/metricas", params={"metrica": metrica}, timeout=5).json()["pontos"]
        except requests.RequestException:
            st.error("API indisponivel")
            return
        if pontos:
            st.caption(f"{metrica} ({METRICAS[metrica][0]})")
            st.line_chart({"valor": [p["valor"] for p in pontos]})


visao_consolidada()
servico = st.selectbox("Servico", ["web", "db", "dns", "smtp", "host"])
detalhe(servico)
