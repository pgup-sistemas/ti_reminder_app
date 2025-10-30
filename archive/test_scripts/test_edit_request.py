"""
Script de teste para simular edição de usuário via HTTP
"""
import requests
from bs4 import BeautifulSoup

# URL base
BASE_URL = "http://192.168.1.86:5000"
LOGIN_URL = f"{BASE_URL}/login"
EDIT_URL = f"{BASE_URL}/configuracoes/usuarios/1/editar"

print("="*70)
print("TESTE DE EDIÇÃO DE USUÁRIO")
print("="*70)

# Criar sessão para manter cookies
session = requests.Session()

# 1. Fazer login primeiro
print("\n[1] Fazendo login...")
try:
    # Pegar página de login para obter CSRF token
    login_page = session.get(LOGIN_URL)
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    if csrf_token:
        csrf_value = csrf_token.get('value')
        print(f"✓ CSRF token obtido: {csrf_value[:20]}...")
        
        # Fazer login (ajuste username/password se necessário)
        login_data = {
            'username': 'admin_test',
            'password': 'Admin@123',  # Ajuste se a senha for diferente
            'csrf_token': csrf_value,
            'remember_me': 'y'
        }
        
        login_response = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        
        if login_response.status_code == 200 and '/login' not in login_response.url:
            print(f"✓ Login realizado com sucesso!")
            print(f"  Redirecionado para: {login_response.url}")
        else:
            print(f"✗ Falha no login. Status: {login_response.status_code}")
            print(f"  URL final: {login_response.url}")
            if 'Invalid username or password' in login_response.text:
                print("  → Credenciais inválidas")
            exit(1)
    else:
        print("✗ Não foi possível obter CSRF token da página de login")
        exit(1)
        
except Exception as e:
    print(f"✗ Erro ao fazer login: {e}")
    exit(1)

# 2. Acessar página de edição
print("\n[2] Acessando página de edição...")
try:
    edit_page = session.get(EDIT_URL)
    
    if edit_page.status_code == 200:
        print(f"✓ Página de edição acessada com sucesso")
        
        # Extrair CSRF token do formulário
        soup = BeautifulSoup(edit_page.text, 'html.parser')
        form = soup.find('form', {'id': 'userForm'})
        
        if form:
            csrf_token = form.find('input', {'name': 'csrf_token'})
            if csrf_token:
                csrf_value = csrf_token.get('value')
                print(f"✓ CSRF token do formulário obtido: {csrf_value[:20]}...")
            else:
                print("✗ CSRF token não encontrado no formulário")
                exit(1)
        else:
            print("✗ Formulário não encontrado na página")
            exit(1)
    else:
        print(f"✗ Erro ao acessar página. Status: {edit_page.status_code}")
        exit(1)
        
except Exception as e:
    print(f"✗ Erro ao acessar página de edição: {e}")
    exit(1)

# 3. Submeter formulário de edição
print("\n[3] Submetendo formulário de edição...")
try:
    # Dados do formulário (editando o username como teste)
    form_data = {
        'csrf_token': csrf_value,
        'username': 'admin_test_editado',  # Mudando o username como teste
        'email': 'admin@test.com',
        'sector_id': '1',  # Assumindo que TI é setor 1
        'is_admin': 'y',
        'is_ti': 'y',
        'ativo': 'on',
        'change_password': '',  # Não mudar senha
        'new_password': '',
        'confirm_password': '',
        'submit': 'Salvar Alterações'
    }
    
    print("  Dados sendo enviados:")
    for key, value in form_data.items():
        if key not in ['csrf_token', 'new_password', 'confirm_password']:
            print(f"    - {key}: {value}")
    
    edit_response = session.post(EDIT_URL, data=form_data, allow_redirects=True)
    
    print(f"\n  Status da resposta: {edit_response.status_code}")
    print(f"  URL final: {edit_response.url}")
    
    # Verificar se teve sucesso
    if edit_response.status_code == 200:
        # Procurar por mensagens de sucesso ou erro no HTML
        soup = BeautifulSoup(edit_response.text, 'html.parser')
        
        # Procurar pelo container de mensagens flash
        flash_container = soup.find('div', {'id': 'flask-messages'})
        if flash_container:
            messages = flash_container.get('data-messages', '')
            print(f"\n✓ Mensagens flash encontradas:")
            print(f"  {messages}")
        
        # Se foi redirecionado para lista de usuários, sucesso!
        if '/configuracoes/usuarios' in edit_response.url and '/editar' not in edit_response.url:
            print("\n✓✓✓ SUCESSO! Usuário editado com sucesso!")
            print("  Foi redirecionado para a lista de usuários")
        elif '/editar' in edit_response.url:
            print("\n⚠ Permaneceu na página de edição - pode haver erros de validação")
            
            # Procurar por mensagens de erro
            errors = soup.find_all('div', class_='invalid-feedback')
            if errors:
                print("  Erros encontrados:")
                for error in errors:
                    print(f"    - {error.get_text().strip()}")
        
    else:
        print(f"✗ Erro na submissão. Status: {edit_response.status_code}")
    
except Exception as e:
    print(f"✗ Erro ao submeter formulário: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TESTE CONCLUÍDO")
print("="*70)
