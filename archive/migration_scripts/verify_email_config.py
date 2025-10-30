"""Script para verificar configurações de e-mail"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("=" * 60)
print("VERIFICAÇÃO DE CONFIGURAÇÕES DE E-MAIL")
print("=" * 60)

# Verificar variáveis de ambiente
config_vars = {
    'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
    'MAIL_PORT': os.environ.get('MAIL_PORT'),
    'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS'),
    'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
    'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
    'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER'),
}

print("\n📋 Variáveis de Ambiente:")
for key, value in config_vars.items():
    if key == 'MAIL_PASSWORD':
        # Mascarar senha
        if value:
            masked = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '****'
            print(f"  ✓ {key}: {masked} (configurado)")
        else:
            print(f"  ✗ {key}: NÃO CONFIGURADO")
    else:
        if value:
            print(f"  ✓ {key}: {value}")
        else:
            print(f"  ✗ {key}: NÃO CONFIGURADO")

# Verificar problemas
print("\n🔍 Diagnóstico:")
issues = []

if not config_vars['MAIL_USERNAME']:
    issues.append("⚠️  MAIL_USERNAME não está configurado")

if not config_vars['MAIL_PASSWORD']:
    issues.append("⚠️  MAIL_PASSWORD não está configurado (use App Password do Gmail)")

if config_vars['MAIL_SERVER'] != 'smtp.gmail.com':
    issues.append("⚠️  MAIL_SERVER deveria ser 'smtp.gmail.com' para Gmail")

if config_vars['MAIL_PORT'] != '587':
    issues.append("⚠️  MAIL_PORT deveria ser '587' para TLS")

if config_vars['MAIL_USE_TLS'] != 'True':
    issues.append("⚠️  MAIL_USE_TLS deveria ser 'True'")

if issues:
    print("\n❌ PROBLEMAS ENCONTRADOS:")
    for issue in issues:
        print(f"  {issue}")
    print("\n📖 SOLUÇÃO:")
    print("  1. Crie uma App Password no Gmail:")
    print("     https://myaccount.google.com/apppasswords")
    print("  2. Configure no arquivo .env na raiz do projeto:")
    print("     MAIL_USERNAME=pageupsistemas@gmail.com")
    print("     MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # App Password")
else:
    print("\n✅ Todas as configurações estão corretas!")
    print("\n🔧 Testando conexão SMTP...")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        server = smtplib.SMTP(config_vars['MAIL_SERVER'], int(config_vars['MAIL_PORT']))
        server.starttls()
        server.login(config_vars['MAIL_USERNAME'], config_vars['MAIL_PASSWORD'])
        print("  ✅ Conexão SMTP bem-sucedida!")
        server.quit()
    except Exception as e:
        print(f"  ❌ Erro ao conectar: {e}")
        print("\n  💡 Verifique se a senha é uma App Password do Gmail")

print("\n" + "=" * 60)
