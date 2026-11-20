"""Teste da infraestrutura real (containers da P1).

So roda quando os containers estao no ar e voce pede:  MONITOR_INFRA=1 pytest tests/test_infra.py
Fora disso e pulado (no GitHub Actions nao ha containers).

Sabotagem manual: `docker compose stop db` dentro de servicos/ -> este teste tem que falhar.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

import pytest

from plataforma.contrato import config
from plataforma.infra.coletor import medir

pytestmark = pytest.mark.skipif(os.environ.get("MONITOR_INFRA") != "1",
                                reason="defina MONITOR_INFRA=1 com os containers no ar")

CONTAINERS = ["web", "db", "dns", "smtp"]


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
