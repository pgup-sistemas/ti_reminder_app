#!/usr/bin/env python3
"""Script para recriar o arquivo .env com encoding correto"""

env_content = """APP_ENV=development
DEBUG=True
TESTING=False

# Banco de dados SQLite local (caminho absoluto para evitar erros)
DATABASE_URL=sqlite:///C:/Users/osn/Documents/ti_reminder_app/instance/ti_reminder_app.db

# Logging
LOG_TO_STDOUT=True
LOG_LEVEL=INFO

# ========================================
# TI OSN SYSTEM - Variáveis de Ambiente
# ========================================

# AMBIENTE
APP_ENV=development
DEBUG=True
TESTING=False

# SEGURANÇA (OBRIGATÓRIAS EM PRODUÇÃO)
SECRET_KEY=your-secret-key-here-64-characters-minimum
JWT_SECRET_KEY=your-jwt-secret-key-here-64-characters-minimum

# BANCO DE DADOS
DATABASE_URL=sqlite:///C:/Users/osn/Documents/ti_reminder_app/instance/ti_reminder_app.db

# EMAIL (OBRIGATÓRIAS EM PRODUÇÃO)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=pageupsistemas@gmail.com
MAIL_PASSWORD=pqex fqow whrd mqoy
MAIL_SUPPRESS_SEND=False
BASE_URL=http://127.0.0.1:5000
MAIL_DEFAULT_SENDER=pageupsistemas@gmail.com

# Email do grupo TI para receber notificações de chamados
TI_EMAIL_GROUP=ti@alphaclin.net.br

# TIMEZONE
TIMEZONE=America/Porto_Velho

# JWT
JWT_EXPIRES_HOURS=1

# LOGGING
LOG_TO_STDOUT=True
LOG_LEVEL=WARNING
LOG_FILE=logs/ti_reminder.log
SECURITY_LOG_FILE=logs/security.log
SQL_ECHO=False

# SCHEDULER
SCHEDULER_API_ENABLED=True

# CONFIGURAÇÃO SEGURA - CHAVE FERNET
CONFIG_SECRET_KEY=FxBx2thNnf7SL1Nr6f6esaiBEV0RyiJHue8bE6_u61U=
"""

# Escrever arquivo com encoding UTF-8
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("Arquivo .env recriado com sucesso!")
print("CONFIG_SECRET_KEY configurada:", "CONFIG_SECRET_KEY" in env_content)
