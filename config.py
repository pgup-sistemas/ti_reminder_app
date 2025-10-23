import os
import secrets
from datetime import timezone, timedelta

class Config:
    """Configuração base da aplicação."""
    
    # Ambiente
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
    
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Banco de dados
    # Render define DATABASE_URL automaticamente, mas localmente usamos localhost
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Ajuste para Render: PostgreSQL usa esquema 'postgresql://', mas Render pode enviar 'postgres://'
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    else:
        # Fallback para localhost (desenvolvimento)
        db_url = "postgresql://postgres:postgres@localhost:5432/ti_reminder_db"

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG and os.environ.get('SQL_ECHO', 'False').lower() == 'true'
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'reminder@example.com')
    
    # Timezone
    TIMEZONE = timezone(timedelta(hours=-4))
    TIMEZONE_NAME = os.environ.get('TIMEZONE', 'America/Porto_Velho')
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_EXPIRES_HOURS', 1)))
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'True').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/ti_reminder.log')
    
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'WARNING',
                'formatter': 'simple',
            },
        },
        'loggers': {
            'werkzeug': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
            'apscheduler': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
            'sqlalchemy': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        },
    }
    
    # Scheduler
    SCHEDULER_API_ENABLED = os.environ.get('SCHEDULER_API_ENABLED', 'True').lower() == 'true'


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    LOG_TO_STDOUT = True
    
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError(
                "SECRET_KEY deve estar definida no ambiente de produção."
            )
        return key


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/ti_reminder_test'
    WTF_CSRF_ENABLED = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env_name=None):
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env_name, DevelopmentConfig)
