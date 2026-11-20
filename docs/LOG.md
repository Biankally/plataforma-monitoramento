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
