import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from flask import Flask
from app.models import db, User
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Altere conforme desejado
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@admin.com'
ADMIN_PASSWORD = 'admin123'

# Criar aplicação Flask com configuração explícita para PostgreSQL
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Verificar se o usuário admin já existe
    if not User.query.filter_by(username=ADMIN_USERNAME).first():
        user = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            is_admin=True,
            ativo=True
        )
        user.set_password(ADMIN_PASSWORD)
        db.session.add(user)
        db.session.commit()
        print('Usuário admin criado com sucesso!')
    else:
        print('Usuário admin já existe.')