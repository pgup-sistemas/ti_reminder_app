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

    # Configurar tarefas agendadas para notificações
    with app.app_context():
        from .services.notification_service import NotificationService
        from .services.satisfaction_service import SatisfactionService
        from .services.certification_service import CertificationService
        from .services.performance_service import PerformanceService

        # Agendar verificação de notificações a cada hora
        scheduler.add_job(
            id='check_notifications',
            func=NotificationService.run_notification_checks,
            trigger='interval',
            hours=1,
            max_instances=1,
            replace_existing=True
        )

        # Agendar tarefa de envio automático de pesquisas de satisfação
        scheduler.add_job(
            id='auto_send_satisfaction_surveys',
            func=SatisfactionService.auto_send_satisfaction_surveys,
            trigger='interval',
            hours=6,  # A cada 6 horas
            max_instances=1,
            replace_existing=True
        )

        # Agendar tarefa de atualização automática de certificações
        scheduler.add_job(
            id='auto_update_certifications',
            func=CertificationService.auto_update_certifications,
            trigger='interval',
            hours=1,  # A cada hora
            max_instances=1,
            replace_existing=True
        )

        # Agendar tarefa de monitoramento de performance
        scheduler.add_job(
            id='performance_monitoring',
            func=PerformanceService.generate_performance_report,
            trigger='interval',
            hours=4,  # A cada 4 horas
            max_instances=1,
            replace_existing=True
        )

        app.logger.info("Tarefa agendada de notificações configurada (a cada 1 hora)")
        app.logger.info("Tarefa agendada de pesquisas de satisfação configurada (a cada 6 horas)")
        app.logger.info("Tarefa agendada de certificações configurada (a cada 1 hora)")

    from . import routes
    app.register_blueprint(routes.bp)

    # Registrar blueprint de autenticação
    from .auth import bp_auth
    app.register_blueprint(bp_auth, url_prefix="/auth")

    # Registrar filtros de template para timezone
    from .template_filters import register_template_filters
    register_template_filters(app)

    # 🔥 Logar o banco de dados realmente configurado
    app.logger.info(f"SQLAlchemy conectado em: {app.config['SQLALCHEMY_DATABASE_URI']}")

    return app
