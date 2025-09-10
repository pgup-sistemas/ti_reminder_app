"""
Testes de integração para autenticação do TI Reminder App
"""
import pytest
from flask import url_for
from app.models import User
from werkzeug.security import generate_password_hash


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationFlow:
    """Testes para fluxo completo de autenticação"""
    
    def test_login_flow(self, client, db_session, sample_sector):
        """Testa fluxo completo de login"""
        # Criar usuário para teste
        user = User(
            username='logintest',
            email='login@test.com',
            password_hash=generate_password_hash('password123'),
            ativo=True,
            sector_id=sample_sector.id
        )
        db_session.add(user)
        db_session.commit()
        
        # Acessar página de login
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Login' in response.data
        
        # Fazer login com credenciais corretas
        response = client.post('/auth/login', data={
            'username': 'logintest',
            'password': 'password123'
        })
        assert response.status_code == 302  # Redirect após login
        
        # Verificar se foi redirecionado para dashboard
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_login_invalid_credentials(self, client, db_session, regular_user):
        """Testa login com credenciais inválidas"""
        response = client.post('/auth/login', data={
            'username': 'user_test',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200  # Permanece na página de login
        assert 'Usuário ou senha incorretos'.encode('utf-8') in response.data or b'Invalid' in response.data
    
    def test_login_inactive_user(self, client, db_session, sample_sector):
        """Testa login com usuário inativo"""
        user = User(
            username='inactive',
            email='inactive@test.com',
            password_hash=generate_password_hash('password123'),
            ativo=False,
            sector_id=sample_sector.id
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post('/auth/login', data={
            'username': 'inactive',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'inativo' in response.data or b'inactive' in response.data
    
    def test_logout_flow(self, authenticated_client):
        """Testa fluxo de logout"""
        # Verificar que está logado
        response = authenticated_client.get('/')
        assert response.status_code == 200
        
        # Fazer logout
        response = authenticated_client.get('/auth/logout')
        assert response.status_code == 302
        
        # Verificar que foi deslogado
        response = authenticated_client.get('/')
        assert response.status_code == 302  # Redirect para login
        assert '/auth/login' in response.location
    
    def test_password_reset_request(self, client, db_session, regular_user):
        """Testa solicitação de reset de senha"""
        response = client.get('/auth/reset_password_request')
        assert response.status_code == 200
        
        response = client.post('/auth/reset_password_request', data={
            'email': regular_user.email
        })
        assert response.status_code == 302  # Redirect após solicitação
        
        # Verificar se token foi gerado
        db_session.refresh(regular_user)
        assert regular_user.reset_token is not None
    
    def test_password_reset_invalid_email(self, client):
        """Testa reset com email inexistente"""
        response = client.post('/auth/reset_password_request', data={
            'email': 'inexistente@test.com'
        })
        assert response.status_code == 200  # Permanece na página
        assert 'não encontrado'.encode('utf-8') in response.data or b'not found' in response.data
    
    def test_session_persistence(self, client, db_session, regular_user):
        """Testa persistência da sessão"""
        # Fazer login
        client.post('/auth/login', data={
            'username': regular_user.username,
            'password': 'user123'
        })
        
        # Verificar múltiplas requisições mantêm sessão
        for _ in range(3):
            response = client.get('/')
            assert response.status_code == 200
            assert b'Dashboard' in response.data


@pytest.mark.integration
@pytest.mark.auth
class TestAuthorizationLevels:
    """Testes para níveis de autorização"""
    
    def test_admin_access(self, client, db_session, admin_user):
        """Testa acesso de administrador"""
        # Login como admin
        client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'admin123'
        })
        
        # Acessar área administrativa
        response = client.get('/admin/users')
        assert response.status_code == 200
        
        # Acessar criação de tutorial
        response = client.get('/criar_tutorial')
        assert response.status_code == 200
    
    def test_ti_user_access(self, client, db_session, ti_user):
        """Testa acesso de usuário TI"""
        # Login como TI
        client.post('/auth/login', data={
            'username': ti_user.username,
            'password': 'ti123'
        })
        
        # Deve ter acesso a funcionalidades de TI
        response = client.get('/chamados')
        assert response.status_code == 200
        
        # Deve poder aprovar equipamentos
        response = client.get('/equipment_requests')
        assert response.status_code == 200
    
    def test_regular_user_restrictions(self, client, db_session, regular_user):
        """Testa restrições de usuário comum"""
        # Login como usuário comum
        client.post('/auth/login', data={
            'username': regular_user.username,
            'password': 'user123'
        })
        
        # Não deve acessar área admin
        response = client.get('/admin/users')
        assert response.status_code == 302  # Redirect
        
        # Não deve criar tutoriais
        response = client.get('/criar_tutorial')
        assert response.status_code == 302  # Redirect
    
    def test_cross_user_data_access(self, client, db_session, test_factory, sample_sector):
        """Testa que usuários não acessam dados de outros"""
        # Criar dois usuários
        user1 = test_factory.create_user(
            db_session, 
            username='user1', 
            email='user1@test.com',
            sector_id=sample_sector.id
        )
        user2 = test_factory.create_user(
            db_session, 
            username='user2', 
            email='user2@test.com',
            sector_id=sample_sector.id
        )
        
        # Criar lembrete para user1
        from app.models import Reminder
        reminder = Reminder(
            name='Lembrete Privado',
            type='teste',
            due_date='2024-12-31',
            responsible='User1',
            user_id=user1.id,
            sector_id=sample_sector.id
        )
        db_session.add(reminder)
        db_session.commit()
        
        # Login como user2
        client.post('/auth/login', data={
            'username': 'user2',
            'password': 'password123'
        })
        
        # user2 não deve ver lembrete de user1 na dashboard
        response = client.get('/')
        assert response.status_code == 200
        assert b'Lembrete Privado' not in response.data
