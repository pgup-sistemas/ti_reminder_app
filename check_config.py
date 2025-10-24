"""
Verificar configuração do app
"""
import sys
sys.path.insert(0, r'c:\Users\Oezios Normando\Documents\tireminderapp')

from app import create_app
import os

print("="*70)
print("VERIFICAÇÃO DE CONFIGURAÇÃO")
print("="*70)

# Verificar .env
print("\n[1] Arquivo .env:")
env_path = r'c:\Users\Oezios Normando\Documents\tireminderapp\.env'
if os.path.exists(env_path):
    print(f"✓ Arquivo existe: {env_path}")
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print("  Conteúdo:")
        for line in content.split('\n'):
            if line.strip():
                key = line.split('=')[0] if '=' in line else line
                print(f"    {key}=...")
else:
    print("✗ Arquivo .env NÃO EXISTE!")

# Verificar variáveis de ambiente
print("\n[2] Variáveis de ambiente:")
secret_key = os.environ.get('SECRET_KEY')
if secret_key:
    print(f"✓ SECRET_KEY: {secret_key[:20]}... (length: {len(secret_key)})")
else:
    print("✗ SECRET_KEY não está em os.environ!")

# Verificar app
print("\n[3] Configuração do App:")
app = create_app()

with app.app_context():
    print(f"  SECRET_KEY: {app.config['SECRET_KEY'][:20]}...")
    print(f"  SESSION_COOKIE_SECURE: {app.config['SESSION_COOKIE_SECURE']}")
    print(f"  SESSION_COOKIE_HTTPONLY: {app.config['SESSION_COOKIE_HTTPONLY']}")
    print(f"  SESSION_COOKIE_SAMESITE: {app.config['SESSION_COOKIE_SAMESITE']}")
    print(f"  WTF_CSRF_ENABLED: {app.config['WTF_CSRF_ENABLED']}")
    print(f"  WTF_CSRF_TIME_LIMIT: {app.config['WTF_CSRF_TIME_LIMIT']}")

print("\n" + "="*70)
