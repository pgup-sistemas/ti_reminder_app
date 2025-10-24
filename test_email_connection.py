"""Script para testar conexão SMTP e envio de e-mail"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("=" * 60)
print("TESTE DE CONEXÃO E ENVIO DE E-MAIL")
print("=" * 60)

# Obter configurações
mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
mail_port = int(os.environ.get('MAIL_PORT', 587))
mail_username = os.environ.get('MAIL_USERNAME')
mail_password = os.environ.get('MAIL_PASSWORD')
mail_sender = os.environ.get('MAIL_DEFAULT_SENDER')

print(f"\n📧 Configurações:")
print(f"  Server: {mail_server}")
print(f"  Port: {mail_port}")
print(f"  Username: {mail_username}")
print(f"  Sender: {mail_sender}")
print(f"  Password: {'*' * 12} (configurado)")

if not mail_username or not mail_password:
    print("\n❌ ERRO: MAIL_USERNAME ou MAIL_PASSWORD não configurados!")
    exit(1)

print("\n🔧 Testando conexão SMTP...")

try:
    # Conectar ao servidor
    server = smtplib.SMTP(mail_server, mail_port, timeout=10)
    server.set_debuglevel(0)  # 0 = sem debug, 1 = com debug
    
    print("  ✓ Conexão estabelecida")
    
    # Iniciar TLS
    server.starttls()
    print("  ✓ TLS iniciado")
    
    # Fazer login
    server.login(mail_username, mail_password)
    print("  ✓ Autenticação bem-sucedida")
    
    # Criar mensagem de teste
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '[TESTE] Configuração de E-mail - TI Reminder'
    msg['From'] = mail_sender
    msg['To'] = mail_username  # Enviar para si mesmo
    
    text = """
    Este é um e-mail de teste do sistema TI Reminder.
    
    Se você recebeu este e-mail, a configuração está funcionando corretamente!
    
    Configurações testadas:
    - Servidor SMTP: {}
    - Porta: {}
    - Autenticação: OK
    - TLS: OK
    
    Sistema TI Reminder
    """.format(mail_server, mail_port)
    
    html = """
    <html>
    <body>
        <h2>✅ Teste de Configuração de E-mail</h2>
        <p>Este é um e-mail de teste do sistema <strong>TI Reminder</strong>.</p>
        <p>Se você recebeu este e-mail, a configuração está funcionando corretamente!</p>
        
        <h3>Configurações testadas:</h3>
        <ul>
            <li>Servidor SMTP: {}</li>
            <li>Porta: {}</li>
            <li>Autenticação: <span style="color: green;">✓ OK</span></li>
            <li>TLS: <span style="color: green;">✓ OK</span></li>
        </ul>
        
        <hr>
        <p style="color: gray; font-size: 12px;">Sistema TI Reminder - E-mail de Teste</p>
    </body>
    </html>
    """.format(mail_server, mail_port)
    
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    # Enviar e-mail de teste
    print("\n📤 Enviando e-mail de teste...")
    server.send_message(msg)
    print(f"  ✓ E-mail enviado com sucesso para {mail_username}")
    
    # Fechar conexão
    server.quit()
    print("  ✓ Conexão encerrada")
    
    print("\n" + "=" * 60)
    print("✅ SUCESSO! Configuração de e-mail está correta!")
    print("=" * 60)
    print(f"\nVerifique sua caixa de entrada: {mail_username}")
    print("Você deve receber um e-mail de teste em alguns segundos.")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ ERRO DE AUTENTICAÇÃO: {e}")
    print("\n💡 Possíveis soluções:")
    print("  1. Verifique se a senha é uma App Password do Gmail")
    print("  2. Acesse: https://myaccount.google.com/apppasswords")
    print("  3. Gere uma nova App Password")
    print("  4. Substitua no arquivo .env")
    
except smtplib.SMTPException as e:
    print(f"\n❌ ERRO SMTP: {e}")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
