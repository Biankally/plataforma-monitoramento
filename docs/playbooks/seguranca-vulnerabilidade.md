# Playbook — Segurança: vulnerabilidade conhecida

## Sintoma
Evento `VULNERABILIDADE` na página Segurança do dashboard, com e-mail. O detalhe traz o CVE, o programa, a versão
encontrada e a versão que corrige a falha. Exemplo: `CVE-2024-8508: ... (versao 1.20.0; corrigido em 1.21.1)` no `dns`.

## Diagnóstico
1. Confira a versão real no container: `dc exec dns unbound -V`, `dc exec web apache2 -v`, `dc exec web php -v`,
   `dc exec db mysqld --version`, `dc exec smtp postconf -h mail_version`.
2. Abra a fonte do CVE (campo `fonte` em `config/vulnerabilidades.toml`) e veja se a falha atinge a configuração usada
   (ex.: falhas só de Windows ou de módulos desligados não se aplicam ao laboratório).
3. Veja se a distribuição da imagem já corrigiu sem trocar o número (backport): aviso de segurança do Alpine
   (`secdb.alpinelinux.org`) ou do Debian (`security-tracker.debian.org`). Se já corrigiu, é falso positivo.

## Ação
1. **Falha real:** atualize a imagem (`dc build --pull <serviço> && dc up -d <serviço>`) ou troque a tag no
   `servicos/docker-compose.yml` / `Dockerfile` por uma versão corrigida; confira a versão de novo (passo 1).
2. **Falso positivo ou não aplicável:** registre a justificativa no `docs/LOG.md`. Se for definitivo, ajuste a entrada
   no `config/vulnerabilidades.toml` (ex.: `ramo`) citando a fonte.
3. **CVE novo publicado:** acrescente uma entrada no `config/vulnerabilidades.toml` com a fonte oficial e reinicie a API.
