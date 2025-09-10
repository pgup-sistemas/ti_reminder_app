"""
Configuração de produção para TI Reminder App
"""
import os
import secrets

# Configurações básicas
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ti_reminder.db')
FLASK_ENV = 'production'
DEBUG = False
TESTING = False

# Configurações de log
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/ti_reminder.log'
LOG_TO_STDOUT = False

# Configurações de email (opcional)
MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')

# Timezone
TIMEZONE = os.getenv('TIMEZONE', 'America/Sao_Paulo')

# Scheduler
SCHEDULER_API_ENABLED = True
