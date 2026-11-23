# Roteiro de testes — Plataforma de Monitoramento

Este roteiro lista os 15 casos que provam que a plataforma atende ao enunciado (seção 2: "Testes de navegação e uso
da plataforma de monitoramento"). Cada caso tem objetivo, requisito atendido, passos, resultado esperado e o arquivo
de evidência (print) que a tarefa 4 guarda em `testes/evidencias/`. O teste `tests/test_roteiro.py` acusa se faltar um
caso ou um desses campos.

Responsável: P3 (Yuri). Revisão: P1 (Bianca) e P2 (Luiz).

## Ambiente

- **Máquina:** VM Ubuntu 24.04 (Parallels, rede em modo bridged), com Docker e o repositório clonado em `~/plataforma-monitoramento`.
- **Serviços vigiados:** containers de `servicos/docker-compose.yml` (web 8080, db 3307, dns 1053, smtp 2525, todos em 127.0.0.1).
- **Plataforma:** três terminais na raiz do projeto, com o ambiente ativo (`source .venv/bin/activate`):
  1. `python -m plataforma.api` (porta 5000)
  2. `python -m plataforma.infra.coletor` (coleta a cada 15 s)
  3. `streamlit run plataforma/dashboard/app.py --server.address 0.0.0.0` (porta 8501)
- **E-mail:** `NOTIFICADOR=smtp` no `.env` para o print da caixa de entrada; com `NOTIFICADOR=arquivo` o e-mail vira um
  `.txt` em `notificacoes/` (vale como evidência alternativa).
- **Tempos das regras de alerta** (`docs/arquitetura.md`, seção 7): a 1ª falha de disponibilidade já é ATENÇÃO e a 2ª
  seguida é CRÍTICO; as demais métricas sobem com 2 amostras seguidas; todas descem com 3. Com coleta a cada 15 s:
  ATENÇÃO em ~15 s, CRÍTICO em ~30 s, volta ao OK em ~45 s.
- Os comandos `docker compose` rodam dentro de `servicos/`.

## Como registrar a evidência

- Um print por caso (ou mais, com sufixo `-a`, `-b`), salvo com o nome indicado no campo **Evidência**.
- O print precisa ser legível e ter o ponto importante destacado (retângulo ou seta).
- Ao terminar o caso, marcar **Passou** ou **Falhou** e anotar data, hora e qualquer desvio em **Observações**.

## Resumo dos casos

| Caso | Título | Requisito do enunciado | Depende de |
| --- | --- | --- | --- |
| T01 | Instalação do zero e testes automáticos | Documentação: guia de instalação | — |
| T02 | Visão consolidada no PC | Front-end com visão consolidada | — |
| T03 | Dashboard por serviço | Front-end com dashboards por serviço; métricas da seção 3 | — |
| T04 | Responsividade no celular | Front-end responsivo | — |
| T05 | Páginas de alertas e segurança e API fora do ar | Front-end; regras de alerta | — |
| T06 | Queda do web: ATENÇÃO, CRÍTICO e e-mail | Níveis de alerta 2 e 3; notificação por e-mail | — |
| T07 | Queda do banco, do DNS e do SMTP | Disponibilidade de cada serviço; níveis 2 e 3 | — |
| T08 | Degradação de latência: ATENÇÃO | Nível 2 (degradação que exige observação) | — |
| T09 | Recuperação: volta ao OK | Nível 1 (estado normal) | T06 ou T07 |
| T10 | Pico de tráfego (DDoS) | Segurança: anomalias de tráfego | agente e `testes/ataque_ddos.sh` (P1) |
| T11 | Isolamento: ataque ao web não derruba os outros | Regra da professora (isolamento) | T10 |
| T12 | Força bruta no login | Segurança: falhas de autenticação | agente e `testes/ataque_brute_force.py` (P1) |
| T13 | Alteração de arquivo de configuração | Segurança: alteração de configuração | agente (P1) |
| T14 | Varredura de vulnerabilidades | Segurança: vulnerabilidade conhecida por serviço | ferramenta a definir no grupo |
| T15 | Proteção da API e dos segredos | Backend de ingestão; segurança do repositório | — |

## Casos

### T01 — Instalação do zero e testes automáticos

**Objetivo:** provar que outra pessoa instala e roda o projeto seguindo só a documentação.

**Requisito:** documentação (guia de instalação); garantia de execução do CHECKLIST (seção 9).

**Pré-condições:** VM Ubuntu nova, com Docker instalado.

**Passos:**

1. `git clone` do repositório numa pasta nova e `cd plataforma-monitoramento`.
2. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
3. `cp .env.exemplo .env` e `cp servicos/.env.exemplo servicos/.env`; preencher as senhas (valores inventados).
4. `pytest`.
5. `cd servicos && docker compose up -d --build && docker compose ps`.
6. `cd .. && MONITOR_INFRA=1 pytest tests/test_infra.py`.

**Resultado esperado:** passo 4 termina com `passed` e nenhum `failed`; passo 5 mostra os 4 containers `Up`; passo 6
termina sem `failed`.

**Evidência:** `testes/evidencias/T01-pytest.png` (saída do `pytest`) e `testes/evidencias/T01-containers.png`
(`docker compose ps` e o teste de infraestrutura).

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T02 — Visão consolidada no PC

**Objetivo:** mostrar a saúde dos 4 serviços numa única tela.

**Requisito:** front-end com visão consolidada.

**Pré-condições:** API, Coletor e dashboard rodando há pelo menos 2 minutos, com todos os serviços no ar.

**Passos:**

1. No navegador do PC (janela de 1366 px ou mais), abrir `http://<IP da VM>:8501`.
2. Ficar na página **Visão geral**.
3. Passar o mouse sobre o ⓘ de um serviço.

**Resultado esperado:** um cartão por serviço (WEB, DB, DNS, SMTP e, com o agente, HOST), todos 🟢 OK; "Última coleta"
com poucos segundos; tabela "Últimos alertas" (ou o aviso de que não há alertas).

**Evidência:** `testes/evidencias/T02-visao-geral-pc.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T03 — Dashboard por serviço

**Objetivo:** provar que cada serviço tem o seu dashboard com as métricas pedidas, com unidade, cor e histórico.

**Requisito:** front-end com dashboards por serviço; métricas recomendadas da seção 3 do enunciado.

**Pré-condições:** as do T02.

**Passos:**

1. Abrir a página **Por serviço**.
2. Escolher WEB e rolar a página até o fim.
3. Passar o mouse no ⓘ de `web.latencia_ms` para ver a descrição e os limites.
4. Repetir o passo 2 para DB, DNS, SMTP e HOST.

**Resultado esperado:** cada página lista todas as métricas do catálogo do serviço com unidade entre parênteses,
valor atual (ou "sem dados", em ⚪, quando a fonte ainda não envia), cor do nível e gráfico da última hora; o ⓘ mostra
os limites de Atenção e Crítico.

**Evidência:** `testes/evidencias/T03-web.png`, `T03-db.png`, `T03-dns.png`, `T03-smtp.png` e `T03-host.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T04 — Responsividade no celular

**Objetivo:** provar que o dashboard se adapta a telas estreitas.

**Requisito:** front-end responsivo.

**Pré-condições:** as do T02; celular na mesma rede da VM.

**Passos:**

1. No Chrome do PC, abrir as ferramentas do desenvolvedor (F12), ativar a barra de dispositivo e escolher 390 × 844.
2. Percorrer as quatro páginas (Visão geral, Por serviço, Alertas, Segurança).
3. No celular, abrir `http://<IP da VM>:8501` e percorrer as mesmas páginas.

**Resultado esperado:** os cartões empilham em uma coluna, nada fica cortado na horizontal e o seletor de páginas
continua acessível.

**Evidência:** `testes/evidencias/T04-devtools-390.png` e `testes/evidencias/T04-celular.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T05 — Páginas de alertas e segurança e API fora do ar

**Objetivo:** mostrar o histórico de alertas e de eventos de segurança, e que o dashboard avisa quando a API cai.

**Requisito:** front-end; regras de alerta.

**Pré-condições:** as do T02; de preferência depois do T06, para haver alertas na tabela.

**Passos:**

1. Abrir a página **Alertas**.
2. Abrir a página **Segurança**.
3. Parar a API (Ctrl+C no terminal 1) e esperar até 15 s.
4. Subir a API de novo (`python -m plataforma.api`).

**Resultado esperado:** Alertas mostra contagens e a tabela com horário, serviço, métrica, de/para com cor, valor,
limite e ✅/❌ do e-mail; Segurança mostra a contagem por tipo, os eventos e a linha de base; com a API parada, a tela
mostra "API indisponível" sem quebrar e volta ao normal quando a API sobe.

**Evidência:** `testes/evidencias/T05-alertas.png`, `T05-seguranca.png` e `T05-api-fora.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T06 — Queda do web: ATENÇÃO, CRÍTICO e e-mail

**Objetivo:** provar que a queda de um serviço gera alerta amarelo, depois vermelho, e e-mail em cada mudança.

**Requisito:** níveis de alerta 2 (Atenção) e 3 (Crítico); notificação por e-mail.

**Pré-condições:** todos os serviços 🟢; `NOTIFICADOR=smtp` (ou `arquivo`).

**Passos:**

1. `docker compose stop web`.
2. Esperar ~15 s e olhar a Visão geral.
3. Esperar mais ~15 s.
4. Abrir a caixa de entrada (ou a pasta `notificacoes/`).
5. Abrir a página Alertas.

**Resultado esperado:** WEB 🟡 ATENCAO no passo 2 e 🔴 CRITICO no passo 3; DB, DNS e SMTP continuam 🟢; dois e-mails
(`[ATENCAO] web — web.disponivel` e `[CRITICO] web — web.disponivel`); na página Alertas, as duas linhas com ✅.

**Evidência:** `testes/evidencias/T06-atencao.png`, `T06-critico.png` e `T06-email.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T07 — Queda do banco, do DNS e do SMTP

**Objetivo:** provar que a sonda de cada serviço detecta a queda pelo protocolo (não só pela porta).

**Requisito:** disponibilidade de cada serviço (seção 3); níveis 2 e 3.

**Pré-condições:** todos os serviços 🟢.

**Passos:**

1. `docker compose stop db`; esperar ~30 s; registrar a Visão geral; `docker compose start db`; esperar voltar ao 🟢.
2. Repetir o passo 1 com `dns`.
3. Repetir o passo 1 com `smtp`.

**Resultado esperado:** em cada rodada só o serviço parado vai a 🟡 e depois 🔴, com e-mail; os outros seguem 🟢.

**Evidência:** `testes/evidencias/T07-db.png`, `T07-dns.png` e `T07-smtp.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T08 — Degradação de latência: ATENÇÃO

**Objetivo:** provar que uma degradação (serviço lento, mas no ar) gera só o nível amarelo.

**Requisito:** nível 2 — Atenção (degradação que exige observação), com e-mail.

**Pré-condições:** todos os serviços 🟢; `tc` disponível na VM (pacote `iproute2`, já vem no Ubuntu).

**Passos:**

1. Atrasar só o tráfego para a porta 8080 (web) na interface local:
   `sudo tc qdisc add dev lo root handle 1: prio`,
   `sudo tc qdisc add dev lo parent 1:3 handle 30: netem delay 400ms` e
   `sudo tc filter add dev lo protocol ip parent 1:0 prio 3 u32 match ip dport 8080 0xffff flowid 1:3`.
2. Esperar ~30 s (2 coletas) e abrir Por serviço → WEB.
3. Remover o atraso: `sudo tc qdisc del dev lo root`.

**Resultado esperado:** `web.latencia_ms` passa de 500 ms (limite de Atenção) e fica abaixo de 2000 ms; WEB vai a
🟡 ATENCAO (não a vermelho) e sai um e-mail de ATENCAO; os outros serviços seguem 🟢.

**Evidência:** `testes/evidencias/T08-latencia.png` (gráfico com o degrau) e `testes/evidencias/T08-email.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:** a validar na VM se o atraso pega a porta publicada pelo Docker; se não pegar, aplicar o atraso na
interface do container (a combinar com P1).

### T09 — Recuperação: volta ao OK

**Objetivo:** provar que o alerta se encerra sozinho quando o serviço volta, sem oscilar.

**Requisito:** nível 1 — Verde (estado normal); histerese das regras.

**Pré-condições:** WEB em 🔴 (fim do T06).

**Passos:**

1. `docker compose start web`.
2. Olhar a Visão geral a cada 15 s por 1 minuto.
3. Abrir a página Alertas e a caixa de entrada.

**Resultado esperado:** WEB volta a 🟢 OK depois de 3 coletas normais (~45 s), sem passar por amarelo; na página
Alertas aparece a linha CRITICO → OK com ✅ e chega o e-mail de recuperação.

**Evidência:** `testes/evidencias/T09-recuperacao.png` e `testes/evidencias/T09-email.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T10 — Pico de tráfego (DDoS)

**Objetivo:** provar que um volume anormal de requisições é detectado como anomalia de tráfego.

**Requisito:** segurança — detecção de anomalias de tráfego (indicadores de DDoS).

**Pré-condições:** agente no ar e configurado (`agente_url`); plataforma coletando há pelo menos 5 minutos (20 amostras
de `web.rps`).

**Passos:**

1. Do notebook, rodar `bash testes/ataque_ddos.sh` (script da P1, só contra o container web).
2. Esperar 15 a 30 s e abrir Por serviço → WEB (gráfico de `web.rps`).
3. Abrir a página Segurança.
4. Parar o ataque.

**Resultado esperado:** `web.rps` dá um salto no gráfico; na Segurança aparece um evento TRAFEGO (🟡 com z ≥ 3 ou 🔴
com z ≥ 5) e sai um e-mail.

**Evidência:** `testes/evidencias/T10-rps.png` e `testes/evidencias/T10-evento.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T11 — Isolamento: ataque ao web não derruba os outros

**Objetivo:** provar a regra da professora: um ataque a um serviço não derruba os demais.

**Requisito:** isolamento dos serviços (decisão com a professora, CHECKLIST seção 10).

**Pré-condições:** as do T10.

**Passos:**

1. Durante o ataque do T10, abrir a Visão geral.
2. Na VM, rodar `docker stats --no-stream`.

**Resultado esperado:** DB, DNS e SMTP continuam 🟢 durante todo o ataque; `docker stats` mostra o web limitado ao seu
teto (1 CPU, 512 MB) e os outros containers com folga.

**Evidência:** `testes/evidencias/T11-visao-geral.png` e `testes/evidencias/T11-docker-stats.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T12 — Força bruta no login

**Objetivo:** provar que tentativas repetidas de senha a partir de um IP são detectadas.

**Requisito:** segurança — falhas de autenticação por conta/IP, detecção de brute-force.

**Pré-condições:** agente no ar lendo `/var/log/app/login.log`.

**Passos:**

1. Do notebook, rodar `python testes/ataque_brute_force.py` (script da P1, contra o login do site).
2. Esperar até 15 s e abrir a página Segurança.
3. Deixar o script chegar a 20 falhas em 60 s e olhar de novo.

**Resultado esperado:** evento AUTENTICACAO 🟡 ATENCAO com o IP de origem ao chegar a 5 falhas em 60 s, e 🔴 CRITICO
ao chegar a 20; um e-mail por subida de nível.

**Evidência:** `testes/evidencias/T12-atencao.png`, `T12-critico.png` e `T12-email.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T13 — Alteração de arquivo de configuração

**Objetivo:** provar que uma mudança num arquivo de configuração vigiado gera alerta.

**Requisito:** segurança — alertas de alterações de configuração.

**Pré-condições:** agente no ar calculando os hashes; linha de base definida com o sistema limpo
(`curl -X POST -H "X-Token: $MONITOR_TOKEN" http://127.0.0.1:5000/api/seguranca/linha-base`).

**Passos:**

1. `docker compose exec smtp sh -c 'echo "# teste T13" >> /etc/postfix/main.cf'`.
2. Esperar até 15 s e abrir a página Segurança.
3. Desfazer a alteração (remover a linha ou recriar o container) e refazer a linha de base.

**Resultado esperado:** evento CONFIGURACAO 🔴 CRITICO com o caminho `/etc/postfix/main.cf` e o hash diferente da
linha de base; um e-mail.

**Evidência:** `testes/evidencias/T13-evento.png` e `testes/evidencias/T13-email.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**

### T14 — Varredura de vulnerabilidades

**Objetivo:** registrar as vulnerabilidades conhecidas de cada serviço vigiado.

**Requisito:** segurança — monitoramento de vulnerabilidade conhecida por serviço.

**Pré-condições:** containers no ar; ferramenta de varredura instalada na VM (a definir no grupo, por exemplo
`nmap -sV` para as versões dos serviços e `nikto` para o site).

**Passos:**

1. `nmap -sV -p 8080,3307,1053,2525 127.0.0.1` e salvar a saída.
2. `nikto -h http://127.0.0.1:8080/` e salvar a saída.
3. Comparar as versões encontradas com as vulnerabilidades conhecidas (CVE) e com as mantidas de propósito no site
   (`docs/LOG.md`, 20/11: enumeração de usuários, login sem limite, XSS em `suaconta.php`, `display_errors` ligado).

**Resultado esperado:** relatório com a versão de cada serviço e as vulnerabilidades encontradas, incluindo as
mantidas de propósito no site.

**Evidência:** `testes/evidencias/T14-nmap.png` e `testes/evidencias/T14-nikto.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:** a plataforma ainda não gera eventos `VULNERABILIDADE` (`docs/arquitetura.md`, seção 8); responsável a
definir no grupo.

### T15 — Proteção da API e dos segredos

**Objetivo:** provar que só o Coletor grava dados e que nenhum segredo vai para o repositório.

**Requisito:** backend de ingestão; segurança do próprio repositório (CHECKLIST seção 8).

**Pré-condições:** API no ar.

**Passos:**

1. Sem token: `curl -i -X POST http://127.0.0.1:5000/api/ingest -H "Content-Type: application/json" -d '{"ts": 1, "amostras": []}'`.
2. Token errado: repetir com `-H "X-Token: errado"`.
3. Métrica fora do catálogo, com o token certo:
   `curl -i -X POST http://127.0.0.1:5000/api/ingest -H "Content-Type: application/json" -H "X-Token: $MONITOR_TOKEN" -d '{"ts": 1795036800, "amostras": [{"servico": "web", "metrica": "web.inventada", "valor": 1}]}'`.
4. `git check-ignore -v .env servicos/.env` e `git status`.

**Resultado esperado:** passos 1 e 2 respondem `401`; passo 3 responde `400` com o motivo; passo 4 mostra os dois
`.env` ignorados pelo `.gitignore` e o `git status` sem `.env`, `.db` ou senhas.

**Evidência:** `testes/evidencias/T15-api.png` e `testes/evidencias/T15-git.png`.

**Resultado:** [ ] Passou [ ] Falhou — data/hora: ____

**Observações:**
