import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app
from app.models import db, User

# Altere conforme desejado
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@admin.com'
ADMIN_PASSWORD = 'admin123'

app = create_app()

with app.app_context():
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
