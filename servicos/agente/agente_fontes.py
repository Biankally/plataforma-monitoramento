"""Fontes do agente: cada funcao busca UMA informacao de um servico e devolve um dicionario.

Regra comum: se a fonte nao responde, os campos ficam None ("sem dado") e o motivo vai para o
terminal do agente. Nunca se inventa um 0, porque 0 e um valor real (ex.: fila vazia).
O Docker e chamado por um "executor" (funcao que roda um comando e devolve a saida); nos testes
ele e trocado por um falso.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen

from agente_log import avisar

Executor = Callable[[list[str]], str]
LIMITE_LISTA = 5000   # teto de itens por leitura (protege a memoria durante um ataque)


class ErroFonte(Exception):
    """Uma fonte nao respondeu (container parado, comando falhou, tempo esgotado)."""


def executar(argv: list[str], timeout_s: float = 15.0) -> str:
    """Executor de verdade: roda o comando e devolve a saida padrao."""
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=timeout_s)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ErroFonte(f"{' '.join(argv[:3])}: {e}") from e
    if r.returncode != 0:
        raise ErroFonte(f"{' '.join(argv[:3])}: {r.stderr.strip()[:200]}")
    return r.stdout


def _numero(texto: str) -> float:
    return float(texto.strip().rstrip("%"))


# ---------- Apache (mod_status) ----------

CAMPOS_APACHE = {"Total Accesses": "total_accesses", "ConnsTotal": "conns_total", "BusyWorkers": "busy_workers"}


def apache_status(url: str) -> dict:
    """Le /server-status?auto: contador total de acessos, conexoes e workers ocupados."""
    resultado = dict.fromkeys(CAMPOS_APACHE.values())
    try:
        with urlopen(url, timeout=5) as resposta:
            texto = resposta.read().decode("utf-8", errors="replace")
    except (URLError, OSError) as e:
        avisar(f"apache sem resposta em {url}: {e}")
        return resultado
    for linha in texto.splitlines():
        chave, _, valor = linha.partition(":")
        if chave.strip() in CAMPOS_APACHE:
            resultado[CAMPOS_APACHE[chave.strip()]] = int(float(valor))
    return resultado


# ---------- log de acesso do Apache: "STATUS MICROSSEGUNDOS" por linha ----------

def resumir_log_web(linhas: list[str]) -> dict:
    por_codigo: Counter[str] = Counter()
    tempos: list[int] = []
    for linha in linhas:
        partes = linha.split()
        if len(partes) != 2 or not partes[0].isdigit() or not partes[1].isdigit():
            continue   # linha fora do formato (ex.: arquivo de outra versao); nao conta
        por_codigo[partes[0]] += 1
        tempos.append(int(partes[1]))
    return {"total": sum(por_codigo.values()), "por_codigo": dict(por_codigo),
            "tempo_servidor_us": tempos[-LIMITE_LISTA:]}


# ---------- Unbound ----------

CHAVES_UNBOUND = ["total.num.queries", "num.answer.rcode.SERVFAIL", "num.answer.rcode.REFUSED",
                  "num.answer.rcode.NXDOMAIN"]


def unbound(executor: Executor, container: str, arquivo_conf: str) -> dict:
    """Contadores acumulados do Unbound (unbound-control stats_noreset, sem zerar)."""
    try:
        texto = executor(["docker", "exec", container, "unbound-control", "-c", arquivo_conf, "stats_noreset"])
    except ErroFonte as e:
        avisar(f"unbound: {e}")
        return dict.fromkeys(CHAVES_UNBOUND)
    valores = dict(linha.split("=", 1) for linha in texto.splitlines() if "=" in linha)
    # com extended-statistics, um codigo que nunca aconteceu pode nao aparecer: isso e 0 de verdade
    return {chave: int(_numero(valores.get(chave, "0"))) for chave in CHAVES_UNBOUND}


# ---------- Postfix ----------

RE_DELAY = re.compile(r"\bdelay=([\d.]+)")


def resumir_postfix(linhas: list[str]) -> dict:
    """Conta o que aconteceu nas linhas novas do log do Postfix."""
    contagem = {"sent": 0, "deferred": 0, "bounced": 0, "rejeicoes": 0, "timeouts": 0}
    atrasos: list[float] = []
    for linha in linhas:
        for situacao in ("sent", "deferred", "bounced"):
            if f"status={situacao}" in linha:
                contagem[situacao] += 1
                achado = RE_DELAY.search(linha)
                if achado:
                    atrasos.append(float(achado.group(1)))
        if " reject: " in linha:
            contagem["rejeicoes"] += 1
        if "timeout after" in linha:
            contagem["timeouts"] += 1
    media = round(sum(atrasos) / len(atrasos), 3) if atrasos else None
    return {**contagem, "delay_medio_s": media}


def fila_postfix(executor: Executor, container: str) -> int | None:
    """postqueue -j imprime uma linha JSON por mensagem na fila."""
    try:
        texto = executor(["docker", "exec", container, "postqueue", "-j"])
    except ErroFonte as e:
        avisar(f"postfix (fila): {e}")
        return None
    return sum(1 for linha in texto.splitlines() if linha.strip().startswith("{"))


def _instante_docker(texto: str) -> tuple[datetime, int]:
    """'2026-11-20T18:00:01.1Z' -> (data ate o segundo, nanossegundos). O Docker corta zeros do fim."""
    base, _, resto = texto.rstrip("Z").partition(".")
    data = datetime.strptime(base, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    return data, int((resto or "0").ljust(9, "0")[:9])


class LeitorDockerLogs:
    """Linhas novas da saida de um container (docker logs), usando a data de cada linha como marca."""

    def __init__(self, executor: Executor, container: str) -> None:
        self.executor, self.container = executor, container
        self._ultimo: tuple[datetime, int] | None = None
        self._desde = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def linhas_novas(self) -> list[str] | None:
        try:
            texto = self.executor(["docker", "logs", "--timestamps", "--since", self._desde, self.container])
        except ErroFonte as e:
            avisar(f"postfix (log): {e}")
            return None
        novas = []
        for linha in texto.splitlines():
            marca, _, conteudo = linha.partition(" ")
            try:
                instante = _instante_docker(marca)
            except ValueError:
                continue
            if self._ultimo is None or instante > self._ultimo:
                novas.append(conteudo)
                self._ultimo = instante
        if self._ultimo is not None:
            self._desde = self._ultimo[0].strftime("%Y-%m-%dT%H:%M:%SZ")
        return novas


def postfix(executor: Executor, container: str, leitor: LeitorDockerLogs) -> dict:
    linhas = leitor.linhas_novas()
    if linhas is None:
        resumo = dict.fromkeys(["sent", "deferred", "bounced", "rejeicoes", "timeouts", "delay_medio_s"])
    else:
        resumo = resumir_postfix(linhas)
    return {"fila": fila_postfix(executor, container), **resumo}


# ---------- tentativas de login (linhas JSON do login.log) ----------

def tentativas(linhas: list[str]) -> list[dict]:
    resultado = []
    for linha in linhas:
        try:
            item = json.loads(linha)
        except json.JSONDecodeError:
            avisar(f"login.log: linha que nao e JSON ignorada: {linha[:80]}")
            continue
        if isinstance(item, dict) and {"ts", "origem", "usuario", "sucesso"} <= set(item):
            resultado.append({k: item[k] for k in ("ts", "origem", "usuario", "sucesso")})
    return resultado[-LIMITE_LISTA:]


# ---------- CPU e memoria de cada container ----------

def containers(executor: Executor, nomes: dict[str, str]) -> dict:
    """nomes: {"web": "monitoramento-web-1", ...}. Le tudo de uma vez com docker stats."""
    resultado = {curto: {"cpu_pct": None, "mem_pct": None} for curto in nomes}
    try:
        texto = executor(["docker", "stats", "--no-stream", "--format", "{{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}"])
    except ErroFonte as e:
        avisar(f"docker stats: {e}")
        return resultado
    por_nome = {completo: curto for curto, completo in nomes.items()}
    for linha in texto.splitlines():
        partes = linha.split("\t")
        if len(partes) == 3 and partes[0] in por_nome:
            resultado[por_nome[partes[0]]] = {"cpu_pct": _numero(partes[1]), "mem_pct": _numero(partes[2])}
    return resultado


# ---------- maquina (o Linux onde os containers rodam) ----------

class MedidorHost:
    """CPU, memoria e disco pelo /proc. CPU e I/O sao diferencas entre duas leituras."""

    def __init__(self, raiz_disco: str = "/") -> None:
        self.raiz_disco = raiz_disco
        self._cpu_antes = self._ler_cpu()
        self._disco_antes = (time.monotonic(), self._ler_disco())

    @staticmethod
    def _ler_cpu() -> tuple[int, int]:
        campos = [int(x) for x in Path("/proc/stat").read_text(encoding="utf-8").split("\n")[0].split()[1:]]
        ocioso = campos[3] + (campos[4] if len(campos) > 4 else 0)   # idle + iowait
        return sum(campos), ocioso

    @staticmethod
    def _ler_disco() -> tuple[int, int, int]:
        """(setores lidos + escritos, operacoes, milissegundos gastos) somando discos fisicos."""
        # /sys/block lista so os discos inteiros (sda, nvme0n1), sem as particoes (sda1)
        discos = {d.name for d in Path("/sys/block").iterdir()
                  if not d.name.startswith(("loop", "ram", "zram"))}
        setores = operacoes = ms = 0
        for linha in Path("/proc/diskstats").read_text(encoding="utf-8").splitlines():
            c = linha.split()
            if len(c) < 14 or c[2] not in discos:
                continue
            operacoes += int(c[3]) + int(c[7])
            setores += int(c[5]) + int(c[9])
            ms += int(c[6]) + int(c[10])
        return setores, operacoes, ms

    @staticmethod
    def _memoria_pct() -> float:
        info = {}
        for linha in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            chave, _, valor = linha.partition(":")
            info[chave] = int(valor.split()[0])
        return round(100 * (1 - info["MemAvailable"] / info["MemTotal"]), 1)

    def medir(self) -> dict:
        total, ocioso = self._ler_cpu()
        dt_total, dt_ocioso = total - self._cpu_antes[0], ocioso - self._cpu_antes[1]
        self._cpu_antes = (total, ocioso)
        cpu = round(100 * (1 - dt_ocioso / dt_total), 1) if dt_total > 0 else 0.0

        agora, disco = time.monotonic(), self._ler_disco()
        (antes, (setores0, ops0, ms0)), (setores1, ops1, ms1) = self._disco_antes, disco
        self._disco_antes = (agora, disco)
        intervalo = max(agora - antes, 1e-6)
        io_kbs = round((setores1 - setores0) * 512 / 1024 / intervalo, 1)
        latencia = round((ms1 - ms0) / (ops1 - ops0), 2) if ops1 > ops0 else 0.0

        uso = shutil.disk_usage(self.raiz_disco)
        return {"cpu_pct": cpu, "mem_pct": self._memoria_pct(), "disco_pct": round(100 * uso.used / uso.total, 1),
                "disco_io_kbs": io_kbs, "disco_latencia_ms": latencia}


# ---------- hash SHA-256 dos arquivos de configuracao dentro dos containers ----------

def hashes(executor: Executor, arquivos: dict[str, list[str]]) -> dict:
    """arquivos: {"monitoramento-smtp-1": ["/etc/postfix/main.cf"], ...} -> {caminho: hash ou None}."""
    def um_hash(container: str, caminho: str) -> str | None:
        try:
            return executor(["docker", "exec", container, "sha256sum", caminho]).split()[0]
        except (ErroFonte, IndexError) as e:
            avisar(f"hash de {caminho} em {container}: {e}")
            return None

    pares = [(c, caminho) for c, caminhos in arquivos.items() for caminho in caminhos]
    with ThreadPoolExecutor(max_workers=len(pares) or 1) as paralelo:   # um docker exec por arquivo, juntos
        hashes_lidos = list(paralelo.map(lambda par: um_hash(*par), pares))
    return {caminho: h for (_, caminho), h in zip(pares, hashes_lidos)}
