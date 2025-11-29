# Guia de Configuração para Produção

## Variáveis de Ambiente Obrigatórias
- `APP_ENV=production`
- `SECRET_KEY` e `JWT_SECRET_KEY` com 64+ caracteres
- `DATABASE_URL` do provedor (ex.: PostgreSQL)
- `BASE_URL` com seu domínio HTTPS (ex.: `https://suaempresa.com`)
- `MAIL_SERVER=smtp.gmail.com`
- `MAIL_PORT=587`
- `MAIL_USE_TLS=True`
- `MAIL_USERNAME=seu_email@gmail.com`
- `MAIL_PASSWORD` (Senha de App do Gmail)
- `MAIL_DEFAULT_SENDER=seu_email@gmail.com`
- `MAIL_SUPPRESS_SEND=False`

## Gmail – Senha de App
- Ative 2FA na conta Gmail.
- Gere em `https://myaccount.google.com/apppasswords`.
- Cole no `.env` como quatro grupos com espaços; o sistema normaliza.
- Remetente e usuário devem coincidir.

## Links em E-mails
- Defina `BASE_URL` para seu domínio público HTTPS.
- O reset de senha monta o link usando `BASE_URL`.

## Banco de Dados
- Use `DATABASE_URL` fornecido pelo provedor.
- O sistema ajusta `postgres://` para `postgresql://` automaticamente.

## Carregamento de Configuração
- O app seleciona a classe via `APP_ENV` e instancia para validar obrigatórios.
- Em produção: `DEBUG=False`, `SESSION_COOKIE_SECURE=True`.

## Verificações Rápidas
- Teste SMTP pela interface: `/integracoes/email`.
- Teste reset: “Esqueceu a senha?” e confirme recebimento.
- Logs em `logs/security.log` para auditoria.

## Segurança
- Cookies seguros, CSRF rígido em produção.
- Limiter configurado; para produção use storage externo se necessário.

## Passos de Deploy
- Defina variáveis no provedor.
- Rode migrações do banco se aplicável.
- Inicie o app e valide saúde/rotas críticas.