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
