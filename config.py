import os
from datetime import timezone, timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'changeme'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///reminder.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'reminder@example.com'
    
    # Configuração de timezone para Porto Velho, Rondônia (UTC-4)
    TIMEZONE = timezone(timedelta(hours=-4))
    TIMEZONE_NAME = 'America/Porto_Velho'
    
    # Configuração de logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = 'logs/ti_reminder.log'
