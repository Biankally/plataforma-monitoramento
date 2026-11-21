"""Banco de metricas em SQLite (camada 2).

Uma conexao por operacao (seguro com o Flask atendendo varias requisicoes) e
modo WAL, para o dashboard ler enquanto o Coletor grava.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from plataforma.contrato.metricas import Lote
from plataforma.dominio.alertas import Estado

ESQUEMA = """
CREATE TABLE IF NOT EXISTS amostra (
  id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, servico TEXT NOT NULL,
  metrica TEXT NOT NULL, valor REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_amostra_metrica_ts ON amostra (metrica, ts);
CREATE TABLE IF NOT EXISTS estado_alerta (
  metrica TEXT PRIMARY KEY, servico TEXT NOT NULL,
  nivel TEXT NOT NULL CHECK (nivel IN ('OK','ATENCAO','CRITICO')),
  desde INTEGER NOT NULL, seq_violacao INTEGER NOT NULL DEFAULT 0,
  seq_normal INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS alerta (
  id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, servico TEXT NOT NULL,
  metrica TEXT NOT NULL, nivel_anterior TEXT NOT NULL, nivel_novo TEXT NOT NULL,
  valor REAL NOT NULL, limite REAL, email_enviado INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS evento_seguranca (
  id INTEGER PRIMARY KEY, ts INTEGER NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('TRAFEGO','AUTENTICACAO','CONFIGURACAO','VULNERABILIDADE')),
  servico TEXT NOT NULL, nivel TEXT NOT NULL CHECK (nivel IN ('ATENCAO','CRITICO')),
  origem TEXT, detalhe TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_evento_tipo_servico_ts ON evento_seguranca (tipo, servico, ts);
CREATE TABLE IF NOT EXISTS tentativa_login (
  id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, origem TEXT NOT NULL,
  usuario TEXT NOT NULL, sucesso INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS idx_tentativa_ts ON tentativa_login (ts);
CREATE TABLE IF NOT EXISTS hash_arquivo (
  caminho TEXT PRIMARY KEY, atual TEXT NOT NULL, ts_atual INTEGER NOT NULL,
  base TEXT, desde_base INTEGER);
"""


class Banco:
    def __init__(self, caminho: Path) -> None:
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self._conectar() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.executescript(ESQUEMA)

    def _conectar(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.caminho, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    # --- escrita ---
    def gravar_lote(self, lote: Lote) -> None:
        with self._conectar() as c:
            c.executemany(
                "INSERT INTO amostra (ts, servico, metrica, valor) VALUES (?, ?, ?, ?)",
                [(lote.ts, a.servico, a.metrica, a.valor) for a in lote.amostras],
            )

    def salvar_estado(self, metrica: str, servico: str, estado: Estado, ts: int, mudou: bool) -> None:
        with self._conectar() as c:
            anterior = c.execute("SELECT desde FROM estado_alerta WHERE metrica = ?", (metrica,)).fetchone()
            desde = ts if (mudou or anterior is None) else anterior["desde"]
            c.execute(
                "INSERT OR REPLACE INTO estado_alerta VALUES (?, ?, ?, ?, ?, ?)",
                (metrica, servico, estado.nivel, desde, estado.seq_violacao, estado.seq_normal),
            )

    def registrar_alerta(self, ts: int, servico: str, metrica: str, nivel_anterior: str,
                         nivel_novo: str, valor: float, limite: float | None) -> int:
        with self._conectar() as c:
            cur = c.execute(
                "INSERT INTO alerta (ts, servico, metrica, nivel_anterior, nivel_novo, valor, limite)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ts, servico, metrica, nivel_anterior, nivel_novo, valor, limite),
            )
            return int(cur.lastrowid)

    def marcar_email_enviado(self, alerta_id: int) -> None:
        with self._conectar() as c:
            c.execute("UPDATE alerta SET email_enviado = 1 WHERE id = ?", (alerta_id,))

    # --- leitura ---
    def ler_estado(self, metrica: str) -> Estado:
        with self._conectar() as c:
            r = c.execute("SELECT * FROM estado_alerta WHERE metrica = ?", (metrica,)).fetchone()
        return Estado(r["nivel"], r["seq_violacao"], r["seq_normal"]) if r else Estado()

    def estados(self) -> list[dict]:
        with self._conectar() as c:
            return [dict(r) for r in c.execute("SELECT * FROM estado_alerta")]

    def serie(self, metrica: str, desde: int, ate: int) -> list[dict]:
        with self._conectar() as c:
            q = "SELECT ts, valor FROM amostra WHERE metrica = ? AND ts BETWEEN ? AND ? ORDER BY ts"
            return [dict(r) for r in c.execute(q, (metrica, desde, ate))]

    def alertas(self, limite: int = 50) -> list[dict]:
        with self._conectar() as c:
            q = "SELECT * FROM alerta ORDER BY id DESC LIMIT ?"
            return [dict(r) for r in c.execute(q, (limite,))]

    def ultimo_ts(self) -> int | None:
        with self._conectar() as c:
            r = c.execute("SELECT MAX(ts) AS m FROM amostra").fetchone()
        return r["m"]

    def apagar_antigas(self, dias: int = 7) -> None:
        with self._conectar() as c:
            c.execute("DELETE FROM amostra WHERE ts < ?", (int(time.time()) - dias * 86400,))

    # --- seguranca ---
    def registrar_evento(self, ts: int, tipo: str, servico: str, nivel: str, origem: str | None,
                         detalhe: str) -> int:
        with self._conectar() as c:
            cur = c.execute(
                "INSERT INTO evento_seguranca (ts, tipo, servico, nivel, origem, detalhe) VALUES (?, ?, ?, ?, ?, ?)",
                (ts, tipo, servico, nivel, origem, detalhe),
            )
            return int(cur.lastrowid)

    def eventos_seguranca(self, limite: int = 50) -> list[dict]:
        with self._conectar() as c:
            q = "SELECT * FROM evento_seguranca ORDER BY id DESC LIMIT ?"
            return [dict(r) for r in c.execute(q, (limite,))]

    def eventos_recentes(self, tipo: str, servico: str, origem: str | None, desde: int) -> list[dict]:
        """Eventos do mesmo tipo, servico e origem (None = sem origem) a partir de `desde`."""
        with self._conectar() as c:
            q = ("SELECT * FROM evento_seguranca WHERE tipo = ? AND servico = ? AND ts >= ?"
                 " AND COALESCE(origem, '') = COALESCE(?, '') ORDER BY id DESC")
            return [dict(r) for r in c.execute(q, (tipo, servico, desde, origem))]

    def registrar_tentativas(self, tentativas: list[dict]) -> None:
        with self._conectar() as c:
            c.executemany(
                "INSERT INTO tentativa_login (ts, origem, usuario, sucesso) VALUES (?, ?, ?, ?)",
                [(t["ts"], t["origem"], t["usuario"], 1 if t["sucesso"] else 0) for t in tentativas],
            )

    def falhas_por_ip(self, desde: int, ate: int) -> dict[str, int]:
        with self._conectar() as c:
            q = ("SELECT origem, COUNT(*) AS n FROM tentativa_login"
                 " WHERE sucesso = 0 AND ts BETWEEN ? AND ? GROUP BY origem")
            return {r["origem"]: r["n"] for r in c.execute(q, (desde, ate))}

    def salvar_hashes(self, ts: int, hashes: dict[str, str]) -> None:
        with self._conectar() as c:
            c.executemany(
                "INSERT INTO hash_arquivo (caminho, atual, ts_atual) VALUES (?, ?, ?)"
                " ON CONFLICT(caminho) DO UPDATE SET atual = excluded.atual, ts_atual = excluded.ts_atual",
                [(caminho, h, ts) for caminho, h in hashes.items()],
            )

    def definir_linha_base(self, ts: int) -> int:
        """Aceita os hashes atuais como linha de base. Devolve quantos arquivos."""
        with self._conectar() as c:
            return c.execute("UPDATE hash_arquivo SET base = atual, desde_base = ?", (ts,)).rowcount

    def linha_base(self) -> dict[str, str]:
        with self._conectar() as c:
            return {r["caminho"]: r["base"] for r in c.execute(
                "SELECT caminho, base FROM hash_arquivo WHERE base IS NOT NULL ORDER BY caminho")}

    def linha_base_detalhada(self) -> list[dict]:
        with self._conectar() as c:
            return [dict(r) for r in c.execute(
                "SELECT caminho, base AS hash, desde_base AS desde FROM hash_arquivo"
                " WHERE base IS NOT NULL ORDER BY caminho")]
