"""
Script de teste para debug do formulário de edição de usuário
"""

import sys
sys.path.insert(0, r'c:\Users\Oezios Normando\Documents\tireminderapp')

from app import create_app, db
from app.models import User
from app.forms import UserEditForm

app = create_app()

with app.app_context():
    # Buscar usuário ID 1
    user = User.query.get(1)
    
    if user:
        print(f"✓ Usuário encontrado: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Setor ID: {user.sector_id}")
        print(f"  Is Admin: {user.is_admin}")
        print(f"  Is TI: {user.is_ti}")
        print(f"  Ativo: {user.ativo}")
        print()
        
        # Criar formulário
        form = UserEditForm(obj=user)
        
        # Verificar campos do formulário
        print("Campos do formulário:")
        print(f"  username: {form.username.data}")
        print(f"  email: {form.email.data}")
        print(f"  sector_id: {form.sector_id.data}")
        print(f"  is_admin: {form.is_admin.data}")
        print(f"  is_ti: {form.is_ti.data}")
        print(f"  change_password: {form.change_password.data}")
        print()
        
        # Simular uma submissão
        print("=== Teste de validação ===")
        
        # Dados simulados de um POST
        from werkzeug.datastructures import MultiDict
        test_data = MultiDict([
            ('username', 'admin_test_modificado'),
            ('email', 'admin@test.com'),
            ('sector_id', '1'),
            ('is_admin', 'y'),
            ('is_ti', 'y'),
            ('csrf_token', 'test')
        ])
        
        form = UserEditForm(test_data)
        form.sector_id.choices = [(0, "Selecione")] + [(1, "TI"), (2, "RH")]
        
        # Desabilitar validação CSRF para teste
        form.csrf_token.data = 'test'
        form.meta.csrf = False
        
        if form.validate():
            print("✓ Formulário válido!")
            print(f"  Username: {form.username.data}")
            print(f"  Email: {form.email.data}")
        else:
            print("✗ Formulário inválido!")
            print(f"  Erros: {form.errors}")
            
    else:
        print("✗ Usuário ID 1 não encontrado")
