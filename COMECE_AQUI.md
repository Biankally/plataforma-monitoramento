# Comece aqui

Faça na ordem, no **terminal do WSL (Ubuntu)**. Quando o passo 5 der verde, mande o print no grupo.

1. **Chave SSH no GitHub** (uma vez por computador)
   ```bash
   git config --global user.name "Seu Nome"
   git config --global user.email "NUMERO+usuario@users.noreply.github.com"   # GitHub > Settings > Emails
   ssh-keygen -t ed25519 -C "seu-email"            # Enter em tudo; crie uma passphrase
   cat ~/.ssh/id_ed25519.pub                        # copie e cole em GitHub > Settings > SSH keys
   ssh -T git@github.com                            # deve responder "Hi usuario!"
   ```
2. **Baixar o projeto**
   ```bash
   cd ~ && git clone git@github.com:Biankally/plataforma-monitoramento.git && cd plataforma-monitoramento
   ```
3. **Ambiente Python**
   ```bash
   sudo apt update && sudo apt install -y python3-venv
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Configuração local**: `cp .env.exemplo .env` (o `.env` nunca vai para o Git).
5. **Prova de que funcionou**: `pytest` → tem que terminar com `passed` e nenhum `failed`. **Print e grupo.**
6. **Sua parte**: leia `AGENTS.md` e o seu pedido em `docs/ia/` (P1, P2 ou P3). Cole os dois na sua IA.

## Deu erro? Faça isto

| Erro | Solução |
| --- | --- |
| `Permission denied (publickey)` | A chave não foi cadastrada no GitHub: refaça o passo 1 |
| `push declined ... private email` | O e-mail do Git não é o `noreply`: refaça o `git config user.email` |
| `No module named venv` / `ensurepip` | `sudo apt install -y python3-venv` |
| `ModuleNotFoundError: flask` (ou outro) | Ative o ambiente: `source .venv/bin/activate` |
| `ModuleNotFoundError: plataforma` | Rode os comandos a partir da pasta do projeto |
| Teste vermelho logo após clonar | Não mexa em nada: mande o print no grupo |
