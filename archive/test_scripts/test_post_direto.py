"""
Teste HTTP direto - simular POST do navegador
"""
import requests

BASE_URL = "http://192.168.1.86:5000"

print("="*70)
print("TESTE HTTP DIRETO")
print("="*70)

# Criar sessão
session = requests.Session()

# 1. Fazer login
print("\n[1] Fazendo login...")
login_data = {
    'username': 'admin_test',
    'password': 'Admin@123',
}

login_response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=True)

if login_response.status_code == 200:
    print(f"✓ Login OK (status: {login_response.status_code})")
else:
    print(f"✗ Login falhou (status: {login_response.status_code})")
    print("Tentando continuar mesmo assim...")

# 2. Acessar página de edição SEM AUTENTICAÇÃO (GET)
print("\n[2] Acessando página de edição SEM AUTENTICAÇÃO...")
edit_url = f"{BASE_URL}/configuracoes/usuarios/1/editar-sem-auth"
get_response = session.get(edit_url)

print(f"  Status: {get_response.status_code}")

if get_response.status_code == 200:
    print("✓ Página acessada")
    
    # Extrair CSRF token
    import re
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', get_response.text)
    
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"✓ CSRF token: {csrf_token[:20]}...")
    else:
        print("✗ CSRF token não encontrado")
        csrf_token = ""
else:
    print(f"✗ Erro ao acessar página: {get_response.status_code}")
    if get_response.status_code == 302:
        print(f"  Redirecionado para: {get_response.headers.get('Location')}")
    exit(1)

# 3. Submeter formulário (POST)
print("\n[3] Submetendo formulário...")

form_data = {
    'csrf_token': csrf_token,
    'username': 'admin_test_HTTP_DIRETO',
    'email': 'admin_http@test.com',
    'sector_id': '1',
    'is_admin': 'y',
    'is_ti': 'y',
    'ativo': 'on',
    'change_password': '',
    'new_password': '',
    'confirm_password': '',
}

print("  Dados:")
for k, v in form_data.items():
    if k != 'csrf_token':
        print(f"    {k}: {v}")

post_response = session.post(edit_url, data=form_data, allow_redirects=False)

print(f"\n  Status: {post_response.status_code}")

if post_response.status_code == 302:
    location = post_response.headers.get('Location', '')
    print(f"✓ Redirecionado para: {location}")
    
    if '/configuracoes/usuarios' in location and '/editar' not in location:
        print("\n✅✅✅ SUCESSO! Usuário editado!")
    else:
        print(f"\n⚠ Redirecionado mas não para lista: {location}")
        
elif post_response.status_code == 200:
    print("\n⚠ Retornou 200 (ficou na mesma página)")
    print("  Verificando erros...")
    
    if 'alert-danger' in post_response.text or 'invalid-feedback' in post_response.text:
        print("  ✗ Há erros na página")
        # Tentar extrair erros
        import re
        errors = re.findall(r'alert alert-danger[^>]*>([^<]+)', post_response.text)
        for err in errors:
            print(f"    - {err.strip()}")
    else:
        print("  Nenhum erro visível encontrado")
else:
    print(f"\n✗ Status inesperado: {post_response.status_code}")

print("\n" + "="*70)
print("TESTE CONCLUÍDO")
print("="*70)
