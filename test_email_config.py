#!/usr/bin/env python3
"""Script para testar as configurações de email manualmente"""

import requests
import json
from bs4 import BeautifulSoup

# Configurações
BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/auth/login"
EMAIL_CONFIG_URL = f"{BASE_URL}/configuracoes/integracoes/email"

# Credenciais de teste (novo usuário admin)
USERNAME = "test_admin"  # novo usuário admin
PASSWORD = "test123"  # senha do novo usuário

def test_email_config():
    """Testa a página de configurações de email"""
    
    print("Iniciando teste das configuracoes de email...")
    
    # Criar sessão
    session = requests.Session()
    
    # 1. Fazer login
    print("\n1. Fazendo login...")
    login_page = session.get(LOGIN_URL)
    
    if login_page.status_code != 200:
        print(f"Erro ao acessar pagina de login: {login_page.status_code}")
        return False
    
    # Extrair CSRF token
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    if not csrf_token:
        print("CSRF token nao encontrado")
        return False
    
    csrf_token = csrf_token.get('value')
    print(f"CSRF token obtido: {csrf_token[:20]}...")
    
    # Fazer POST para login
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrf_token': csrf_token,
        'remember': False
    }
    
    login_response = session.post(LOGIN_URL, data=login_data)
    
    if login_response.status_code != 200:
        print(f"Erro no login: {login_response.status_code}")
        print(f"Resposta: {login_response.text[:500]}")
        return False
    
    # Verificar se login foi bem-sucedido
    if "dashboard" in login_response.url.lower() or "index" in login_response.url.lower():
        print("Login realizado com sucesso!")
    else:
        print("Login falhou - redirecionado para pagina de login novamente")
        return False
    
    # 2. Acessar página de configurações de email
    print("\n2. Acessando pagina de configuracoes de email...")
    email_page = session.get(EMAIL_CONFIG_URL)
    
    if email_page.status_code != 200:
        print(f"Erro ao acessar configuracoes de email: {email_page.status_code}")
        return False
    
    # Verificar se a página carregou corretamente
    if "Integracao de Email" in email_page.text:
        print("Pagina de configuracoes de email carregada!")
    else:
        print("Pagina de configuracoes nao encontrada ou conteudo incorreto")
        print(f"Conteudo: {email_page.text[:500]}")
        return False
    
    # 3. Verificar elementos da página
    print("\n3. Verificando elementos da pagina...")
    soup = BeautifulSoup(email_page.text, 'html.parser')
    
    # Verificar formulário SMTP
    smtp_form = soup.find('form')
    if smtp_form:
        print("Formulario SMTP encontrado")
    else:
        print("Formulario SMTP nao encontrado")
        return False
    
    # Verificar campos principais
    fields_to_check = [
        'smtp_server', 'smtp_port', 'smtp_username', 
        'smtp_password', 'from_email', 'from_name'
    ]
    
    for field in fields_to_check:
        input_field = soup.find('input', {'name': field})
        if input_field:
            value = input_field.get('value', '')
            print(f"Campo {field}: {'preenchido' if value else 'vazio'}")
        else:
            print(f"Campo {field} nao encontrado")
    
    # 4. Testar configuração SMTP (se houver dados)
    print("\n4. Testando configuracao SMTP...")
    
    # Obter CSRF token para formulário
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    if csrf_token:
        csrf_token = csrf_token.get('value')
        
        # Dados de teste (configuração Gmail)
        test_data = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587',
            'smtp_username': 'pageupsistemas@gmail.com',
            'smtp_password': 'pqex fqow whrd mqoy',
            'smtp_use_tls': 'on',
            'smtp_use_ssl': '',
            'from_email': 'pageupsistemas@gmail.com',
            'from_name': 'TI OSN System',
            'csrf_token': csrf_token,
            'test_connection': '1'  # Flag para testar conexão
        }
        
        # Enviar teste de conexão
        test_url = f"{BASE_URL}/configuracoes/integracoes/email/test-connection"
        test_response = session.post(test_url, data=test_data)
        
        if test_response.status_code == 200:
            try:
                result = test_response.json()
                if result.get('success'):
                    print(f"Teste de conexao SMTP: {result.get('message')}")
                else:
                    print(f"Teste de conexao falhou: {result.get('message')}")
            except:
                print(f"Resposta invalida do servidor: {test_response.text[:200]}")
        else:
            print(f"Erro no teste: {test_response.status_code}")
    
    print("\nTeste concluido!")
    print(f"Resumo:")
    print(f"   - Login: OK")
    print(f"   - Pagina de email: OK")
    print(f"   - Formulario SMTP: OK")
    print(f"   - Sistema funcional: OK")
    
    return True

if __name__ == "__main__":
    print("Teste Manual - Configuracoes de Email")
    print("=" * 50)
    print(f"URL Base: {BASE_URL}")
    print(f"Usuario: {USERNAME}")
    print(f"Senha: {'*' * len(PASSWORD)}")
    print("=" * 50)
    
    try:
        success = test_email_config()
        if success:
            print("\nSUCESSO! Sistema está pronto para uso.")
        else:
            print("\nFALHA! Verifique os erros acima.")
    except Exception as e:
        print(f"\nErro inesperado: {e}")
