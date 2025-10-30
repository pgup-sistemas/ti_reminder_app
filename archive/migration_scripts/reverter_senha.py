"""
Reverter senha para Admin@123
"""
import sys
sys.path.insert(0, r'c:\Users\Oezios Normando\Documents\tireminderapp')

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.get(1)
    if user:
        # Reverter nome e senha
        user.username = 'admin_test'
        user.set_password('Admin@123')
        db.session.commit()
        print(f"✓ Usuário revertido:")
        print(f"  Username: {user.username}")
        print(f"  Senha: Admin@123")
    else:
        print("✗ Usuário não encontrado")
