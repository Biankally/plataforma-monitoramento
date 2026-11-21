# Erros HTTP no site

Métricas: `web.taxa_erro_4xx_pct`, `web.taxa_erro_5xx_pct`, `web.conexoes_ativas` (e as contagens `web.req_4xx`, `web.req_5xx`).

## Sintoma
- 4xx: ATENÇÃO > 20 %, CRÍTICO > 50 % das requisições da janela. Costuma ser cliente errado ou varredura: 404 em massa
  (procura de páginas), 401/403 (tentativas de acesso).
- 5xx: ATENÇÃO > 2 %, CRÍTICO > 10 %. É falha do **servidor**: PHP com erro, banco indisponível, falta de workers.
- Conexões ativas: ATENÇÃO > 100, CRÍTICO > 180 (Apache esgotando workers; o container tem limite de 200 processos).
- As taxas são calculadas sobre o log da janela; sem requisições na janela a taxa não existe (não é zero).

## Diagnóstico
1. 5xx: `dc logs web | grep -E ' 50[0-9] '` e o log de erros do PHP. Erro de conexão com o banco? Veja `db.disponivel`.
2. 4xx: quais URLs e de quais IPs? `dc exec web sh -c "awk '{print \$1, \$9, \$7}' /var/log/apache2/access.log | sort | uniq -c | sort -rn | head"`
   (ajuste o caminho do log). Muitos 404 de um IP só = varredura; muitos 401/403 em `login.php` = ver `seguranca-forca-bruta.md`.
3. Conexões altas: `web.rps` subiu junto? Então é carga ou DDoS (`seguranca-ddos.md`). Se não subiu, conexões estão
   presas (lentas): veja `latencia-alta.md` e o banco.
4. Mudança recente no site ou na configuração? Veja eventos `CONFIGURACAO`.

## Ação
- 5xx por banco: restaure o banco (`servico-indisponivel.md`) e confirme que o site volta a responder.
- 5xx por código: reverta a alteração do site (git) e reinicie `dc restart web`.
- Varredura (4xx de um IP): registre o IP; o bloqueio por firewall do host fica a cargo de P1.
- Excesso de conexões legítimas: avalie `MaxRequestWorkers` e o limite do container, com o grupo.
