#!/usr/bin/env python3
"""Script simples para testar login"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/auth/login"

def test_login():
    session = requests.Session()
    
    # 1. Obter página de login
    print("1. Obtendo pagina de login...")
    login_page = session.get(LOGIN_URL)
    
    if login_page.status_code != 200:
        print(f"Erro: {login_page.status_code}")
        return False
    
    print(f"Status: {login_page.status_code}")
    print(f"URL atual: {login_page.url}")
    
    # 2. Extrair formulário
    soup = BeautifulSoup(login_page.text, 'html.parser')
    
    # Verificar se há formulário de login
    form = soup.find('form')
    if not form:
        print("Nenhum formulario encontrado")
        return False
    
    print("Formulario encontrado!")
    
    # 3. Extrair campos
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    username_field = soup.find('input', {'name': 'username'})
    password_field = soup.find('input', {'name': 'password'})
    
    print(f"CSRF token: {'encontrado' if csrf_token else 'NAO encontrado'}")
    print(f"Campo username: {'encontrado' if username_field else 'NAO encontrado'}")
    print(f"Campo password: {'encontrado' if password_field else 'NAO encontrado'}")
    
    if csrf_token:
        print(f"Valor CSRF: {csrf_token.get('value', '')[:30]}...")
    
    # 4. Tentar login
    if csrf_token and username_field and password_field:
        login_data = {
            'username': 'test_admin',
            'password': 'test123',
            'csrf_token': csrf_token.get('value'),
            'remember': False
        }
        
        print("\n2. Tentando login...")
        response = session.post(LOGIN_URL, data=login_data)
        
        print(f"Status: {response.status_code}")
        print(f"URL final: {response.url}")
        print(f"Redirecionado: {'sim' if response.url != LOGIN_URL else 'nao'}")
        
        # Verificar se há mensagens de erro
        soup = BeautifulSoup(response.text, 'html.parser')
        alerts = soup.find_all(class_='alert')
        if alerts:
            print("Alertas encontrados:")
            for alert in alerts:
                print(f"  - {alert.get_text().strip()}")
        
        # Verificar se está logado (procurando links de admin)
        admin_links = soup.find_all('a', href=lambda x: x and 'configuracoes' in x)
        if admin_links:
            print("Links de admin encontrados - login bem-sucedido!")
            return True
        else:
            print("Nenhum link de admin encontrado - login falhou")
            return False
    
    return False

if __name__ == "__main__":
    print("Teste Simples de Login")
    print("=" * 30)
    test_login()
