# Runbook — dns (Unbound)

- **Container:** `monitoramento-dns-1` · **Porta:** `127.0.0.1:1053` (UDP e TCP) · **Limites:** 0,5 CPU, 256 MB, 100 processos
- **Configuração:** `servicos/dns/unbound.conf`: zona local `lab.local`, com `teste.lab.local → 192.0.2.10`
- **Estatísticas:** `unbound-control` dentro do container (o agente usa `stats_noreset`, que não zera os contadores)

Todos os comandos são rodados dentro de `servicos/`.

| Ação | Comando |
| --- | --- |
| Iniciar | `docker compose up -d dns` |
| Parar | `docker compose stop dns` |
| Reiniciar | `docker compose restart dns` |
| Reconstruir (mudou o `unbound.conf`) | `docker compose up -d --build dns` |

## Verificar
```bash
python -c "import dns.resolver as r; x=r.Resolver(configure=False); x.nameservers=['127.0.0.1']; x.port=1053; print(x.resolve('teste.lab.local','A')[0])"
# esperado: 192.0.2.10
docker compose exec dns unbound-control -c /etc/unbound/unbound.conf stats_noreset | grep total.num.queries
```

## Problemas
| Sintoma | O que fazer |
| --- | --- |
| Consulta dá timeout | `docker compose ps dns`; `docker compose logs dns` (erro de sintaxe aparece lá) |
| Mudança no `unbound.conf` não fez efeito | O arquivo é copiado na construção: use `up -d --build dns` |
| Alerta de alteração de configuração no DNS | Alguém mexeu em `/etc/unbound/unbound.conf` dentro do container: compare com o do repositório e reconstrua |
