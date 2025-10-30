"""
Teste com autenticação para identificar onde está o problema
"""
import requests

BASE_URL = "http://192.168.1.86:5000"

print("="*70)
print("TESTE COM AUTENTICAÇÃO")
print("="*70)

session = requests.Session()

# 1. Login
print("\n[1] Fazendo login...")
login_response = session.post(f"{BASE_URL}/auth/login", data={
    'username': 'admin_test',
    'password': 'Admin@123',
}, allow_redirects=True)

print(f"  Status: {login_response.status_code}")

if login_response.status_code == 200:
    print("✓ Login OK")
    # Ver cookies
    print(f"  Cookies: {session.cookies.get_dict()}")
else:
    print(f"✗ Login falhou")
    exit(1)

# 2. Acessar página de edição COM AUTH
print("\n[2] Acessando edição COM autenticação...")
edit_url = f"{BASE_URL}/configuracoes/usuarios/1/editar"
get_response = session.get(edit_url)

print(f"  Status: {get_response.status_code}")

if get_response.status_code == 302:
    print(f"✗ Redirecionado para: {get_response.headers.get('Location')}")
    print("  → Perdeu a sessão!")
    exit(1)
elif get_response.status_code != 200:
    print(f"✗ Erro: {get_response.status_code}")
    exit(1)

print("✓ Página acessada")

# Extrair CSRF
import re
csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', get_response.text)

if not csrf_match:
    print("✗ CSRF token não encontrado")
    exit(1)

csrf_token = csrf_match.group(1)
print(f"✓ CSRF: {csrf_token[:20]}...")

# 3. POST
print("\n[3] Submetendo formulário COM AUTH...")

form_data = {
    'csrf_token': csrf_token,
    'username': 'admin_test_COM_AUTH',
    'email': 'admin@test.com',
    'sector_id': '1',
    'is_admin': 'y',
    'is_ti': 'y',
    'ativo': 'on',
    'change_password': 'on',
    'new_password': 'TestAuth@123',
    'confirm_password': 'TestAuth@123',
}

post_response = session.post(edit_url, data=form_data, allow_redirects=False)

print(f"  Status: {post_response.status_code}")

if post_response.status_code == 302:
    location = post_response.headers.get('Location', '')
    print(f"✓ Redirecionado para: {location}")
    
    if '/auth/login' in location:
        print("\n✗✗✗ PERDEU A SESSÃO NO POST!")
        print("  Problema: @login_required está rejeitando")
    elif '/configuracoes/usuarios' in location and '/editar' not in location:
        print("\n✅✅✅ SUCESSO!")
    else:
        print(f"\n⚠ Redirecionado mas não esperado: {location}")
else:
    print(f"\n✗ Status inesperado: {post_response.status_code}")

print("\n" + "="*70)
