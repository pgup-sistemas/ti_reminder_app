"""
Configurações globais para testes do TI Reminder App
"""
import pytest
import tempfile
import os
from app import create_app, db
from app.models import User, Sector, SlaConfig
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app():
    """Cria uma instância da aplicação para testes"""
    # Criar um arquivo temporário para o banco de dados de teste
    db_fd, db_path = tempfile.mkstemp()
    
    # Configurações específicas para teste
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'MAIL_SUPPRESS_SEND': True,
        'LOG_TO_STDOUT': False,
        'SCHEDULER_API_ENABLED': False
    }
    
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        db.create_all()
        # Criar configurações padrão de SLA
        SlaConfig.criar_configuracoes_padrao()
        yield app
        
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Cliente de teste Flask"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Runner de comandos CLI"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Sessão de banco de dados para cada teste"""
    with app.app_context():
        # Limpar todas as tabelas antes de cada teste
        db.session.remove()
        db.drop_all()
        db.create_all()
        
        # Recriar configurações padrão
        SlaConfig.criar_configuracoes_padrao()
        
        yield db.session
        
        # Cleanup após cada teste
        db.session.remove()


@pytest.fixture
def sample_sector(db_session):
    """Cria um setor de exemplo"""
    sector = Sector(name='TI')
    db_session.add(sector)
    db_session.commit()
    return sector


@pytest.fixture
def admin_user(db_session, sample_sector):
    """Cria um usuário administrador de teste"""
    user = User(
        username='admin_test',
        email='admin@test.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True,
        is_ti=True,
        ativo=True,
        sector_id=sample_sector.id
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def regular_user(db_session, sample_sector):
    """Cria um usuário comum de teste"""
    user = User(
        username='user_test',
        email='user@test.com',
        password_hash=generate_password_hash('user123'),
        is_admin=False,
        is_ti=False,
        ativo=True,
        sector_id=sample_sector.id
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def ti_user(db_session, sample_sector):
    """Cria um usuário da equipe de TI de teste"""
    user = User(
        username='ti_test',
        email='ti@test.com',
        password_hash=generate_password_hash('ti123'),
        is_admin=False,
        is_ti=True,
        ativo=True,
        sector_id=sample_sector.id
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def authenticated_client(client, admin_user):
    """Cliente autenticado como administrador"""
    with client.session_transaction() as sess:
        sess['user_id'] = admin_user.id
        sess['_fresh'] = True
    return client


@pytest.fixture
def user_authenticated_client(client, regular_user):
    """Cliente autenticado como usuário comum"""
    with client.session_transaction() as sess:
        sess['user_id'] = regular_user.id
        sess['_fresh'] = True
    return client


class TestDataFactory:
    """Factory para criar dados de teste"""
    
    @staticmethod
    def create_user(db_session, **kwargs):
        """Cria um usuário com dados customizados"""
        defaults = {
            'username': 'test_user',
            'email': 'test@example.com',
            'password_hash': generate_password_hash('password123'),
            'is_admin': False,
            'is_ti': False,
            'ativo': True
        }
        defaults.update(kwargs)
        
        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        return user
    
    @staticmethod
    def create_sector(db_session, name='Test Sector'):
        """Cria um setor de teste"""
        sector = Sector(name=name)
        db_session.add(sector)
        db_session.commit()
        return sector


@pytest.fixture
def test_factory():
    """Fixture para acessar a factory de dados de teste"""
    return TestDataFactory
