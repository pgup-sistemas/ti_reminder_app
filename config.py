import os
import secrets
from datetime import timezone, timedelta

def _env_bool(name, default):
    val = os.environ.get(name, default)
    return str(val).lower() in ("1", "true", "t", "yes", "y")

class Config:
    """Configuração base da aplicação."""
    
    # Ambiente
    # FLASK_ENV está deprecado no Flask 2.3+, usar apenas DEBUG
    DEBUG = _env_bool('DEBUG', 'True')
    TESTING = _env_bool('TESTING', 'False')
    
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Sessões seguras
    SESSION_COOKIE_SECURE = False  # Será True em produção (HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Token nunca expira (apenas com a sessão)
    WTF_CSRF_SSL_STRICT = False  # Será True em produção
    
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
    MAIL_USE_TLS = _env_bool('MAIL_USE_TLS', 'True')
    MAIL_USE_SSL = _env_bool('MAIL_USE_SSL', 'False')
    MAIL_SUPPRESS_SEND = _env_bool('MAIL_SUPPRESS_SEND', 'False')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'pageupsistemas@gmail.com')
    MAIL_USERNAME = MAIL_USERNAME.strip() if MAIL_USERNAME else None
    MAIL_PASSWORD = MAIL_PASSWORD.replace(' ', '') if MAIL_PASSWORD else None
    
    # Email do grupo TI para receber notificações de chamados
    TI_EMAIL_GROUP = os.environ.get('TI_EMAIL_GROUP', 'ti@alphaclin.net.br')

    # Base URL usada em links externos nos e-mails (reset de senha, chamados)
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Flask URL building (necessário para url_for fora de contexto de requisição)
    # SERVER_NAME é usado pelo Flask para construir URLs fora de contexto de requisição
    # Em desenvolvimento, usar 127.0.0.1 para evitar warnings
    SERVER_NAME = os.environ.get('SERVER_NAME', '127.0.0.1:5000')
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'

    # Criptografia de segredos de configurações
    CONFIG_SECRET_KEY = os.environ.get('CONFIG_SECRET_KEY')
    
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
    SECURITY_LOG_FILE = os.environ.get('SECURITY_LOG_FILE', 'logs/security.log')
    
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
            'security': {
                'format': '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'WARNING',
                'formatter': 'simple',
            },
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/security.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'formatter': 'security',
                'level': 'INFO',
            },
        },
        'loggers': {
            'werkzeug': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
            'apscheduler': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
            'sqlalchemy': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
            'security': {'handlers': ['security_file', 'console'], 'level': 'INFO', 'propagate': False},
        },
    }
    
    # Scheduler
    SCHEDULER_API_ENABLED = os.environ.get('SCHEDULER_API_ENABLED', 'True').lower() == 'true'

    # Uploads de imagens (profissional)
    ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}
    MAX_IMAGE_UPLOAD_MB = int(os.environ.get('MAX_IMAGE_UPLOAD_MB', 3))
    IMAGE_MAX_WIDTH = int(os.environ.get('IMAGE_MAX_WIDTH', 1600))
    IMAGE_MAX_HEIGHT = int(os.environ.get('IMAGE_MAX_HEIGHT', 1200))
    IMAGE_JPEG_QUALITY = int(os.environ.get('IMAGE_JPEG_QUALITY', 85))


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    LOG_TO_STDOUT = True
    
    # Sessões seguras em produção (HTTPS obrigatório)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # CSRF mais rígido em produção
    WTF_CSRF_SSL_STRICT = True
    
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError(
                "SECRET_KEY deve estar definida no ambiente de produção."
            )
        return key
    
    @property
    def JWT_SECRET_KEY(self):
        key = os.environ.get('JWT_SECRET_KEY')
        if not key:
            raise ValueError(
                "JWT_SECRET_KEY deve estar definida no ambiente de produção."
            )
        return key
    
    def __init__(self):
        super().__init__()
        # Validar configurações obrigatórias de email em produção
        if not os.environ.get('MAIL_USERNAME'):
            raise ValueError("MAIL_USERNAME deve estar definido em produção.")
        if not os.environ.get('MAIL_PASSWORD'):
            raise ValueError("MAIL_PASSWORD deve estar definido em produção.")


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/ti_reminder_test'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env_name=None):
    if env_name is None:
        # Usar APP_ENV ao invés de FLASK_ENV (deprecado no Flask 2.3+)
        env_name = os.environ.get('APP_ENV', 'development')
    return config_map.get(env_name, DevelopmentConfig)
