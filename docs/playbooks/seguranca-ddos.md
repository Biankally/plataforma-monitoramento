# Segurança: tráfego anormal (DDoS)

Evento `TRAFEGO` em `GET /api/seguranca`, sobre `web.rps` (serviço web) e `dns.qps` (serviço dns).

## Sintoma
- Escore z do valor atual contra a última hora: **ATENÇÃO** z ≥ 3, **CRÍTICO** z ≥ 5 (o detalhe do evento traz valor,
  média, desvio e z). Só aumento conta; o desvio tem piso de 5 para não disparar com tráfego ocioso.
- Costuma vir junto com `web.conexoes_ativas`, `web.latencia_ms`, `host.cpu_pct` ou `dns.qps` subindo.
- O aviso não se repete enquanto o ataque continua no mesmo nível (a cada 5 min ou se o nível subir).
- Sem 20 amostras de histórico (primeiros 5 min) a detecção não roda.

## Diagnóstico
1. Confirme no dashboard: `web.rps` ou `dns.qps` realmente saltou? Foi um teste do laboratório (P1 roda scripts de ataque)?
2. Origem: `dc logs web | awk '{print $1}' | sort | uniq -c | sort -rn | head` (IPs mais frequentes); para DNS, `tcpdump -ni any udp port 1053 -c 200`.
3. Alvo: que URL é pedida? Muitas requisições à mesma página, a `login.php` ou ao `/server-status`?
4. Impacto: `web.latencia_ms`, `web.taxa_erro_5xx_pct`, `host.cpu_pct`, e se os outros serviços seguem OK (o isolamento por
   limites de container deve segurar).

## Ação
- Registre horário, origem e impacto em `docs/LOG.md` (evidência para o relatório).
- Bloqueio da origem no firewall do host e ajustes do Apache/Unbound: com P1 (infra).
- Se for teste do laboratório, deixe o ataque terminar, confirme que os alertas voltam a OK e guarde as capturas.
- Se a linha de base ficou "contaminada" por um ataque longo, os próximos ataques de mesmo tamanho podem não disparar:
  isso se corrige sozinho depois de 1 h sem ataque.
