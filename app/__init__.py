from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from .email_utils import mail_init_app

mail = Mail()
db = SQLAlchemy()
scheduler = APScheduler()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    mail_init_app(app, mail)
    scheduler.init_app(app)
    scheduler.start()
    migrate.init_app(app, db)

    from . import routes
    app.register_blueprint(routes.bp)

    # Registrar blueprint de autenticação
    from .auth import bp_auth
    app.register_blueprint(bp_auth, url_prefix='/auth')

    return app
