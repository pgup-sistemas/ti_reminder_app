from flask import Flask
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from .email_utils import mail_init_app

mail = Mail()
db = SQLAlchemy()
scheduler = APScheduler()
migrate = Migrate()
bootstrap = Bootstrap()


def create_app():
    import logging
    import os
    from logging.handlers import RotatingFileHandler

    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Configuração de logging
    if not app.debug and not app.testing:
        # Criar diretório de logs se não existir
        log_dir = os.path.dirname(app.config["LOG_FILE"])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Configurar handler de arquivo
        file_handler = RotatingFileHandler(
            app.config["LOG_FILE"], maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(app.config["LOG_LEVEL"])

        # Adicionar handler ao logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(app.config["LOG_LEVEL"])
        app.logger.info("Inicialização do TI Reminder")

        # Se configurado, também logar para stdout
        if app.config.get("LOG_TO_STDOUT"):
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            stream_handler.setLevel(app.config["LOG_LEVEL"])
            app.logger.addHandler(stream_handler)

    db.init_app(app)
    mail_init_app(app, mail)
    scheduler.init_app(app)
    scheduler.start()
    migrate.init_app(app, db)
    bootstrap.init_app(app)

    from . import routes

    app.register_blueprint(routes.bp)

    # Registrar blueprint de autenticação
    from .auth import bp_auth

    app.register_blueprint(bp_auth, url_prefix="/auth")

    # Registrar filtros de template para timezone
    from .template_filters import register_template_filters

    register_template_filters(app)

    return app
