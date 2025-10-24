"""
Teste de edição COM MUDANÇA DE SENHA
"""
import requests

BASE_URL = "http://192.168.1.86:5000"

print("="*70)
print("TESTE DE EDIÇÃO COM MUDANÇA DE SENHA")
print("="*70)

session = requests.Session()

# Acessar página
print("\n[1] Acessando página de edição...")
edit_url = f"{BASE_URL}/configuracoes/usuarios/1/editar-sem-auth"
get_response = session.get(edit_url)

if get_response.status_code != 200:
    print(f"✗ Erro: {get_response.status_code}")
    exit(1)

print("✓ Página acessada")

# Extrair CSRF token
import re
csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', get_response.text)

if not csrf_match:
    print("✗ CSRF token não encontrado")
    exit(1)

csrf_token = csrf_match.group(1)
print(f"✓ CSRF token: {csrf_token[:20]}...")

# Submeter com senha
print("\n[2] Submetendo formulário COM MUDANÇA DE SENHA...")

form_data = {
    'csrf_token': csrf_token,
    'username': 'admin_test_COM_SENHA',
    'email': 'admin@test.com',
    'sector_id': '1',
    'is_admin': 'y',
    'is_ti': 'y',
    'ativo': 'on',
    'change_password': 'on',  # MARCADO!
    'new_password': 'NovaSenha@123',
    'confirm_password': 'NovaSenha@123',
}

print("  Dados:")
for k, v in form_data.items():
    if k in ['new_password', 'confirm_password']:
        print(f"    {k}: ***")
    elif k != 'csrf_token':
        print(f"    {k}: {v}")

post_response = session.post(edit_url, data=form_data, allow_redirects=False)

print(f"\n  Status: {post_response.status_code}")

if post_response.status_code == 302:
    location = post_response.headers.get('Location', '')
    print(f"✓ Redirecionado para: {location}")
    
    if '/configuracoes/usuarios' in location and '/editar' not in location:
        print("\n✅✅✅ SUCESSO! Usuário E SENHA atualizados!")
        print("\n⚠ IMPORTANTE: Senha foi alterada para 'NovaSenha@123'")
        print("   Você precisará usar essa senha no próximo login")
    else:
        print(f"\n⚠ Redirecionado mas não para lista: {location}")
else:
    print(f"\n✗ Status inesperado: {post_response.status_code}")
    
    if post_response.status_code == 200:
        print("  Verificando erros...")
        if 'alert-danger' in post_response.text:
            errors = re.findall(r'alert alert-danger[^>]*>([^<]+)', post_response.text)
            for err in errors:
                print(f"    - {err.strip()}")

print("\n" + "="*70)
