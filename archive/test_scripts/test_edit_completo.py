"""
Teste completo e definitivo de edição de usuário
"""
import sys
sys.path.insert(0, r'c:\Users\Oezios Normando\Documents\tireminderapp')

from app import create_app, db
from app.models import User
from flask import session
from werkzeug.datastructures import ImmutableMultiDict

print("="*70)
print("TESTE DEFINITIVO - EDIÇÃO DE USUÁRIO")
print("="*70)

app = create_app()

with app.app_context():
    with app.test_request_context():
        # 1. Buscar usuário
        print("\n[1] Buscando usuário ID 1...")
        user = User.query.get(1)
        
        if not user:
            print("✗ Usuário não encontrado!")
            exit(1)
        
        print(f"✓ Usuário encontrado:")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Setor: {user.sector_id}")
        print(f"  Admin: {user.is_admin}")
        print(f"  TI: {user.is_ti}")
        print(f"  Ativo: {user.ativo}")
        
        # 2. Criar test client
        print("\n[2] Criando cliente de teste...")
        client = app.test_client()
        
        # 3. Fazer login usando flask_login
        print("\n[3] Fazendo login...")
        from flask_login import login_user
        
        # Simular login no contexto
        with app.test_request_context('/'):
            login_user(user)
            print("✓ Usuário logado no contexto")
        
        # 4. Acessar página de edição (GET)
        print("\n[4] Acessando página de edição...")
        response = client.get(f'/configuracoes/usuarios/{user.id}/editar')
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ Erro ao acessar página: {response.status_code}")
            exit(1)
        
        # Extrair CSRF token do HTML
        html = response.data.decode('utf-8')
        import re
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        
        if not csrf_match:
            print("✗ CSRF token não encontrado no HTML!")
            exit(1)
        
        csrf_token = csrf_match.group(1)
        print(f"✓ CSRF token obtido: {csrf_token[:20]}...")
        
        # 5. Submeter formulário de edição (POST)
        print("\n[5] Submetendo formulário de edição...")
        
        form_data = {
            'csrf_token': csrf_token,
            'username': 'admin_test_EDITADO_DEFINITIVO',
            'email': 'admin_editado@test.com',
            'sector_id': '1',
            'is_admin': 'y',
            'is_ti': 'y',
            # Não enviar change_password - deixa vazio
        }
        
        print("  Dados sendo enviados:")
        for key, value in form_data.items():
            if key != 'csrf_token':
                print(f"    {key}: {value}")
        
        response = client.post(
            f'/configuracoes/usuarios/{user.id}/editar',
            data=form_data,
            follow_redirects=False
        )
        
        print(f"\n  Status da resposta: {response.status_code}")
        print(f"  Location: {response.location if response.status_code in [301, 302] else 'N/A'}")
        
        # 6. Verificar resultado
        print("\n[6] Verificando resultado...")
        
        # Recarregar usuário do banco
        db.session.expire(user)
        user = User.query.get(1)
        
        if response.status_code in [301, 302]:
            if '/configuracoes/usuarios' in response.location and '/editar' not in response.location:
                print("\n✓✓✓ SUCESSO! Redirecionado para lista de usuários")
                print(f"\nUsuário atualizado:")
                print(f"  Username: {user.username}")
                print(f"  Email: {user.email}")
                
                # Reverter mudanças
                print("\n[7] Revertendo mudanças...")
                user.username = 'admin_test'
                user.email = 'admin@test.com'
                db.session.commit()
                print("✓ Mudanças revertidas")
            else:
                print(f"\n⚠ Redirecionado mas não para o lugar esperado: {response.location}")
        else:
            print(f"\n✗ Não houve redirecionamento. Status: {response.status_code}")
            
            # Verificar se há erros no HTML
            html = response.data.decode('utf-8')
            if 'invalid-feedback' in html or 'alert-danger' in html:
                print("\n  Erros de validação encontrados no HTML:")
                # Tentar extrair erros
                error_matches = re.findall(r'<div class="invalid-feedback">([^<]+)</div>', html)
                for error in error_matches:
                    print(f"    - {error.strip()}")
                
                # Procurar alerts
                alert_matches = re.findall(r'alert alert-danger[^>]*>([^<]+)', html)
                for alert in alert_matches:
                    print(f"    - {alert.strip()}")

print("\n" + "="*70)
print("TESTE CONCLUÍDO")
print("="*70)
