# LOG do projeto

Registro de toda mudança no projeto, da mais antiga para a mais nova.
**Regra:** cada mudança acrescenta uma entrada no fim deste arquivo, no mesmo commit da mudança.

Modelo de entrada:

```
## AAAA-MM-DD HH:MM — título curto
- **Quem:** nome (P1/P2/P3)
- **O que mudou:** ...
- **Por quê:** ...
- **Arquivos:** ...
- **Verificação:** comando rodado e resultado (ex.: `pytest` → 30 passed)
- **Pendências / riscos:** ...
```

---

## 2026-11-12 — Repositório criado
- **Quem:** Bia
- **O que mudou:** criação do repositório privado no GitHub, estrutura inicial de pastas, `README.md`, `CHECKLIST.md` e `.gitignore`.
- **Por quê:** organizar as entregas do enunciado desde o início.
- **Arquivos:** `README.md`, `CHECKLIST.md`, `.gitignore`, pastas com `.gitkeep`.
- **Verificação:** `git status` limpo e `origin/main` sincronizado (commit `689a1bc`).
- **Pendências / riscos:** nenhuma.

## 2026-11-18 — Plano de gerenciamento e documento de arquitetura (1ª versão)
- **Quem:** Bia
- **O que mudou:** plano baseado no PMBOK 8 (EAP com 27 pacotes, riscos, marcos M0–M5) e documento de arquitetura (visões 4+1, catálogo de métricas, modelo de dados, contrato da API, motor de alertas, segurança).
- **Por quê:** definir escopo, prazos e contrato antes do código.
- **Arquivos:** documentos externos (ainda não estão em `docs/`).
- **Verificação:** revisão de leitura (sem execução).
- **Pendências / riscos:** precisam ser atualizados para containers, Streamlit e TOML e trazidos para `docs/` em Markdown.

## 2026-11-19 — Respostas da professora
- **Quem:** Bia
- **O que mudou:** decisões confirmadas: trio permitido; repositório privado com a professora como colaboradora; infraestrutura livre (VMs ou containers), desde que um ataque não derrube outros serviços; aplicação vulnerável pronta (DVWA) permitida; uso de IA permitido.
- **Por quê:** eliminar dúvidas de requisito.
- **Arquivos:** `CHECKLIST.md` (seção 10).
- **Verificação:** respostas por escrito da professora.
- **Pendências / riscos:** falta o usuário da professora no GitHub e confirmar data/horário da apresentação.

## 2026-11-20 — Decisões de projeto
- **Quem:** Bia (coordenação)
- **O que mudou:**
  1. Serviços vigiados em **containers com limite de CPU, memória e processos** na VM-S; plataforma na VM-P.
  2. Alvo web: **site Receitas Práticas** (PHP + MySQL); DVWA como plano B se a adaptação travar até 21/11 12h.
  3. Dashboard em **Streamlit** (uma linguagem só no projeto).
  4. Configuração em **TOML** (lido pela biblioteca padrão do Python, sem dependência extra).
  5. Bibliotecas fechadas no `requirements.txt`: flask, requests, streamlit, pymysql, dnspython, pytest.
  6. Código em **camadas** (contrato → domínio → infra → api → dashboard), verificadas por teste automático.
- **Por quê:** cumprir a regra de isolamento da professora, reduzir risco no prazo de 6 dias e impedir que cada IA use uma tecnologia diferente.
- **Arquivos:** `AGENTS.md`, `requirements.txt`, `config/`.
- **Verificação:** ver entrada seguinte.
- **Pendências / riscos:** recalibrar limites de alerta com a linha de base real.

## 2026-11-20 — Esqueleto em camadas com teste termômetro
- **Quem:** Bia
- **O que mudou:** implementação mínima do fluxo completo: contrato de métricas, regras de alerta com histerese, banco SQLite, sondas HTTP/TCP, coletor, notificador (arquivo/SMTP), API Flask, dashboard Streamlit, teste de camadas, teste termômetro, GitHub Actions, `AGENTS.md`, pedidos por pessoa e guia "Comece aqui".
- **Por quê:** provar no primeiro dia que as interfaces se encaixam e rodam (integração testada no começo).
- **Arquivos:** `plataforma/**`, `tests/**`, `config/**`, `docs/ia/**`, `.github/workflows/testes.yml`, `pyproject.toml`, `requirements.txt`, `.env.exemplo`, `AGENTS.md`, `COMECE_AQUI.md`, `README.md`, `CHECKLIST.md`.
- **Verificação:**
  - `pytest` → 30 passed (no WSL da Bia, 20/11 12:53).
  - 7 sabotagens no código (alerta no 1º pico, sem atenção imediata, e-mail não enviado, API sem token, métrica inventada, import proibido, sonda sempre "no ar") → todas acusadas pelos testes.
  - Suíte rodada em pasta com acento e espaço → 30 passed.
  - Ensaio limpo (ambiente virtual novo, só `requirements.txt`) → 30 passed, 3 de 3 vezes.
- **Defeitos encontrados e corrigidos durante a verificação:**
  1. Erro 500 na API quando um alerta disparava: nome de parâmetro diferente entre a API (`nivel_anterior`) e o banco (`anterior`). Corrigido em `plataforma/infra/banco.py`.
  2. Sabotagem "sonda sempre no ar" não era acusada: faltava testar site respondendo 500. Criado `tests/test_sondas.py`.
  3. Teste instável: servidor TCP falso seguia aceitando conexão depois de derrubado (Linux). Corrigido com `shutdown()` antes de `close()` em `tests/falsos/servicos_falsos.py`; 40 de 40 execuções estáveis.
- **Pendências / riscos:** sondas de banco, DNS e SMTP ainda só testam a porta (tarefa de P2); serviços reais ainda não montados (tarefa de P1).

## 2026-11-20 — CLAUDE.md fora do repositório
- **Quem:** Bia
- **O que mudou:** `CLAUDE.md` adicionado ao `.gitignore`; cada pessoa que usar essa ferramenta cria o arquivo localmente (`echo '@AGENTS.md' > CLAUDE.md`).
- **Por quê:** manter no repositório só as regras genéricas (`AGENTS.md`).
- **Arquivos:** `.gitignore`.
- **Verificação:** `git status` sem `CLAUDE.md`.
- **Pendências / riscos:** nenhuma.

## 2026-11-20 — LOG do projeto criado
- **Quem:** Bia
- **O que mudou:** criação deste arquivo e da regra no `AGENTS.md` de registrar toda mudança aqui.
- **Por quê:** rastrear o que mudou, quando e por quê, para achar a causa se algo falhar.
- **Arquivos:** `docs/LOG.md`, `AGENTS.md`.
- **Verificação:** arquivo presente no commit.
- **Pendências / riscos:** nenhuma.

## 2026-11-20 14:30 — Divisão das partes e infraestrutura em WSL2 + Docker
- **Quem:** Bia (P1)
- **O que mudou:**
  1. Divisão: Bia fica com **P1 (Infra e Segurança)**; a sugestão de um integrante foi incorporada à **P2** (pedido em `docs/ia/pedido-p2.md`).
  2. Infraestrutura pelo **caminho B**: WSL2 (VM Linux leve) com **Docker Desktop**; a plataforma roda no WSL e os 4 serviços em containers. VirtualBox descartado (disputa de virtualização com o WSL2 e 2–3 h só de instalação).
  3. **Portas alternativas** publicadas só em 127.0.0.1: web 8080, db 3307, dns 1053, smtp 2525 (evita conflito com XAMPP nas portas 80/3306 e com o Windows nas 53/25).
- **Por quê:** prazo curto; a professora liberou containers desde que um ataque não derrube outros serviços (garantido pelos limites de CPU, memória e processos de cada container).
- **Arquivos:** `config/servicos.toml`.
- **Verificação:** ver entrada seguinte.
- **Pendências / riscos:** plataforma e serviços na mesma VM (o isolamento vem dos limites dos containers); registrar como decisão na arquitetura.

## 2026-11-20 14:30 — Infraestrutura mínima (4 containers com limites)
- **Quem:** Bia (P1)
- **O que mudou:** `docker-compose.yml` com `web` (php:8.3-apache, página provisória), `db` (mysql:8.0), `dns` (Unbound sobre Alpine, zona `lab.local`) e `smtp` (Postfix sobre Alpine), cada um com `cpus`, `mem_limit` e `pids_limit`; teste da infraestrutura real; remoção do `.gitkeep` que sobrou em `plataforma/api/`.
- **Por quê:** colocar serviços reais no ar hoje, para P2 testar as sondas, antes de adaptar o site e montar o agente.
- **Arquivos:** `servicos/docker-compose.yml`, `servicos/.env.exemplo`, `servicos/web-vuln/site/index.php`, `servicos/dns/Dockerfile`, `servicos/dns/unbound.conf`, `servicos/smtp/Dockerfile`, `servicos/smtp/main.cf`, `tests/test_infra.py`, `config/servicos.toml`.
- **Verificação (antes de subir no WSL):**
  - `docker compose config` → válido; limites lidos (web 1 CPU/512 MB/200 proc., db 1 CPU/1 GB/300, dns e smtp 0,5 CPU/256 MB/100).
  - `unbound-checkconf` → sem erros; Unbound rodando com o arquivo: `teste.lab.local` → 192.0.2.10, nome inexistente → NXDOMAIN, `unbound-control stats_noreset` mostra `total.num.queries` e `num.answer.rcode.NXDOMAIN`.
  - Postfix rodando com o `main.cf`: EHLO 250, envio aceito, log com `status=sent` e `delay=`.
  - `pytest` → 30 passed, 8 skipped (os testes de infraestrutura só rodam com `MONITOR_INFRA=1`).
- **Verificação no WSL da Bia (20/11 14:40):** 4 containers Up; `MONITOR_INFRA=1 pytest tests/test_infra.py` → 8 passed; sabotagem `docker compose stop db` → 1 failed (só o db), 7 passed; `docker compose start db` restaurou. Limitação: a sonda TCP aceita a conexão pelo encaminhamento de porta do Docker Desktop antes de o MySQL ficar pronto; as sondas reais da P2 (`SELECT 1`, consulta DNS, diálogo SMTP) resolvem.
- **Pendências / riscos:** imagens não foram baixadas no ambiente de validação (sem acesso ao Docker Hub); a subida real é conferida no WSL.

## 2026-11-20 15:10 — Site Receitas Práticas no container web e banco inicial
- **Quem:** Bia (P1, tarefas 2 e 3)
- **O que mudou:**
  1. Site copiado do XAMPP para `servicos/web-vuln/site/` **sem** a pasta `.git` e sem o `.sql` (o `.sql` virou `servicos/banco/init.sql`). Servido em `http://127.0.0.1:8080/receitas_práticas/` (mesmo caminho que os links do site já usam); a raiz `/` redireciona para lá.
  2. Conexão única com o MySQL em `site/db.php`, lendo `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME` do ambiente. As 6 conexões antigas (todas com `localhost` e `root`) agora passam por ele. O site usa o usuário `site` (não `root`).
  3. `login.php` grava cada tentativa (sucesso, senha errada, e-mail inexistente) em `/var/log/app/login.log`, uma linha JSON `{"ts", "origem", "usuario", "sucesso"}` (função em `login/registro_login.php`). O log fica no volume `web_logs`, para o agente ler depois.
  4. `logout.php`: removida a linha de JavaScript que quebrava o logout.
  5. "Esqueci a senha": envio pelo container `smtp` (porta 25, sem usuário e senha); credenciais do Gmail removidas do `mail_config.php`; link do e-mail em `http`.
  6. Contatos reais do rodapé (e-mail, endereço e telefone) trocados por fictícios.
  7. Banco: `init.sql` com `usuarios` (já com `nome_completo`, `telefone`, `reset_token`, `reset_token_expiry`, que o site usa e o script original não criava), `recuperacao_senha` e `favorites`; 5 usuários e 4 favoritos **inventados** (`@lab.local`, senhas = hash de texto aleatório). `02-monitor.sh` cria o usuário `monitor` só com `SELECT` e `PROCESS`.
  8. Container web com `Dockerfile` próprio (PHP 8.3 + `mysqli` + `/server-status` liberado só na rede interna).
  9. Postfix: todo e-mail para `@lab.local` cai numa caixa única (`/var/mail/lab`).
  10. `servicos/.env.exemplo` ganhou `SITE_DB_USUARIO`, `SITE_DB_SENHA` e `MONITOR_DB_SENHA`.
- **Por quê:** o site é o alvo dos ataques; o log de login é a fonte da detecção de força bruta; nenhuma senha pode ficar no repositório.
- **Arquivos:** `servicos/web-vuln/**`, `servicos/banco/init.sql`, `servicos/banco/02-monitor.sh`, `servicos/docker-compose.yml`, `servicos/.env.exemplo`, `servicos/smtp/Dockerfile`, `servicos/smtp/main.cf`, `tests/varredura_site.py`, `tests/test_site.py`, `tests/test_infra.py`.
- **Verificação (ambiente de validação, sem Docker Hub):**
  - Testes escritos antes: `pytest tests/test_site.py` → 9 failed; depois da adaptação → 13 passed.
  - Ponta a ponta com PHP 8.3, MariaDB e Postfix locais: raiz redireciona para o site; cadastro → 302; senha errada e e-mail inexistente → mensagem e linha `sucesso: false`; login certo → `suaconta.php` e linha `sucesso: true`; favoritos e atualização de dados → `success: true`; logout → 302; "esqueci a senha" → "E-mail enviado" e e-mail entregue em `/var/mail/lab` com o link `http`.
  - Banco: 3 tabelas, 5 usuários, 4 favoritos; `monitor` lê e recebe `ERROR 1142` ao tentar `INSERT`.
  - Sabotagens acusadas: tirar `sucesso` do JSON; apagar um `registrar_tentativa()` do `login.php`; dar `INSERT` ao `monitor`; pôr um e-mail do Gmail no `home.html`; senha de root errada no `02-monitor.sh` (para com erro em vez de dizer "criado").
  - Credenciais originais do `mail_config.php` procuradas no repositório inteiro → 0 arquivos.
  - `docker compose config` → válido; sem `SITE_DB_SENHA` → erro "defina SITE_DB_SENHA".
  - `pytest` → 43 passed, 12 skipped (os 12 só rodam com `MONITOR_INFRA=1`).
- **Verificação no WSL da Bia (20/11 15:14):** `MONITOR_INFRA=1 pytest tests/test_infra.py` → 11 passed, 1 failed: `test_site_receitas_no_ar` não achou "Receitas Práticas" porque o Apache não informava a codificação e o texto foi lido como Latin-1. Correção: `AddDefaultCharset UTF-8` no `servicos/web-vuln/Dockerfile`.
- **Pendências / riscos:**
  - Conferir no WSL: `docker compose down -v` (o banco antigo não tem as tabelas; o `init.sql` só roda em volume novo) e `MONITOR_INFRA=1 pytest tests/test_infra.py`.
  - Vulnerabilidades mantidas de propósito (alvo do laboratório): mensagens diferentes para "e-mail não encontrado" e "senha incorreta" (enumeração de usuários), login sem limite de tentativas, nome do usuário impresso sem escape em `suaconta.php` (XSS), `display_errors` ligado em `resetpassword.php`.
  - Código morto do site original mantido como estava: `processa_cadastro.php` e `login/update_password.php` usam colunas que não existem.
- **Verificação final no WSL (20/11 15:17):** `pytest` → 43 passed, 12 skipped; `MONITOR_INFRA=1 pytest tests/test_infra.py` → 12 passed.

## 2026-11-20 19:00 — Sondas reais de MySQL, DNS e SMTP (P2, tarefa 1)
- **Quem:** Luiz (P2)
- **O que mudou:** `sonda_mysql` (PyMySQL: conecta, `SELECT 1`, `SHOW GLOBAL STATUS`, `max_connections`, tamanho dos bancos), `sonda_dns` (dnspython: consulta A direta no servidor; NXDOMAIN, SERVFAIL, REFUSED, resposta vazia e timeout contam como fora do ar) e `sonda_smtp` (smtplib: banner 220, EHLO 250, QUIT). Todas devolvem `disponivel` e `latencia_ms`; a do MySQL devolve também `status.<Contador>` brutos, `max_connections` e `tamanho_mb` (o Coletor/`derivadas` transforma em `db.*`).
- **Por quê:** a sonda TCP dava "no ar" só porque o Docker aceita a conexão antes do serviço estar pronto.
- **Arquivos:** `plataforma/infra/sondas.py`, `tests/test_sondas.py`, `tests/falsos/dns_smtp_falsos.py`.
- **Verificação:** `pytest tests/test_sondas.py` → 23 passed (teste escrito antes: 17 failed). Sabotagens acusadas: porta aberta que não é MySQL/SMTP; servidor fora do ar; SELECT 1 falhando; banner 421/554; EHLO 550; DNS com SERVFAIL/REFUSED/NXDOMAIN; DNS mudo. Mutações no código (EHLO ignorado, exceção DNS não tratada, MB sem dividir, MySQLError não tratado, porta errada) → todas acusadas.
- **Pendências / riscos:** o MySQL foi testado com conexão falsa (não há MySQL real no ambiente de validação); conferir no WSL com `MONITOR_INFRA=1`. `servicos.toml` (novos `tipo`) muda junto com a tarefa 4, porque o Coletor ainda não conhece os tipos novos.

## 2026-11-20 19:00 — Cliente do agente (P2, tarefa 2)
- **Quem:** Luiz (P2)
- **O que mudou:** `ler_metricas(url_base, token, timeout_s)` faz `GET {url_base}/metrics` com `X-Token` e devolve o dicionário; falhas sobem como `ErroAgente` (sem rede, HTTP diferente de 200, token errado, corpo que não é objeto JSON).
- **Por quê:** o Coletor precisa saber que o agente falhou e omitir as métricas, em vez de receber um dicionário vazio.
- **Arquivos:** `plataforma/infra/agente_cliente.py`, `tests/test_agente_cliente.py`.
- **Verificação:** `pytest tests/test_agente_cliente.py` → 8 passed, com servidor falso servindo `tests/falsos/agente_exemplo.json`. Mutações (sem checar status, sem enviar token, sem checar objeto) → acusadas.
- **Pendências / riscos:** URL e token do agente vêm de `config`/`.env` na tarefa 4 (nomes a combinar com P1).

## 2026-11-20 19:00 — Derivadas do agente para o catálogo (P2, tarefa 3)
- **Quem:** Luiz (P2)
- **O que mudou:** `derivar(atual, anterior, falhas_sonda_dns=0)` converte o JSON do agente em amostras `web.*`, `dns.*`, `smtp.*`, `host.*`. Métrica que não dá para calcular (seção ausente, sem leitura anterior, contador que diminuiu, divisão por zero) é omitida.
- **Por quê:** o agente entrega contadores e contagens; o catálogo pede taxas e percentuais.
- **Arquivos:** `plataforma/dominio/derivadas.py`, `tests/test_derivadas.py`.
- **Verificação:** `pytest tests/test_derivadas.py` → 13 passed (teste escrito antes: erro de import); valores calculados à mão no cabeçalho do teste. Mutações (p95, divisão por zero, unidade de e-mails/min, faixa 5xx, falha da sonda DNS) → acusadas. `pytest` inteiro (cópia do repositório com os arquivos recebidos) → 44 passed, 5 de 5 vezes.
- **Pendências / riscos:** premissas: `log_web` e `postfix` são contagens da janela (não acumulam); `apache` e `unbound` são acumulados; `smtp.taxa_erro_pct` usa como total sent+deferred+bounced+rejeicoes+timeouts; p95 pelo posto mais próximo. Confirmar com P1 (agente).

## 2026-11-21 — Coletor junta sondas reais e agente num lote só (P2, tarefa 4)
- **Quem:** Luiz (P2)
- **O que mudou:**
  1. `coletor.py` ganhou os tipos de sonda `mysql`, `dns` e `smtp` (além de `http` e `tcp`) e passou a ler o agente (`agente_cliente`) e derivar as métricas (`derivadas`, `derivadas_db`), tudo em um único lote para `POST /api/ingest`.
  2. Novo `Memoria` guarda a leitura anterior do agente e do MySQL, e as leituras do banco dos últimos 10 min (as taxas e o `db.crescimento_mb_dia` precisam de duas leituras). Em `--uma-vez` não há leitura anterior, então só saem os valores instantâneos.
  3. Novo `dominio/derivadas_db.py`: `db.qps`, `db.rollbacks_s`, `db.conexoes_abortadas`, `db.slow_queries_min`, `db.conexoes`, `db.conexoes_executando`, `db.threads_cache`, `db.uso_conexoes_pct`, `db.tamanho_mb`, `db.crescimento_mb_dia` (exige ≥ 60 s de histórico, comparando com a leitura mais antiga dos últimos 10 min, para o tamanho não oscilar por páginas de 16 KB).
  4. `config/servicos.toml`: `db` = `mysql`, `dns` = `dns`, `smtp` = `smtp`; `agente_url` comentado até o agente (P1) estar no ar.
- **Por quê:** até aqui as sondas de banco, DNS e SMTP só viam a porta, e o agente não era lido.
- **Arquivos:** `plataforma/infra/coletor.py`, `plataforma/dominio/derivadas_db.py`, `config/servicos.toml`, `tests/test_coletor.py`, `tests/test_derivadas_db.py`.
- **Variáveis novas no `.env` (sem valor no repositório):** `MONITOR_DB_SENHA` (obrigatória para o tipo `mysql`), `MONITOR_DB_USUARIO` (padrão `monitor`), `MONITOR_DNS_CONSULTA` (padrão `teste.lab.local`), `MONITOR_AGENTE_URL` (ou `agente_url` no toml) e `MONITOR_AGENTE_TOKEN` (obrigatória quando o agente está configurado).
- **Comportamento em falha:** agente fora do ar → mensagem em stderr e só as métricas do agente são omitidas; banco fora do ar → só `db.disponivel` e `db.latencia_ms`, e essa leitura não vira referência; senha ou token ausentes → erro explícito (não finge que o serviço caiu).
- **Verificação:** `pytest` (cópia do repositório) → 68 passed, 1 skipped (dashboard, sem streamlit aqui), 3 de 3 vezes; `tests/test_termometro.py` continua verde. Ponta a ponta: API + Coletor reais contra web, DNS, SMTP e agente falsos, banco fora do ar → `db` CRITICO, os outros OK, `host.cpu_pct` e `web.latencia_p95_ms` gravados. Mutações no código (banco caído virando referência, falha da sonda DNS ignorada, janela de crescimento, leitura do agente não guardada, senha ausente aceita, exceção do agente, agente sem configuração, sonda errada por tipo, histórico mínimo, taxa por minuto) → todas acusadas.
- **Pendências / riscos:** não testado contra MariaDB, Unbound e Postfix reais (rodar `MONITOR_INFRA=1 pytest tests/test_infra.py` e `python -m plataforma.infra.coletor --uma-vez` no WSL); porta e formato do agente a confirmar com P1; `tests/test_infra.py` não foi visto e pode ler `servicos.toml`.

## 2026-11-21 19:00 — Regras de alerta de todas as métricas (P2, tarefa 5)
- **Quem:** Luiz (P2)
- **O que mudou:** `config/regras.toml` passou de 6 para 40 regras (web, banco, DNS, SMTP e host). Só 5 métricas ficaram sem regra de propósito (`web.rps`, `web.req_4xx`, `web.req_5xx`, `db.conexoes`, `db.threads_cache`): são contagens ou volume, tratados por outra regra ou pela detecção de DDoS. `db.crescimento_mb_dia` usa `subir = 3`.
- **Por quê:** o esqueleto só alertava disponibilidade e latência de web e DNS.
- **Arquivos:** `config/regras.toml`, `tests/test_regras.py`.
- **Verificação:** `pytest tests/test_regras.py` → 10 passed. Sabotagens acusadas: regra removida (a métrica precisa ter regra ou estar na lista de informativas do teste), limite crítico invertido, operador inválido, campo desconhecido no TOML. `test_termometro.py` continua verde.
- **Pendências / riscos:** **os limites são propostas iniciais** (não tive a seção 8 da arquitetura original): conferir com o grupo e recalibrar com a linha de base real. Com os dados de exemplo do agente, `web.taxa_erro_5xx_pct` (3,3 %) e `smtp.taxa_entrega_pct` (92,3 %) já passam de ATENÇÃO.

## 2026-11-21 19:00 — Segurança: DDoS, força bruta e alteração de configuração (P2, tarefa 6)
- **Quem:** Luiz (P2)
- **O que mudou:**
  1. `dominio/seguranca.py`: escore z de `web.rps` e `dns.qps` contra a última hora (z ≥ 3 ATENÇÃO, z ≥ 5 CRÍTICO; mínimo de 20 amostras; piso de desvio 5), falhas de login por IP em 60 s (5 = ATENÇÃO, 20 = CRÍTICO) e hash diferente da linha de base (CRÍTICO).
  2. API: `POST /api/seguranca/leitura` (X-Token; recebe `auth` e `hashes` do agente), `POST /api/seguranca/linha-base` (X-Token), `GET /api/seguranca`; no `POST /api/ingest` o DDoS é avaliado antes das regras de alerta. Eventos gravam em `evento_seguranca` e saem por e-mail pelo notificador.
  3. Sem repetição: o aviso só se repete se o nível subir ou após 5 min; alteração de arquivo avisa uma vez por mudança de hash.
  4. `infra/banco.py`: tabelas `tentativa_login` e `hash_arquivo` e métodos novos (só acréscimos; `CREATE TABLE IF NOT EXISTS`, bancos existentes se atualizam sozinhos). `infra/notificador.py`: linha `Detalhe:` opcional no e-mail. `infra/coletor.py`: repassa `auth` e `hashes` do agente à API depois de cada lote (uma vez por leitura).
- **Por quê:** o pedido P2 tarefa 6; o contrato do lote (`amostras`) não carrega login nem hashes, por isso a rota nova de leitura.
- **Arquivos:** `plataforma/dominio/seguranca.py`, `plataforma/api/app.py`, `plataforma/infra/banco.py`, `plataforma/infra/notificador.py`, `plataforma/infra/coletor.py`, `tests/test_seguranca.py`, `tests/test_api_seguranca.py`, `tests/test_coletor.py`.
- **Verificação:** `pytest` (cópia do repositório) → 155 passed, 1 skipped, 3 de 3 vezes. Mutações no código (limites, queda tratada como DDoS, hash igual, nível não sobe, token removido nas duas rotas, janela de 60 s, ponto atual no próprio histórico, cooldown, deduplicação de configuração, filtro de sucesso, origem no SQL, leitura reenviada) → todas acusadas. Ponta a ponta com API e Coletor reais: leitura do agente chega, linha de base grava o hash.
- **Pendências / riscos:** a rota nova e a mudança do Coletor são acréscimos ao combinado (as rotas existentes não mudaram); avisar P1 e P3. Premissas sobre o agente a confirmar com P1: `auth` traz só tentativas novas (se repetir, as falhas contam em dobro) e os relógios do agente e da plataforma estão sincronizados. Tipo `VULNERABILIDADE` não implementado. `HOST` pode aparecer em `/api/status` quando o agente manda `host.*`: o dashboard (P3) deve prever o serviço extra. `tentativa_login` não tem limpeza.

## 2026-11-21 19:00 — Arquitetura final e playbooks (P2, tarefa 7)
- **Quem:** Luiz (P2)
- **O que mudou:** `docs/arquitetura.md` (visões de implantação, camadas e ciclo com diagramas Mermaid, catálogo de métricas e limites gerados a partir do contrato e do `regras.toml`, API, alertas, segurança, modelo de dados, configuração, limitações) e 11 playbooks em `docs/playbooks/` (serviço fora do ar, latência, erros HTTP, banco conexões, banco crescimento, DNS, SMTP, recursos da máquina, DDoS, força bruta, configuração alterada), cada um com Sintoma, Diagnóstico e Ação, mais um índice.
- **Por quê:** substituir o documento externo da 1ª versão por Markdown versionado, alinhado ao que foi implementado.
- **Arquivos:** `docs/arquitetura.md`, `docs/playbooks/*.md`, `tests/test_docs.py`.
- **Verificação:** `pytest tests/test_docs.py` → 17 passed: toda métrica com regra está na arquitetura e no playbook da sua linha do índice, todo playbook está no índice e tem as três seções, os limites de segurança batem com o código, os links entre playbooks existem. 8 sabotagens na documentação acusadas.
- **Pendências / riscos:** aguardando revisão de P3. Os comandos dos playbooks não foram executados nos containers (conferir nomes de logs e caminhos no WSL). A arquitetura descreve o agente como combinado com P1; ajustar quando o agente real existir. Itens que não pude confirmar: limites de CPU/memória dos containers (vieram do LOG de 20/11) e se o dashboard já usa `/api/seguranca`.

## 2026-11-20 21:10 — Agente, DNS/SMTP conferidos, ataques, isolamento, guia e runbooks
- **Quem:** Bia (P1, tarefas 4 a 8)
- **O que mudou:**
  1. **Agente** (`servicos/agente/`): servidor `http.server` em `127.0.0.1:9101`. `GET /metrics` com `X-Token` devolve as chaves de `tests/falsos/agente_exemplo.json`; sem token = 401. Roda no WSL (fora dos containers) e lê:
     - Apache: `/server-status`;
     - logs de acesso e login, incrementais, com guarda da posição e tratamento de rotação e de linha pela metade;
     - Unbound: `unbound-control stats_noreset`;
     - Postfix: `postqueue -j` e `docker logs`;
     - `docker stats`, `/proc` e SHA-256 dos arquivos de configuração dentro dos containers.

     Fonte fora do ar vira `null`, sem derrubar o agente. Semântica de cada campo (acumulado, janela ou foto) em `docs/runbooks/agente.md`.
  2. **Logs do web** saem do volume escondido para a pasta `servicos/logs/web/` (fora do Git), para o agente ler. Novo log `acesso.log` com `código tempo_us` (`web-vuln/apache-log.conf`); o container acerta o dono da pasta na subida.
  3. **DNS:** a construção para se faltar o `unbound-control`. **SMTP:** testes reais de entrega (`status=sent`) e fila.
  4. **Ataques** (`testes/`): `ataque_ddos.py` (inundação HTTP), `ataque_brute_force.py` (lista de senhas fracas, com `--criar-vitima`) e `teste_isolamento.py` (DDoS no web enquanto sondas reais vigiam db, dns e smtp; grava a evidência em `testes/evidencias/`). Todos recusam alvo fora de 127.0.0.1 (`alvo_local.py`). No `pedido-p1.md`, o `ataque_ddos.sh` virou `.py`.
  5. **Documentação:** `docs/guia-instalacao.md` (do zero, WSL + Docker Desktop) e `docs/runbooks/` (web, db, dns, smtp, agente, ataques).
  6. `.env.exemplo` ganhou `AGENTE_TOKEN` e `AGENTE_URL`; `.gitignore` ganhou `servicos/logs/`.
- **Por quê:** fechar a parte P1: a P2 precisa do agente para as métricas internas e a segurança; a regra da professora exige provar o isolamento.
- **Arquivos:** `servicos/agente/*.py`, `servicos/web-vuln/Dockerfile`, `servicos/web-vuln/apache-log.conf`, `servicos/dns/Dockerfile`, `servicos/docker-compose.yml`, `testes/*.py`, `tests/test_agente.py`, `tests/test_ataques.py`, `tests/test_infra.py`, `tests/test_site.py`, `docs/guia-instalacao.md`, `docs/runbooks/*.md`, `docs/ia/pedido-p1.md`, `.env.exemplo`, `.gitignore`.
- **Verificação (ambiente de validação):**
  - Testes escritos antes do código (coleta falhou sem os módulos); depois: `tests/test_agente.py` → 13 passed; `tests/test_ataques.py` → 12 passed; `pytest` → 68 passed, 17 skipped.
  - Fontes com serviços reais locais:
    - Unbound real: `teste.lab.local` → 192.0.2.10, NXDOMAIN contado;
    - Apache real com as duas `.conf`: `Syntax OK`, `/server-status` lido, `acesso.log` com `200 329` e `404 119`;
    - `postqueue -j` e `sha256sum`: hash `null` para arquivo inexistente.
  - Força bruta no site real (PHP + MariaDB): `ENTROU` na tentativa 29, com as linhas no `login.log`.
  - Isolamento: DDoS de 5 s, ~960 req/s no site; db, dns e smtp 5/5; com a porta do db errada → reprovado.
  - Sabotagens acusadas: tirar a checagem de rotação do log; aceitar qualquer token; devolver 0 em vez de `null` com o Unbound fora do ar; liberar alvo fora de 127.0.0.1.
- **Integração com a P2 (PRs #4, #5 e #6 já na `main`):** o JSON real do agente passou por `agente_cliente.ler_metricas` → `derivadas.derivar` → `validar_lote` com 17 métricas aceitas; DNS fora do ar (`null`) → métricas `dns.*` omitidas, como combinado. `sonda_mysql` testada num MariaDB real com o usuário `monitor` (lê status, `max_connections` e tamanho; senha errada = fora do ar). Ajuste: `AGENTE_URL` no `.env.exemplo` sem `/metrics` (o cliente da P2 já acrescenta).
- **Pendências / riscos:**
  - Rodar no WSL: `MONITOR_INFRA=1 pytest tests/test_infra.py` (17 testes, incluindo agente, DNS, SMTP, hash e isolamento de 15 s).
- **Verificação no WSL da Bia (20/11 16:01):** `pytest` → 68 passed, 17 skipped; `MONITOR_INFRA=1 pytest tests/test_infra.py` → 16 passed, 1 failed: `test_agente_le_os_containers_de_verdade` com `log_web.total = 0`.
  - **Causa:** o site padrão da imagem (`000-default`, `<VirtualHost *:80>`) tem o próprio `CustomLog`, e então o `CustomLog` de fora é ignorado para as requisições dele.
  - **Por que a validação local não pegou:** o Apache de teste ouvia na porta 8088 e o VirtualHost estava em `*:80`, então as requisições não passavam pelo VirtualHost. Isso foi um erro do meu teste.
  - **Reproduzido** com o VirtualHost na mesma porta: 0 linhas com `CustomLog` e 1 linha com `GlobalLog`.
  - **Correção:** `GlobalLog` em `servicos/web-vuln/apache-log.conf`.
  - Avisar a P2: os campos `null` e a semântica "janela desde a leitura anterior" (`docs/runbooks/agente.md`) valem para o `agente_cliente.py` e as `derivadas.py`.
  - A detecção (escore z, falhas por IP, linha de base de hash) é da P2, tarefa 6. A P1 entrega os dados e os ataques.

## 2026-11-20 21:30 — Organização do repositório
- **Quem:** Bia (P1)
- **O que mudou:** `README.md` com a estrutura atual (agente, logs, ataques, guia) e os comandos para subir tudo; removidos os `.gitkeep` de `servicos/agente/`, `testes/` e `docs/runbooks/` (as pastas já têm arquivos).
- **Por quê:** a professora vai avaliar a organização do Git.
- **Arquivos:** `README.md`, `servicos/agente/.gitkeep`, `testes/.gitkeep`, `docs/runbooks/.gitkeep`.
- **Verificação:** `git ls-files` sem `.gitkeep` em pasta com conteúdo; `pytest` verde.
- **Pendências / riscos:** apagar as branches já mescladas; ligar "apagar branch depois do merge"; tags de marco (`v0.1.0` esqueleto, `v0.2.0` serviços + agente).

## 2026-11-22 13:30 — Agente ligado ao coletor da P2 e envio da parte P1
- **Quem:** Bia (P1)
- **O que mudou:**
  1. A branch `a/agente-ataques` (20/11) não tinha sido enviada. O mesmo conteúdo foi refeito sobre a `main` atual, já com os PRs #4 a #14 da P2, na branch `a/agente-final`.
  2. Token do agente renomeado de `AGENTE_TOKEN` para `MONITOR_AGENTE_TOKEN`, e a URL para `MONITOR_AGENTE_URL`, que são os nomes que o coletor da P2 lê. O `.env.exemplo` ganhou `MONITOR_DB_SENHA` (a sonda do banco da P2 precisa dela; é a mesma senha do `servicos/.env`, e o guia mostra como copiar).
  3. O agente faz as consultas ao Docker em paralelo (`ThreadPoolExecutor`): o coletor espera no máximo 5 s, e em série elas podiam passar disso durante um ataque.
  4. `CHECKLIST.md`: marcados os itens da P1 (banco, site, DNS, SMTP, runbooks, guia).
- **Por quê:** a parte P1 não estava no GitHub, e o agente precisava conversar com o coletor que a P2 já colocou na `main`.
- **Arquivos:** os da entrada de 20/11 21:10, mais `servicos/agente/agente.py`, `servicos/agente/agente_fontes.py`, `tests/test_agente.py`, `.env.exemplo`, `docs/guia-instalacao.md`, `docs/runbooks/agente.md`, `CHECKLIST.md`.
- **Verificação:** `pytest` sobre a `main` atual → 197 passed, 17 skipped. Teste novo: com cada comando do Docker levando 0,5 s, uma leitura leva menos de 2 s (em série seriam ~4,5 s); sabotagem (hashes com 1 thread) → acusada.
- **Pendências / riscos:**
  - Rodar `MONITOR_INFRA=1 pytest tests/test_infra.py` no WSL.
  - O monitoramento de **vulnerabilidade conhecida por serviço** (enunciado, seção 5) ainda não tem dono: falta combinar no grupo.
- **Verificação no WSL (23/11 12:04):** `pytest` → 197 passed; `MONITOR_INFRA=1` → 16 passed, 1 failed: o teste do db chamava a sonda sem ler o `.env`. Correção: `config.carregar_env()` em `tests/test_infra.py`.

## 2026-11-23 10:50 — Roteiro de testes T01 a T15 (P3, tarefa 3)
- **Quem:** Yuri (P3)
- **O que mudou:** `testes/roteiro.md` com os 15 casos de teste da plataforma, cada um com objetivo, requisito do enunciado, pré-condições, passos numerados (comandos exatos), resultado esperado, arquivo de evidência em `testes/evidencias/` e campo de passou/falhou; seções de ambiente (VM, 3 terminais, modo de e-mail, tempos das regras de alerta), de como registrar a evidência e tabela de resumo caso × requisito × dependência. `tests/test_roteiro.py` confere a estrutura.
- **Por quê:** pedido P3, tarefa 3. A seção 13 da arquitetura citada no pedido não existe; os casos foram montados a partir da seção 6 do `CHECKLIST.md` e dos requisitos do enunciado (seções 2 a 5).
- **Arquivos:** `testes/roteiro.md`, `tests/test_roteiro.py`, `docs/LOG.md`.
- **Verificação:**
  - Teste escrito antes: `pytest tests/test_roteiro.py` → 5 failed (arquivo ausente); depois do roteiro → 5 passed.
  - Sabotagens acusadas: caso T07 removido, campo "Resultado esperado" trocado no T03, evidência do T12 sem arquivo, T15 fora da tabela de resumo, e (no arquivo real) campo "Requisito" do T12 renomeado.
  - Tempos dos casos T06, T08 e T09 conferidos contra `plataforma/dominio/alertas.py` (disponibilidade: 1ª falha ATENÇÃO, 2ª CRÍTICO; demais sobem com 2; todas descem com 3, direto para o nível medido).
  - `pytest` → 173 passed, 15 skipped (os pulados precisam de Docker/PHP: `MONITOR_INFRA=1`).
- **Pendências / riscos:** revisão de P1 e P2 (critério "pronto quando" do pedido). T10, T12 e T13 dependem do agente e dos scripts de ataque (P1, ainda não estão no repositório). T08 usa `tc` na interface local: validar na VM se o atraso pega a porta publicada pelo Docker. T14: ferramenta e responsável pela "vulnerabilidade conhecida por serviço" a definir no grupo.

## 2026-11-23 09:14 — Dashboard completo: páginas por serviço, alertas e segurança (P3, tarefas 1 e 2)
- **Quem:** Yuri (P3)
- **O que mudou:**
  1. `plataforma/dashboard/app.py` com 4 páginas (seletor no topo): **Visão geral** (um cartão por serviço com a cor do nível e os 5 últimos alertas), **Por serviço** (todas as métricas do catálogo do serviço, com unidade, cor, valor atual, gráfico da última hora e, na ajuda ⓘ, a descrição e os limites do `regras.toml`), **Alertas** (`GET /api/alertas`: contagens e tabela com de/para, valor, limite e e-mail enviado) e **Segurança** (`GET /api/seguranca`: contagem por tipo, tabela de eventos e linha de base dos arquivos).
  2. Cores: 🟢 OK, 🟡 ATENCAO, 🔴 CRITICO, ⚪ sem dados, 🔵 métrica informativa (sem regra). O nível de cada métrica é o `nivel_novo` do alerta mais novo dela (o mesmo estado com histerese da API); métrica sem dados nunca aparece como OK.
  3. Serviço `HOST` previsto (aparece na visão geral quando o agente manda `host.*`, como pedido no LOG de 21/11).
  4. API fora do ar (ou resposta que não é JSON) vira mensagem "API indisponível" em cada página, sem quebrar a tela.
  5. Responsividade: cartões em linhas de 3 colunas (`st.columns`), que o Streamlit empilha sozinho em telas estreitas; conferido a 1366 px e a 390 px.
  6. Novo `plataforma/dashboard/formatos.py`: funções puras (nível de cada métrica, valor com unidade no padrão brasileiro, texto dos limites, horário legível), testáveis sem o Streamlit.
  7. `CHECKLIST.md`: marcados os dois itens de front-end (por serviço e visão consolidada).
- **Por quê:** pedido P3, tarefas 1 e 2; a visão geral continua com exatamente os 4 cartões de serviço, então o `test_termometro.py` não precisou mudar.
- **Arquivos:** `plataforma/dashboard/app.py`, `plataforma/dashboard/formatos.py`, `tests/test_dashboard.py`, `tests/test_dashboard_formatos.py`, `CHECKLIST.md`, `docs/LOG.md`.
- **Verificação:**
  - Testes escritos antes: `pytest tests/test_dashboard.py tests/test_dashboard_formatos.py` → erro de import e 15 failed; depois da implementação → 32 passed. O teste do dashboard usa `AppTest` contra a API real (`criar_app` numa thread com banco temporário, dados enviados pelas mesmas rotas do Coletor).
  - 11 sabotagens no código, todas acusadas: métrica sem dados virando OK, alerta antigo sobrescrevendo o novo, rótulo sem unidade, API fora do ar sem tratamento, página com só 3 métricas, e-mail sempre "não enviado", CRÍTICO com cor verde, evento sem origem, valor sem unidade, HOST escondido, linha de base escondida.
  - `pytest` → 200 passed, 15 skipped (os 15 precisam de Docker/PHP: `MONITOR_INFRA=1`). Camadas: o dashboard só importa `contrato` e o próprio `formatos`.
  - Tela conferida com API + dashboard reais e 1 h de dados de demonstração, a 1366 px (PC) e 390 px (celular).
- **Pendências / riscos:** prints definitivos no PC e no celular (tarefa 2) saem na VM, com os serviços reais (tarefa 4). Os limites mostrados na ajuda vêm do `config/regras.toml` local do dashboard (é configuração, não dado; os dados continuam vindo só da API).
- **Verificação no WSL (23/11 12:06):** `MONITOR_INFRA=1 pytest tests/test_infra.py` → 17 passed.

## 2026-11-23 13:30 — Vulnerabilidade conhecida por serviço, CPU e memória do banco e revisão final da P1
- **Quem:** Bia (P1)
- **O que mudou:**
  1. **Vulnerabilidade conhecida por serviço** (enunciado, seção 5; era o único item sem dono):
     - o agente lê a versão de Apache, PHP, MySQL, Unbound e Postfix dentro dos containers, com cache de 10 min;
     - novo campo `versoes` no JSON do agente (`tests/falsos/agente_exemplo.json`), repassado pelo Coletor em `POST /api/seguranca/leitura`;
     - `config/vulnerabilidades.toml` lista 8 CVEs reais (Apache, PHP, MySQL, Unbound e Postfix), cada um com versão corrigida, nível e fonte oficial conferida em 23/11;
     - `plataforma/dominio/vulnerabilidades.py` compara as versões levando em conta ramo e faixa e gera evento `VULNERABILIDADE`, uma vez por falha, com e-mail;
     - a API guarda as versões (tabela `versao_programa`) e as devolve em `GET /api/seguranca`;
     - o dashboard mostra a tabela de versões na página Segurança;
     - novo playbook `seguranca-vulnerabilidade.md`, e o caso T14 do roteiro foi refeito.
  2. **CPU e memória do banco** (enunciado, seção 3.2): métricas `db.cpu_pct` e `db.mem_pct`, vindas do `docker stats` do container `db`. O contrato ganhou essas duas métricas (proposta de 20/11). Regras: > 80/95 e > 85/95. I/O e latência de disco do banco são os do disco da máquina (`host.disco_*`); está registrado na arquitetura.
  3. **Revisão final da P1**, que estava só na máquina da Bia:
     - formato dos logs descrito no `docs/runbooks/web.md`;
     - comentários reescritos;
     - `README` com "regras de contribuição";
     - evidência do teste de isolamento (60 s de DDoS, ~700 req/s; db, dns e smtp 46/46);
     - teste de isolamento marcado na CHECKLIST;
     - roteiro citando `python testes/ataque_ddos.py`.
- **Por quê:** fechar os dois itens do enunciado que faltavam, conferidos item por item contra o PDF do enunciado.
- **Ajustes em testes de outras partes (sem enfraquecer):**
  - `test_derivadas`: o valor esperado ganhou `db.cpu_pct` e `db.mem_pct`, calculados à mão.
  - `test_coletor`: a leitura de segurança passou a incluir `versoes`.
  - No banco fora do ar, `db.cpu_pct` e `db.mem_pct` (que vêm do agente) continuam válidos.
- **Arquivos:**
  - código: `config/vulnerabilidades.toml`, `config/regras.toml`, `plataforma/contrato/config.py`, `plataforma/contrato/metricas.py`, `plataforma/dominio/vulnerabilidades.py`, `plataforma/dominio/derivadas.py`, `plataforma/api/app.py`, `plataforma/infra/banco.py`, `plataforma/infra/coletor.py`, `plataforma/dashboard/app.py`, `servicos/agente/agente.py`, `servicos/agente/agente_fontes.py`, `servicos/web-vuln/site/login/registro_login.php`;
  - testes: `tests/test_vulnerabilidades.py`, `tests/test_api_seguranca.py`, `tests/test_agente.py`, `tests/test_derivadas.py`, `tests/test_coletor.py`, `tests/test_dashboard.py`, `tests/test_infra.py`, `tests/test_site.py`, `tests/falsos/agente_exemplo.json`;
  - documentação: `docs/arquitetura.md`, `docs/playbooks/README.md`, `docs/playbooks/seguranca-vulnerabilidade.md`, `docs/runbooks/agente.md`, `docs/runbooks/web.md`, `testes/roteiro.md`, `testes/evidencias/isolamento-*.json`, `README.md`, `CHECKLIST.md`.
- **Verificação:**
  - Testes escritos antes do código: coleta falhou (módulo ausente) e 3 failed no agente, dashboard e derivadas. Depois: `pytest` → 253 passed, 17 skipped.
  - Comandos de versão rodados em programas reais (Apache 2.4.58, PHP 8.3.6, Unbound 1.19.2, Postfix 3.8.6): todas as versões lidas; a comparação marcou os CVEs esperados.
  - Sabotagens acusadas:
    - ignorar o ramo (3.7.12 marcado pela correção do ramo 3.8);
    - avisar a cada ciclo em vez de uma vez;
    - versão ilegível;
    - programa fora do ar;
    - container do banco sem dado;
    - versões fora do formato na API (400).
- **Pendências / riscos:**
  - Rodar `MONITOR_INFRA=1 pytest tests/test_infra.py` no WSL (confere as versões reais nos containers).
  - Avisar P2 e P3 das mudanças nos arquivos deles (campo `versoes`, `db.cpu_pct` e `db.mem_pct`, tabela no dashboard).
  - A lista de CVEs é mantida à mão.

## 2026-11-23 15:00 — Ensaio da plataforma inteira e correção do notificador
- **Quem:** Bia (P1)
- **O que mudou:**
  1. **Ensaio de ponta a ponta:**
     - Rodaram juntos agente, API e coletor (o laço de 15 s, aqui com 3 s), contra serviços reais: site PHP com MariaDB, Unbound, Postfix e Apache com `/server-status`.
     - Só o Docker foi simulado (um `docker` falso que roda os comandos na própria máquina), porque o ambiente de validação não baixa imagens.
     - Resultado: 39 das 40 métricas gravadas (falta só `db.crescimento_mb_dia`, que exige 60 s de histórico); os 4 serviços e o `host` ficaram OK.
     - Força bruta (29 tentativas): AUTENTICACAO ATENÇÃO e depois CRÍTICO.
     - `main.cf` alterado depois da linha de base: CONFIGURACAO CRÍTICO.
     - Unbound derrubado: `dns` ATENÇÃO e depois CRÍTICO, com os outros serviços OK.
     - Versões antigas da máquina de teste: 4 eventos VULNERABILIDADE.
     - Todos os eventos saíram por e-mail.
  2. **Defeito encontrado no ensaio:** no modo arquivo, dois avisos com a mesma hora, métrica e nível tinham o mesmo nome de arquivo, e o segundo sobrescrevia o primeiro (4 vulnerabilidades geraram só 2 arquivos). Agora o nome inclui o serviço, e um número se o arquivo já existir. No modo SMTP não havia perda.
  3. Textos desatualizados:
     - porta do agente no comentário do `config/servicos.toml` (9100 → 9101);
     - "notebook" → WSL no `testes/roteiro.md` e no `docs/ia/pedido-p1.md`;
     - endereços da VM antiga no `pedido-p1.md`.
  4. `CHECKLIST.md`: marcados os itens de segurança do repositório (`.env` fora do Git, nenhum segredo, README).
- **Arquivos:** `plataforma/infra/notificador.py`, `tests/test_notificador.py`, `config/servicos.toml`, `testes/roteiro.md`, `docs/ia/pedido-p1.md`, `CHECKLIST.md`.
- **Verificação:**
  - `tests/test_notificador.py` escrito antes: 1 failed (2 de 3 arquivos); depois, 1 passed.
  - `pytest` → 254 passed, 17 skipped.
  - Varredura: nenhum `.env`, banco ou chave rastreados; nenhum e-mail real fora da `vendor/`.
- **Pendências / riscos:** repetir o ensaio no WSL com os containers de verdade (`docs/runbooks/ataques.md`); avisar a professora que o alvo é o site do grupo, e não a DVWA (CHECKLIST, seção 10).

