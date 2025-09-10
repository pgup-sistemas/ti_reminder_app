"""
Configurações para testes end-to-end com Selenium
"""
import pytest
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from app import create_app, db
from app.models import User, Sector, SlaConfig
from werkzeug.security import generate_password_hash
import tempfile
import os


@pytest.fixture(scope='session')
def selenium_app():
    """Cria aplicação Flask para testes Selenium"""
    db_fd, db_path = tempfile.mkstemp()
    
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key-e2e',
        'WTF_CSRF_ENABLED': False,
        'MAIL_SUPPRESS_SEND': True,
        'LOG_TO_STDOUT': False,
        'SCHEDULER_API_ENABLED': False,
        'SERVER_NAME': 'localhost:5555'
    }
    
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        db.create_all()
        SlaConfig.criar_configuracoes_padrao()
        
        # Criar dados de teste
        sector = Sector(name='TI')
        db.session.add(sector)
        db.session.commit()
        
        admin_user = User(
            username='admin_e2e',
            email='admin@e2e.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True,
            is_ti=True,
            ativo=True,
            sector_id=sector.id
        )
        
        regular_user = User(
            username='user_e2e',
            email='user@e2e.com',
            password_hash=generate_password_hash('user123'),
            is_admin=False,
            is_ti=False,
            ativo=True,
            sector_id=sector.id
        )
        
        db.session.add_all([admin_user, regular_user])
        db.session.commit()
        
        yield app
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='session')
def live_server(selenium_app):
    """Servidor Flask rodando para testes E2E"""
    def run_server():
        selenium_app.run(host='localhost', port=5555, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Aguardar servidor iniciar
    time.sleep(2)
    
    yield 'http://localhost:5555'


@pytest.fixture(scope='session')
def driver():
    """Driver Selenium Chrome"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Executar sem interface gráfica
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()


@pytest.fixture
def logged_in_driver(driver, live_server):
    """Driver com usuário admin logado"""
    driver.get(f'{live_server}/auth/login')
    
    username_field = driver.find_element('name', 'username')
    password_field = driver.find_element('name', 'password')
    
    username_field.send_keys('admin_e2e')
    password_field.send_keys('admin123')
    
    login_button = driver.find_element('css selector', 'button[type="submit"]')
    login_button.click()
    
    return driver


@pytest.fixture
def user_logged_in_driver(driver, live_server):
    """Driver com usuário comum logado"""
    driver.get(f'{live_server}/auth/login')
    
    username_field = driver.find_element('name', 'username')
    password_field = driver.find_element('name', 'password')
    
    username_field.send_keys('user_e2e')
    password_field.send_keys('user123')
    
    login_button = driver.find_element('css selector', 'button[type="submit"]')
    login_button.click()
    
    return driver
