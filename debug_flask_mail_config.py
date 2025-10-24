"""Debug das configurações do Flask-Mail"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("DEBUG: Configurações Flask-Mail")
print("=" * 60)

# Ver valores RAW do .env
print("\n📋 Valores RAW do .env:")
print(f"  MAIL_SERVER: {repr(os.environ.get('MAIL_SERVER'))}")
print(f"  MAIL_PORT: {repr(os.environ.get('MAIL_PORT'))}")
print(f"  MAIL_USE_TLS: {repr(os.environ.get('MAIL_USE_TLS'))}")
print(f"  MAIL_USERNAME: {repr(os.environ.get('MAIL_USERNAME'))}")
print(f"  MAIL_PASSWORD: {repr(os.environ.get('MAIL_PASSWORD')[:4] + '***')}")

# Ver conversões no config.py
print("\n🔧 Conversões:")
mail_use_tls_raw = os.environ.get('MAIL_USE_TLS', 'True')
mail_use_tls_converted = mail_use_tls_raw.lower() == 'true'
print(f"  MAIL_USE_TLS raw: {repr(mail_use_tls_raw)}")
print(f"  MAIL_USE_TLS.lower(): {repr(mail_use_tls_raw.lower())}")
print(f"  MAIL_USE_TLS convertido: {repr(mail_use_tls_converted)}")

# Testar Flask-Mail
print("\n🧪 Testando Flask-Mail:")
from flask import Flask
from flask_mail import Mail

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

print(f"  Flask app.config['MAIL_USE_TLS']: {repr(app.config['MAIL_USE_TLS'])}")
print(f"  Tipo: {type(app.config['MAIL_USE_TLS'])}")

mail = Mail(app)

print("\n📧 Testando envio com Flask-Mail:")
try:
    from flask_mail import Message
    
    with app.app_context():
        msg = Message(
            subject="[TESTE] Flask-Mail - TI Reminder",
            recipients=[app.config['MAIL_USERNAME']],
            body="Teste de envio usando Flask-Mail"
        )
        
        # Tentar enviar
        mail.send(msg)
        print("  ✅ E-mail enviado com sucesso!")
        
except Exception as e:
    print(f"  ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
