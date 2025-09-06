from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from .email_utils import mail_init_app

mail = Mail()
db = SQLAlchemy()
scheduler = APScheduler()
migrate = Migrate()
bootstrap = Bootstrap()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
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
    app.register_blueprint(bp_auth, url_prefix='/auth')

    # Registrar filtros de template para timezone
    from .template_filters import register_template_filters
    register_template_filters(app)

    return app
