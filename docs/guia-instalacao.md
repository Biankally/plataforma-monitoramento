# Guia de instalação (do zero)

Este guia monta o ambiente inteiro num computador com Windows 10/11 e 16 GB de RAM.
Quem seguir só este guia termina com os 4 serviços vigiados, o agente, a plataforma e o dashboard rodando.

## 1. Visão geral

```
Windows
└── WSL2 (Ubuntu 24.04)  ← "VM-S" e "VM-P" ficam na mesma VM Linux leve
    ├── Docker Desktop (integração com o WSL)
    │   ├── web   Apache + PHP + site Receitas Práticas   127.0.0.1:8080
    │   ├── db    MySQL 8.0                               127.0.0.1:3307
    │   ├── dns   Unbound (zona lab.local)                127.0.0.1:1053
    │   └── smtp  Postfix                                 127.0.0.1:2525
    ├── agente    servicos/agente/agente.py               127.0.0.1:9101
    └── plataforma (Python)
        ├── API Flask                                     127.0.0.1:5000
        ├── coletor (a cada 15 s)
        └── dashboard Streamlit                           127.0.0.1:8501
```

- **Por que containers e não duas VMs:** a professora liberou containers, desde que um ataque a um serviço não derrube os outros. Cada container tem teto de CPU, memória e processos (`servicos/docker-compose.yml`). O `tests/test_infra.py` e o `testes/teste_isolamento.py` provam isso.
- **Por que portas diferentes das padrão:** 80 e 3306 já são usadas pelo XAMPP, e 53 e 25 pelo Windows. Todas as portas ficam presas em `127.0.0.1`: nada fica exposto na rede da faculdade.

## 2. Pré-requisitos (uma vez por computador)

1. **WSL2 com Ubuntu.** No PowerShell como administrador: `wsl --install -d Ubuntu-24.04`. Reinicie e crie o usuário do Ubuntu.
2. **Docker Desktop.** Instale do site oficial e abra *Settings → Resources → WSL integration*. Ligue a integração com o **Ubuntu-24.04**. Não instale outro Docker dentro do Ubuntu (`docker.io`), porque ele entra em conflito com o Docker Desktop.
3. **Git e Python no Ubuntu.** Abra o terminal do Ubuntu (comando `wsl` no PowerShell) e rode:
   ```bash
   sudo apt update && sudo apt install -y git python3-venv unzip
   docker --version && docker compose version     # precisa responder as duas versões
   ```
4. **Acesso ao GitHub:** chave SSH e e-mail `noreply`, como está no `COMECE_AQUI.md`, passo 1.

## 3. Baixar o projeto e preparar o Python

```bash
cd ~ && git clone git@github.com:Biankally/plataforma-monitoramento.git
cd plataforma-monitoramento
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                        # tem que terminar com "passed" e nenhum "failed"
```

## 4. Arquivos de segredos (`.env`)

Os dois arquivos ficam **fora do Git** (estão no `.gitignore`). As senhas são geradas na hora e não aparecem na tela.

```bash
# Plataforma e agente
cp .env.exemplo .env
sed -i "s/^MONITOR_TOKEN=.*/MONITOR_TOKEN=$(openssl rand -hex 24)/" .env
sed -i "s/^MONITOR_AGENTE_TOKEN=.*/MONITOR_AGENTE_TOKEN=$(openssl rand -hex 24)/" .env

# Containers
cp servicos/.env.exemplo servicos/.env
sed -i "s/^MYSQL_ROOT_PASSWORD=.*/MYSQL_ROOT_PASSWORD=$(openssl rand -hex 16)/" servicos/.env
sed -i "s/^SITE_DB_SENHA=.*/SITE_DB_SENHA=$(openssl rand -hex 16)/" servicos/.env
sed -i "s/^MONITOR_DB_SENHA=.*/MONITOR_DB_SENHA=$(openssl rand -hex 16)/" servicos/.env

# A plataforma tambem precisa da senha do monitor (sonda do banco): copia do servicos/.env
sed -i "s/^MONITOR_DB_SENHA=.*/$(grep ^MONITOR_DB_SENHA= servicos/.env)/" .env
```

Para o e-mail de alerta sair de verdade, preencha `NOTIFICADOR=smtp` e as linhas `SMTP_*` do `.env` com uma **senha de app** criada só para isso. Sem isso, os e-mails ficam como arquivo na pasta `notificacoes/`.

## 5. Subir os serviços vigiados

```bash
cd servicos
mkdir -p logs/web                 # login.log e acesso.log do site (o agente lê daqui)
docker compose up -d --build      # na 1ª vez baixa as imagens (alguns minutos)
docker compose ps                 # os 4 com STATUS "Up"
docker stats --no-stream          # coluna LIMIT mostra o teto de memória de cada um
cd ..
```

Na **primeira** subida, o MySQL roda sozinho o `servicos/banco/init.sql` e o `02-monitor.sh`, que criam as tabelas, os dados inventados e o usuário `monitor` só de leitura. Espere uns 30 s antes de testar. Para recriar o banco do zero: `docker compose down -v` (isso apaga só os dados do laboratório).

Abra http://127.0.0.1:8080 no navegador: o site tem que aparecer.

## 6. Subir o agente, a plataforma e o dashboard

Abra 4 terminais do Ubuntu e, em cada um, rode antes `cd ~/plataforma-monitoramento && source .venv/bin/activate`:

| Terminal | Comando | Deixa rodando |
| --- | --- | --- |
| 1 | `python servicos/agente/agente.py` | agente na porta 9101 |
| 2 | `python -m plataforma.api` | API na porta 5000 |
| 3 | `python -m plataforma.infra.coletor` | coleta a cada 15 s |
| 4 | `streamlit run plataforma/dashboard/app.py` | dashboard em http://127.0.0.1:8501 |

## 7. Conferir que tudo funciona

```bash
pytest -q                                      # testes sem containers
MONITOR_INFRA=1 pytest tests/test_infra.py -q  # testes com os containers de verdade (~30 s)
```

O segundo comando confere várias coisas:
- os 4 serviços respondem e cada container tem limite;
- o site está no ar e login certo e errado viram linhas no log;
- o "esqueci a senha" entrega o e-mail e o `monitor` só lê;
- o DNS resolve e o SMTP registra a entrega no log;
- o agente lê os containers e uma alteração de configuração muda o hash;
- um DDoS de 15 s no web não derruba os outros.

## 8. Problemas comuns

| Sintoma | Causa provável | O que fazer |
| --- | --- | --- |
| `docker: command not found` no Ubuntu | Integração do Docker Desktop com o WSL desligada | Docker Desktop → Settings → Resources → WSL integration → ligar Ubuntu-24.04 |
| `required variable ... is missing` | Faltou linha no `servicos/.env` | Refaça o passo 4 |
| Site mostra "Falha na conexão com o banco" | O MySQL ainda está iniciando, ou o banco é antigo | Espere 30 s; se continuar, `docker compose down -v && docker compose up -d` |
| `port is already allocated` | Outra coisa usa a porta (ex.: XAMPP) | Pare o outro programa ou mude a porta no compose **e** no `config/servicos.toml` |
| Agente: `MONITOR_AGENTE_TOKEN vazio` | Faltou o token no `.env` da raiz | Refaça o passo 4 |
| Comando colado no PowerShell não funciona | Era para o terminal do Ubuntu | Rode `wsl` primeiro |

Operação de cada serviço (iniciar, parar, verificar, reiniciar): `docs/runbooks/`.
