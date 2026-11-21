"""API Flask (camada 3): unico ponto de entrada e saida de dados.

O Coletor so escreve por aqui (POST /api/ingest) e o dashboard so le por aqui.
Ao receber um lote, a API grava as amostras, avalia as regras de alerta e
dispara o e-mail de cada mudanca de nivel.
"""

from __future__ import annotations

import os
import smtplib
import time
from pathlib import Path

from flask import Flask, jsonify, request

from plataforma.contrato import config
from plataforma.contrato.metricas import SEM_DADOS, ErroContrato, servico_da_metrica, validar_lote
from plataforma.dominio import seguranca
from plataforma.dominio.alertas import avaliar, pior_nivel, regra_de_dict
from plataforma.infra import notificador
from plataforma.infra.banco import Banco


def _validar_leitura_seguranca(dados: object) -> tuple[int, list[dict], dict[str, str] | None]:
    """Valida o corpo de POST /api/seguranca/leitura (campos `auth` e `hashes` do agente)."""
    if not isinstance(dados, dict):
        raise ErroContrato("a leitura precisa ser um objeto JSON")
    ts = dados.get("ts")
    if not isinstance(ts, int) or isinstance(ts, bool) or ts <= 0:
        raise ErroContrato("'ts' precisa ser um inteiro positivo (epoch UTC em segundos)")
    auth = dados.get("auth", [])
    if not isinstance(auth, list):
        raise ErroContrato("'auth' precisa ser uma lista")
    for i, a in enumerate(auth):
        if not isinstance(a, dict):
            raise ErroContrato(f"auth {i}: precisa ser um objeto")
        if not isinstance(a.get("ts"), int) or isinstance(a.get("ts"), bool):
            raise ErroContrato(f"auth {i}: 'ts' precisa ser inteiro")
        if not isinstance(a.get("origem"), str) or not a["origem"]:
            raise ErroContrato(f"auth {i}: 'origem' precisa ser texto")
        if not isinstance(a.get("usuario"), str):
            raise ErroContrato(f"auth {i}: 'usuario' precisa ser texto")
        if not isinstance(a.get("sucesso"), bool):
            raise ErroContrato(f"auth {i}: 'sucesso' precisa ser verdadeiro ou falso")
    hashes = dados.get("hashes")
    if hashes is not None:
        if not isinstance(hashes, dict) or not all(
                isinstance(k, str) and isinstance(v, str) and v for k, v in hashes.items()):
            raise ErroContrato("'hashes' precisa ser um objeto caminho -> hash (texto)")
    return ts, auth, hashes


def criar_app(caminho_banco: Path, token: str) -> Flask:
    app = Flask(__name__)
    banco = Banco(caminho_banco)
    regras = {m: regra_de_dict(m, d) for m, d in config.regras_alerta().items()}
    servicos = [s.nome for s in config.servicos_monitorados()]

    def _avisar(evento: seguranca.EventoSeguranca, ts: int) -> None:
        """Grava o evento e manda o e-mail (a falha do e-mail e registrada, o evento fica gravado)."""
        banco.registrar_evento(ts, evento.tipo, evento.servico, evento.nivel, evento.origem, evento.detalhe)
        try:
            notificador.enviar(seguranca.alerta_do_evento(evento, ts))
        except (OSError, smtplib.SMTPException, KeyError, ValueError) as erro:
            app.logger.error("falha ao enviar e-mail do evento de seguranca %s: %s", evento.tipo, type(erro).__name__)

    def _avisar_se_o_nivel_subiu(evento: seguranca.EventoSeguranca, ts: int) -> int:
        recentes = banco.eventos_recentes(evento.tipo, evento.servico, evento.origem, ts - seguranca.COOLDOWN_S)
        ultimo = seguranca.maior_nivel([e["nivel"] for e in recentes])
        if not seguranca.deve_emitir(evento.nivel, ultimo):
            return 0
        _avisar(evento, ts)
        return 1

    def _avisar_config_nova(evento: seguranca.EventoSeguranca, ts: int) -> int:
        """Alteracao de arquivo: avisa uma vez por mudanca (o hash alterado continua diferente para sempre)."""
        antigos = banco.eventos_recentes(evento.tipo, evento.servico, evento.origem, 0)
        if any(e["detalhe"] == evento.detalhe for e in antigos):
            return 0
        _avisar(evento, ts)
        return 1

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
            piso = seguranca.PISO_DESVIO_TRAFEGO.get(a.metrica)
            if piso is not None:  # DDoS: escore z contra a ultima hora (sem o ponto atual)
                historico = [p["valor"] for p in banco.serie(a.metrica, lote.ts - 3600, lote.ts - 1)]
                evento = seguranca.avaliar_trafego(a.servico, a.metrica, historico, a.valor, piso)
                if evento is not None:
                    _avisar_se_o_nivel_subiu(evento, lote.ts)
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

    @app.post("/api/seguranca/leitura")
    def seguranca_leitura():
        """O Coletor repassa o que o agente leu: tentativas de login (`auth`) e hashes de arquivos (`hashes`)."""
        if request.headers.get("X-Token") != token:
            return jsonify(erro="token ausente ou invalido"), 401
        try:
            ts, auth, hashes = _validar_leitura_seguranca(request.get_json(silent=True))
        except ErroContrato as erro:
            return jsonify(erro=str(erro)), 400

        novos = 0
        if auth:
            banco.registrar_tentativas(auth)
        falhas = banco.falhas_por_ip(ts - seguranca.JANELA_LOGIN_S, ts)
        for evento in seguranca.avaliar_login(falhas):
            novos += _avisar_se_o_nivel_subiu(evento, ts)
        if hashes is not None:
            banco.salvar_hashes(ts, hashes)
            for evento in seguranca.avaliar_hashes(hashes, banco.linha_base()):
                novos += _avisar_config_nova(evento, ts)
        return jsonify(eventos=novos), 201

    @app.post("/api/seguranca/linha-base")
    def seguranca_linha_base():
        """Aceita os hashes atuais como linha de base (rodar com o sistema limpo, ou depois de uma mudanca legitima)."""
        if request.headers.get("X-Token") != token:
            return jsonify(erro="token ausente ou invalido"), 401
        arquivos = banco.definir_linha_base(int(time.time()))
        if arquivos == 0:
            return jsonify(erro="nenhuma leitura de hashes recebida ainda"), 409
        return jsonify(arquivos=arquivos)

    @app.get("/api/seguranca")
    def seguranca_consulta():
        try:
            limite = int(request.args.get("limite", 50))
        except ValueError:
            return jsonify(erro="'limite' precisa ser inteiro"), 400
        return jsonify(eventos=banco.eventos_seguranca(limite), linha_base=banco.linha_base_detalhada())

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
