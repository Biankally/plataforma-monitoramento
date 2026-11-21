# DNS: erros e volume de consultas

Métricas: `dns.taxa_erro_pct`, `dns.qps` (a indisponibilidade está em `servico-indisponivel.md`).

## Sintoma
- Taxa de erro: ATENÇÃO > 5 %, CRÍTICO > 20 % = (SERVFAIL + REFUSED + falhas da sonda) sobre o total de consultas da
  janela. SERVFAIL = o Unbound não conseguiu resolver; REFUSED = recusou (cliente fora do `access-control`).
- Volume: ATENÇÃO > 100, CRÍTICO > 500 consultas por segundo. Em laboratório isso é muito acima do normal e indica
  inundação de consultas (DDoS ou amplificação).
- NXDOMAIN **não** conta como erro de serviço (nome inexistente é resposta válida).

## Diagnóstico
1. Estatísticas do Unbound: `dc exec dns unbound-control stats_noreset | grep -E 'num.answer.rcode|total.num.queries|num.query.type'`.
2. SERVFAIL: `dc logs dns` (falha de resolução, zona `lab.local` quebrada: `dc exec dns unbound-checkconf`).
3. REFUSED: o cliente está dentro do `access-control` do `unbound.conf`? Fonte nova de consultas?
4. Volume alto: de quem? Ative log de consultas temporariamente (`log-queries: yes`) ou use `tcpdump -ni any udp port 1053 -c 200`
   e veja IPs e nomes repetidos. Compare com eventos `TRAFEGO` em `/api/seguranca`.

## Ação
- Configuração quebrada: restaure o `unbound.conf` e `dc restart dns`.
- Inundação: trate como ataque (`seguranca-ddos.md`); mantenha `access-control` restrito (nada de resolvedor aberto).
- Erros por origem legítima nova: adicione a rede ao `access-control` com o grupo.
