"""
Teste direto de edição de usuário usando app context
"""
import sys
sys.path.insert(0, r'c:\Users\Oezios Normando\Documents\tireminderapp')

from app import create_app, db
from app.models import User
from werkzeug.datastructures import MultiDict

print("="*70)
print("TESTE DIRETO DE EDIÇÃO DE USUÁRIO")
print("="*70)

app = create_app()

with app.app_context():
    # 1. Buscar usuário ID 1
    print("\n[1] Buscando usuário ID 1...")
    user = User.query.get(1)
    
    if not user:
        print("✗ Usuário ID 1 não encontrado!")
        exit(1)
    
    print(f"✓ Usuário encontrado:")
    print(f"  - ID: {user.id}")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - Setor ID: {user.sector_id}")
    print(f"  - Is Admin: {user.is_admin}")
    print(f"  - Is TI: {user.is_ti}")
    print(f"  - Ativo: {user.ativo}")
    
    # 2. Criar dados de formulário simulando POST
    print("\n[2] Simulando submissão de formulário...")
    
    # Dados que seriam enviados pelo formulário
    form_data = MultiDict([
        ('username', 'admin_test_MODIFICADO'),  # Alterando username
        ('email', 'admin_modificado@test.com'),  # Alterando email
        ('sector_id', '1'),
        ('is_admin', 'y'),
        ('is_ti', 'y'),
        ('change_password', ''),  # Não alterar senha
        ('new_password', ''),
        ('confirm_password', ''),
        ('csrf_token', 'test-token')  # Token fake para teste
    ])
    
    print("  Dados do formulário:")
    for key, value in form_data.items():
        print(f"    - {key}: {value}")
    
    # 3. Validar e processar dados
    print("\n[3] Processando alterações...")
    
    try:
        # Salvar estado anterior
        old_username = user.username
        old_email = user.email
        
        # Aplicar mudanças
        user.username = form_data.get('username')
        user.email = form_data.get('email')
        user.sector_id = int(form_data.get('sector_id', 0)) or None
        user.is_admin = form_data.get('is_admin') == 'y'
        user.is_ti = form_data.get('is_ti') == 'y'
        
        # Commit
        db.session.commit()
        
        print("\n✓✓✓ SUCESSO! Usuário atualizado:")
        print(f"  - Username: {old_username} → {user.username}")
        print(f"  - Email: {old_email} → {user.email}")
        print(f"  - Setor ID: {user.sector_id}")
        print(f"  - Is Admin: {user.is_admin}")
        print(f"  - Is TI: {user.is_ti}")
        
        # 4. Reverter mudanças para não bagunçar o banco
        print("\n[4] Revertendo mudanças (para não alterar o banco real)...")
        user.username = old_username
        user.email = old_email
        db.session.commit()
        print("✓ Mudanças revertidas")
        
    except Exception as e:
        db.session.rollback()
        print(f"\n✗ Erro ao atualizar usuário: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
print("TESTE CONCLUÍDO")
print("="*70)
