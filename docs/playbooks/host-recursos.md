# Recursos da máquina e dos containers

Métricas: `host.cpu_pct`, `host.mem_pct`, `host.disco_io_kbs`, `host.disco_latencia_ms`.

## Sintoma
- CPU e memória: ATENÇÃO > 80 %, CRÍTICO > 95 %.
- Disco: leitura + escrita > 50 000 KB/s (atenção) e > 200 000 KB/s (crítico); latência por operação > 20 ms / > 100 ms.
- Recursos no limite derrubam ou deixam lentos os serviços (`servico-indisponivel.md`, `latencia-alta.md`) e podem fazer o
  kernel matar processos por falta de memória.

## Diagnóstico
1. Quem consome? `docker stats --no-stream` (por container) e `top` ou `htop` na máquina.
2. Um container no limite do `docker-compose.yml` (CPU 0,5/1; memória 256 MB a 1 GB) mostra uso alto **do container**, não
   da máquina inteira.
3. Memória: `docker inspect <container> --format '{{.State.OOMKilled}}'`; `dmesg | grep -i -E 'killed process|oom'`.
4. Disco: `df -h`, `docker system df`, `iostat -x 1 3`. Banco crescendo? Veja `banco-crescimento.md`.
5. Correlacione com tráfego (`web.rps`, `dns.qps`) e eventos de segurança.

## Ação
- Pico por ataque: `seguranca-ddos.md`. Pico por carga legítima: ajuste os limites do container com o grupo.
- Disco cheio: `docker system prune` (imagens e containers parados; **sem** `--volumes`) e remova logs antigos.
- Vazamento de memória em um serviço: reinicie só esse container (`dc restart <servico>`) e anote em `docs/LOG.md`.
- No WSL2, a memória do WSL tem teto no `.wslconfig` do Windows; se a máquina inteira sobe, esse teto pode ser a causa.
