"""API Flask (camada 3): unico ponto de entrada e saida de dados.

O Coletor so escreve por aqui (POST /api/ingest) e o dashboard so le por aqui.
Ao receber um lote, a API grava as amostras, avalia as regras de alerta e
dispara o e-mail de cada mudanca de nivel.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from flask import Flask, jsonify, request

from plataforma.contrato import config
from plataforma.contrato.metricas import SEM_DADOS, ErroContrato, servico_da_metrica, validar_lote
from plataforma.dominio.alertas import avaliar, pior_nivel, regra_de_dict
from plataforma.infra import notificador
from plataforma.infra.banco import Banco


def criar_app(caminho_banco: Path, token: str) -> Flask:
    app = Flask(__name__)
    banco = Banco(caminho_banco)
    regras = {m: regra_de_dict(m, d) for m, d in config.regras_alerta().items()}
    servicos = [s.nome for s in config.servicos_monitorados()]

    @app.post("/api/ingest")
    def ingest():
        if request.headers.get("X-Token") != token:
            return jsonify(erro="token ausente ou invalido"), 401
        try:
            lote = validar_lote(request.get_json(silent=True))
        except ErroContrato as erro:
            return jsonify(erro=str(erro)), 400

        banco.gravar_lote(lote)
        for a in lote.amostras:
            regra = regras.get(a.metrica)
            if regra is None:
                continue
            anterior = banco.ler_estado(a.metrica)
            novo, mudou = avaliar(regra, anterior, a.valor)
            banco.salvar_estado(a.metrica, a.servico, novo, lote.ts, mudou)
            if mudou:
                limite = regra.critico if novo.nivel == "CRITICO" else regra.atencao
                alerta = dict(ts=lote.ts, servico=a.servico, metrica=a.metrica,
                              nivel_anterior=anterior.nivel, nivel_novo=novo.nivel,
                              valor=a.valor, limite=limite)
                alerta_id = banco.registrar_alerta(**alerta)
                try:
                    notificador.enviar(alerta)
                    banco.marcar_email_enviado(alerta_id)
                except Exception as erro:  # o alerta fica gravado com email_enviado = 0
                    app.logger.error("falha ao enviar e-mail do alerta %s: %s", alerta_id, type(erro).__name__)
        return jsonify(gravadas=len(lote.amostras)), 201

    @app.get("/api/status")
    def status():
        por_servico: dict[str, list[dict]] = {s: [] for s in servicos}
        for e in banco.estados():
            por_servico.setdefault(e["servico"], []).append(e)
        resposta = []
        for servico, estados in por_servico.items():
            if not estados:
                resposta.append(dict(servico=servico, nivel=SEM_DADOS, pior_metrica=None))
                continue
            nivel = pior_nivel([e["nivel"] for e in estados])
            pior = next((e["metrica"] for e in estados if e["nivel"] == nivel and nivel != "OK"), None)
            resposta.append(dict(servico=servico, nivel=nivel, pior_metrica=pior))
        return jsonify(atualizado_em=banco.ultimo_ts(), servicos=resposta)

    @app.get("/api/metricas")
    def metricas():
        metrica = request.args.get("metrica")
        if not metrica:
            return jsonify(erro="parametro 'metrica' obrigatorio"), 400
        agora = int(time.time())
        desde = int(request.args.get("desde", agora - 3600))
        ate = int(request.args.get("ate", agora))
        return jsonify(metrica=metrica, servico=servico_da_metrica(metrica),
                       pontos=banco.serie(metrica, desde, ate))

    @app.get("/api/alertas")
    def alertas():
        return jsonify(alertas=banco.alertas(int(request.args.get("limite", 50))))

    @app.get("/api/saude")
    def saude():
        ultimo = banco.ultimo_ts()
        ok = ultimo is not None and time.time() - ultimo <= 60
        return jsonify(ok=ok, ultima_coleta=ultimo), (200 if ok else 503)

    return app


def app_do_ambiente() -> Flask:
    config.carregar_env()
    banco = os.environ.get("MONITOR_DB") or str(config.raiz_do_projeto() / "dados" / "metricas.db")
    return criar_app(Path(banco), os.environ["MONITOR_TOKEN"])
