"""
Teste final simplificado - edição direta no banco
"""
import sys
sys.path.insert(0, r'c:\Users\Oezios Normando\Documents\tireminderapp')

from app import create_app, db
from app.models import User

print("="*70)
print("TESTE SIMPLIFICADO - EDIÇÃO DIRETA")
print("="*70)

app = create_app()

with app.app_context():
    # Buscar usuário
    print("\n[1] Buscando usuário ID 1...")
    user = User.query.get(1)
    
    if not user:
        print("✗ Usuário não encontrado!")
        exit(1)
    
    print(f"✓ Usuário encontrado: {user.username} ({user.email})")
    
    # Editar
    print("\n[2] Editando usuário...")
    old_username = user.username
    old_email = user.email
    
    user.username = "admin_test_EDITADO"
    user.email = "admin_editado@test.com"
    
    try:
        db.session.commit()
        print("✓ Usuário editado com sucesso!")
        print(f"  Username: {old_username} → {user.username}")
        print(f"  Email: {old_email} → {user.email}")
        
        # Reverter
        print("\n[3] Revertendo...")
        user.username = old_username
        user.email = old_email
        db.session.commit()
        print("✓ Revertido com sucesso")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Erro: {e}")

print("\n" + "="*70)
print("SE ESTE TESTE PASSOU, O PROBLEMA É NO FORMULÁRIO WEB")
print("="*70)
