# Monkey patch para resolver problemas de compatibilidade Flask/Werkzeug
import sys
from markupsafe import Markup

# Adicionar Markup ao módulo flask antes de importar flask_wtf
import flask
flask.Markup = Markup
sys.modules['flask'].Markup = Markup

# Adicionar url_encode ao werkzeug.urls para compatibilidade
try:
    from werkzeug import urls
    if not hasattr(urls, 'url_encode'):
        from urllib.parse import urlencode
        urls.url_encode = urlencode
except (ImportError, AttributeError):
    pass

from flask import Flask
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

from .email_utils import mail_init_app

mail = Mail()
db = SQLAlchemy()
scheduler = APScheduler()
migrate = Migrate()
bootstrap = Bootstrap()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
login_manager = LoginManager()
talisman = Talisman()


def create_app():
    import logging
    import os
    from logging.handlers import RotatingFileHandler
    import logging.config

    app = Flask(__name__)
    app.config.from_object("config.Config")
    
    # Configuração de logging
    logging.config.dictConfig(app.config.get('LOGGING_CONFIG', {}))
    
    # Configuração adicional para o logger principal
    app.logger.setLevel(app.config['LOG_LEVEL'])
    
    # Remover handlers existentes
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    
    # Configurar handler para arquivo de log
    if not app.debug and not app.testing:
        # Criar diretório de logs se não existir
        log_dir = os.path.dirname(app.config["LOG_FILE"])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = RotatingFileHandler(
            app.config["LOG_FILE"], 
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(app.config["LOG_LEVEL"])
        app.logger.addHandler(file_handler)
    
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

    # Configuração de log para desenvolvimento
    if app.debug or app.testing:
        # Configuração mínima para desenvolvimento
        logging.basicConfig(level=logging.WARNING)
        # Suprimir logs desnecessários
        for logger in ['werkzeug', 'apscheduler', 'sqlalchemy.engine', 'urllib3.connectionpool', 'flask_limiter']:
            logging.getLogger(logger).setLevel(logging.WARNING)
        # Suprimir avisos específicos do Flask-Limiter
        import warnings
        warnings.filterwarnings('ignore', message='Using the in-memory storage for tracking rate limits')

    db.init_app(app)
    mail_init_app(app, mail)
    jwt.init_app(app)
    
    # Configurar o Limiter após a criação do app
    limiter.init_app(app)
    
    # Configurar storage em memória para o Limiter e suprimir avisos
    if not app.config.get('TESTING', False):
        limiter.storage_backend = 'memory'
        limiter.storage_uri = 'memory://'  # Configura explicitamente o storage em memória
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    scheduler.init_app(app)
    scheduler.start()
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    
    # Configurar headers de segurança HTTP com Talisman
    if not app.config.get('TESTING', False):
        csp = {
            'default-src': "'self'",
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Necessário para Bootstrap e alguns scripts inline
                "'unsafe-eval'",   # Necessário para alguns frameworks JS
                'cdn.jsdelivr.net',
                'code.jquery.com',
                'stackpath.bootstrapcdn.com',
                'cdnjs.cloudflare.com'
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",  # Necessário para estilos inline
                'cdn.jsdelivr.net',
                'stackpath.bootstrapcdn.com',
                'cdnjs.cloudflare.com',
                'fonts.googleapis.com'
            ],
            'font-src': [
                "'self'",
                'cdn.jsdelivr.net',
                'cdnjs.cloudflare.com',
                'fonts.gstatic.com',
                'data:'
            ],
            'img-src': [
                "'self'",
                'data:',
                'https:'
            ],
            'connect-src': "'self'",
            'frame-ancestors': "'none'",
            'base-uri': "'self'",
            'form-action': "'self'"
        }
        
        talisman.init_app(
            app,
            force_https=app.config.get('SESSION_COOKIE_SECURE', False),
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 ano
            strict_transport_security_include_subdomains=True,
            content_security_policy=csp,
            content_security_policy_report_only=False,
            referrer_policy='strict-origin-when-cross-origin',
            feature_policy={
                'geolocation': "'none'",
                'midi': "'none'",
                'notifications': "'self'",
                'push': "'self'",
                'sync-xhr': "'self'",
                'microphone': "'none'",
                'camera': "'none'",
                'magnetometer': "'none'",
                'gyroscope': "'none'",
                'speaker': "'self'",
                'vibrate': "'none'",
                'fullscreen': "'self'",
                'payment': "'none'"
            }
        )

    # Configurar contexto de aplicação para disponibilizar variáveis em todos os templates
    @app.context_processor
    def inject_pending_approvals():
        from flask_login import current_user
        from .services.equipment_service import EquipmentService
        
        # Inicializa com valor padrão
        pending_count = 0
        
        # Verifica se o usuário está autenticado e tem permissão
        if current_user.is_authenticated and (current_user.is_admin or current_user.is_ti):
            try:
                pending_count = EquipmentService.count_pending_approvals()
            except Exception as e:
                app.logger.error(f"Erro ao contar aprovações pendentes: {str(e)}")
                pending_count = 0
        
        return {'pending_approvals_count': pending_count}

    # Configurar tarefas agendadas para notificações
    with app.app_context():
        from .services.notification_service import NotificationService
        from .services.satisfaction_service import SatisfactionService
        from .services.certification_service import CertificationService
        from .services.performance_service import PerformanceService
        from .services.reminder_service import ReminderService

        # Funções wrapper para garantir contexto da aplicação
        def run_notification_checks_with_context():
            with app.app_context():
                return NotificationService.run_notification_checks()
        
        def process_recurring_reminders_with_context():
            with app.app_context():
                return ReminderService.process_recurring_reminders()

        def auto_send_satisfaction_surveys_with_context():
            with app.app_context():
                return SatisfactionService.auto_send_satisfaction_surveys()

        def auto_update_certifications_with_context():
            with app.app_context():
                return CertificationService.auto_update_certifications()

        def generate_performance_report_with_context():
            with app.app_context():
                return PerformanceService.generate_performance_report()

        # Agendar verificação de notificações a cada hora
        scheduler.add_job(
            id='check_notifications',
            func=run_notification_checks_with_context,
            trigger='interval',
            hours=1,
            max_instances=1,
            replace_existing=True
        )

        # Agendar processamento de lembretes recorrentes a cada hora
        scheduler.add_job(
            id='process_recurring_reminders',
            func=process_recurring_reminders_with_context,
            trigger='interval',
            hours=1,
            max_instances=1,
            replace_existing=True
        )

        # Agendar tarefa de envio automático de pesquisas de satisfação
        scheduler.add_job(
            id='auto_send_satisfaction_surveys',
            func=auto_send_satisfaction_surveys_with_context,
            trigger='interval',
            hours=6,  # A cada 6 horas
            max_instances=1,
            replace_existing=True
        )

        # Agendar tarefa de atualização automática de certificações
        scheduler.add_job(
            id='auto_update_certifications',
            func=auto_update_certifications_with_context,
            trigger='interval',
            hours=1,  # A cada hora
            max_instances=1,
            replace_existing=True
        )

        # Agendar tarefa de monitoramento de performance
        scheduler.add_job(
            id='performance_monitoring',
            func=generate_performance_report_with_context,
            trigger='interval',
            hours=4,  # A cada 4 horas
            max_instances=1,
            replace_existing=True
        )

        # Agendar verificação de SLA de equipamentos
        def check_equipment_sla_with_context():
            with app.app_context():
                from .services.equipment_service import EquipmentService
                return EquipmentService.check_sla_status()

        scheduler.add_job(
            id='equipment_sla_check',
            func=check_equipment_sla_with_context,
            trigger='interval',
            hours=1,  # A cada hora
            max_instances=1,
            replace_existing=True
        )

        # Agendar lembretes de devolução de equipamentos
        def send_equipment_reminders_with_context():
            with app.app_context():
                from .services.equipment_service import EquipmentService
                return EquipmentService.send_return_reminders()

        scheduler.add_job(
            id='equipment_return_reminders',
            func=send_equipment_reminders_with_context,
            trigger='interval',
            hours=6,  # A cada 6 horas
            max_instances=1,
            replace_existing=True
        )

        # Agendar verificação de alertas de manutenção
        def check_equipment_maintenance_with_context():
            with app.app_context():
                from .services.equipment_service import EquipmentService
                return EquipmentService.check_maintenance_alerts()

        scheduler.add_job(
            id='equipment_maintenance_alerts',
            func=check_equipment_maintenance_with_context,
            trigger='interval',
            hours=24,  # Uma vez por dia
            max_instances=1,
            replace_existing=True
        )

        # Tarefas agendadas configuradas

    from . import routes
    app.register_blueprint(routes.bp)

    # Registrar blueprint de autenticação
    from .auth import bp_auth
    app.register_blueprint(bp_auth, url_prefix="/auth")

    # Registrar filtros de template para timezone
    from .template_filters import register_template_filters
    register_template_filters(app)

    # Registrar blueprint de configurações do sistema
    try:
        # Simplesmente importar o módulo diretamente
        from .blueprints.system_config import system_config
        app.register_blueprint(system_config)
        # Blueprint de configurações do sistema registrado
    except Exception as e:
        app.logger.warning(f"Blueprint de configurações não pôde ser registrado")
        # Não mostrar traceback completo para não poluir logs

    # Configurar Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # Registrar blueprint de equipamentos (ANTIGO - será desativado)
    # try:
    #     from .blueprints.equipment import bp as equipment_bp
    #     app.register_blueprint(equipment_bp)
    #     app.logger.info("Blueprint de equipamentos registrado com sucesso")
    # except Exception as e:
    #     app.logger.error(f"Blueprint de equipamentos não pôde ser registrado: {e}")
    #     import traceback
    #     app.logger.error(traceback.format_exc())

    # Registrar blueprint de equipamentos V2 (NOVO - LIMPO)
    try:
        from .blueprints.equipment_clean import bp as equipment_v2_bp
        app.register_blueprint(equipment_v2_bp)
        app.logger.info("Blueprint de equipamentos V2 (limpo) registrado com sucesso")
    except Exception as e:
        app.logger.error("Blueprint de equipamentos V2 não pôde ser registrado")

    return app
