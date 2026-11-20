# AGENTS.md — regras para qualquer IA que mexer neste repositório

Leia tudo antes de escrever código. Estas regras são ordens, não sugestões.

## O projeto em 3 linhas
Plataforma de monitoramento (trabalho final de Redes, IDP). Um Coletor mede 4 serviços (web, banco, DNS, SMTP),
envia as medições para uma API Flask, que grava em SQLite, avalia alertas (verde/amarelo/vermelho) e manda e-mail.
Um dashboard em Streamlit mostra tudo. Os serviços vigiados rodam em containers numa VM separada.

## Regra de camadas (verificada por `tests/test_camadas.py`)
Um arquivo só importa da **própria camada ou de camadas abaixo**:

| Camada | Pasta | Pode importar |
| --- | --- | --- |
| 0 contrato | `plataforma/contrato/` | só biblioteca padrão |
| 1 domínio | `plataforma/dominio/` | contrato (Python puro: sem rede, banco, arquivo ou e-mail) |
| 2 infra | `plataforma/infra/` | contrato, domínio |
| 3 api | `plataforma/api/` | contrato, domínio, infra |
| 4 dashboard | `plataforma/dashboard/` | contrato (lê dados **só pela API**, via HTTP) |

`servicos/agente/` é um programa separado (roda na VM-S) e não importa nada de `plataforma/`.

## Proibido
1. Mudar nome de métrica, formato de JSON, rota da API ou assinatura de função pública sem combinar com o grupo.
   O contrato está em `plataforma/contrato/metricas.py` e o JSON do agente em `tests/falsos/agente_exemplo.json`.
2. Adicionar biblioteca fora do `requirements.txt` (flask, requests, streamlit, pymysql, dnspython, pytest).
3. Colocar senha, token, e-mail real ou dado real em qualquer arquivo. Tudo sensível vem do `.env`.
4. Esconder erro: nada de `except:` vazio ou `except Exception: pass`.
5. Mexer em arquivo fora da pasta da sua tarefa ou "melhorar" o que não foi pedido.
6. Apagar ou enfraquecer um teste para ele passar.

## Obrigatório
1. **Teste antes do código:** escreva o teste, rode e veja falhar; depois implemente.
2. **Teste de sabotagem:** toda verificação tem um caso que estraga o resultado e exige que o teste acuse.
3. Todo `open()` / `read_text()` / `write_text()` com `encoding="utf-8"`.
4. Caminhos sempre com `pathlib.Path`; nunca texto com `\`.
5. Subprocesso sempre com `sys.executable`, nunca `"python"`.
6. Código simples, com nomes e comentários em português.
7. Uma responsabilidade por arquivo.
8. **Toda mudança registra uma entrada no fim de `docs/LOG.md`**, no mesmo commit (modelo no topo do arquivo):
   quem, o que mudou, por quê, arquivos, verificação (comando e resultado) e pendências.

## Comandos
```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                                   # todos os testes (precisam ficar verdes)
python -m plataforma.api                 # sobe a API (porta 5000)
python -m plataforma.infra.coletor       # coleta a cada 15 s (--uma-vez para um ciclo)
streamlit run plataforma/dashboard/app.py
```

## Definição de pronto
Uma tarefa só está pronta quando: (1) o teste dela existe e passa, (2) o teste de sabotagem acusa,
(3) `pytest` inteiro está verde, (4) a entrada em `docs/LOG.md` foi escrita, (5) o critério "pronto quando" do pedido em `docs/ia/` foi cumprido.

## Git
- Branch por tarefa com prefixo do dono: `a/...` (P1), `b/...` (P2), `c/...` (P3). Nunca commit direto na `main`.
- Commits no padrão Conventional Commits: `feat(coletor): ...`, `fix(api): ...`, `test(...)`, `docs(...)`.
- Pull request pequeno: o arquivo, o teste dele e a documentação dele.
- Antes de todo commit: `git status` sem `.env`, banco `.db`, planilhas ou senhas.
