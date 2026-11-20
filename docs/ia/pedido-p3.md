# Pedido P3 — Dashboard, Testes e Documento (branches `c/...`)

Cole este arquivo na IA junto com o `AGENTS.md`. Faça uma tarefa por vez, na ordem.

## Contexto
O dashboard em Streamlit (`plataforma/dashboard/app.py`) já mostra a visão consolidada e um gráfico por métrica,
lendo **só pela API**. Sua parte é deixá-lo completo e responsivo, provar com testes que o sistema atende ao
enunciado e montar o PDF em ABNT.

## Tarefas
| # | Arquivo(s) | O que fazer | Pronto quando | Prazo |
| --- | --- | --- | --- | --- |
| 1 | `plataforma/dashboard/app.py` | Página por serviço (todas as métricas do catálogo, com unidade), página de alertas (`/api/alertas`) e de segurança (`/api/seguranca`), cores verde/amarelo/vermelho | Teste com `streamlit.testing.v1.AppTest` contra a API do termômetro; sem `exception` | 21/11 20h |
| 2 | (mesmo arquivo) | Responsividade: colunas que empilham no celular | Print no PC e no celular (DevTools, largura 390 px) | 22/11 12h |
| 3 | `testes/roteiro.md` | Casos T01 a T15 (seção 13 da arquitetura), cada um com passos, resultado esperado e campo para o print | Revisado por P1 e P2 | 22/11 20h |
| 4 | `testes/evidencias/` | Executar os casos nas VMs reais e guardar os prints (legíveis, com o ponto importante destacado) | Todos os casos com evidência | 23/11 20h |
| 5 | `relatorio/` | PDF em ABNT (NBR 14724:2024, 6023:2018, 10520:2023) com os capítulos de todos e a URL do Git | Conferido item a item contra a norma | 24/11 12h |
| 6 | `README.md`, `CHECKLIST.md` | Manter atualizados a cada marco | `CHECKLIST.md` 100% conferido na véspera | 24/11 20h |

## Interfaces que você consome (não mude sem combinar)
- `GET /api/status` → `{"atualizado_em": int|null, "servicos": [{"servico", "nivel", "pior_metrica"}]}`;
  `nivel` é `OK`, `ATENCAO`, `CRITICO` ou `SEM_DADOS`.
- `GET /api/metricas?metrica=&desde=&ate=` → `{"metrica", "servico", "pontos": [{"ts", "valor"}]}`.
- `GET /api/alertas?limite=50` → `{"alertas": [...]}` (colunas da tabela `alerta`).
- Unidades e descrições: `METRICAS` em `plataforma/contrato/metricas.py`.
