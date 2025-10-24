"""
Teste do fluxo completo de reset de senha auto-solicitado
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("TESTE: FLUXO DE RESET DE SENHA AUTO-SOLICITADO")
print("=" * 70)

# Simular o processo
print("\n📋 Cenário:")
print("  1. Usuário acessa: http://192.168.1.86:5000/auth/reset_password_request")
print("  2. Digita o e-mail cadastrado")
print("  3. Sistema gera token e envia link por e-mail")
print("  4. Usuário clica no link e define nova senha")

print("\n🔧 Configurações SMTP:")
print(f"  MAIL_SERVER: {os.environ.get('MAIL_SERVER')}")
print(f"  MAIL_PORT: {os.environ.get('MAIL_PORT')}")
print(f"  MAIL_USERNAME: {os.environ.get('MAIL_USERNAME')}")
print(f"  MAIL_USE_TLS: {os.environ.get('MAIL_USE_TLS')}")

print("\n" + "=" * 70)
print("TESTANDO GERAÇÃO DE TOKEN E ENVIO DE E-MAIL")
print("=" * 70)

# Importar contexto da aplicação
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Buscar um usuário para testar
    user = User.query.first()
    
    if not user:
        print("\n❌ Nenhum usuário encontrado no banco de dados!")
        print("   Crie um usuário primeiro.")
        exit(1)
    
    print(f"\n👤 Usuário de teste: {user.username}")
    print(f"📧 E-mail: {user.email}")
    
    # Gerar token
    token = user.generate_reset_token()
    print(f"\n🔑 Token gerado: {token[:20]}... (truncado)")
    print(f"⏰ Validade: 1 hora")
    
    # Salvar no banco
    db.session.commit()
    
    # Simular envio de e-mail
    from app.email_utils import send_password_reset_email
    
    print("\n📤 Enviando e-mail de reset de senha...")
    
    try:
        # O link será algo como: http://192.168.1.86:5000/auth/reset_password/<token>
        send_password_reset_email(user, token)
        
        print("\n✅ E-MAIL ENVIADO COM SUCESSO!")
        print(f"\n📬 Verifique a caixa de entrada de: {user.email}")
        print("\n📝 O e-mail contém:")
        print("  - Link para redefinir senha")
        print("  - Link expira em 1 hora")
        print(f"  - Link: http://192.168.1.86:5000/auth/reset_password/{token}")
        
        print("\n🎯 PRÓXIMOS PASSOS:")
        print("  1. Abra o e-mail recebido")
        print("  2. Clique no link de redefinição")
        print("  3. Defina sua nova senha")
        print("  4. Faça login com a nova senha")
        
    except Exception as e:
        print(f"\n❌ ERRO ao enviar e-mail: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
