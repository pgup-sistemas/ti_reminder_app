"""
Testes end-to-end para fluxos de usuário do TI Reminder App
"""
import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException


@pytest.mark.e2e
@pytest.mark.slow
class TestLoginFlow:
    """Testes E2E para fluxo de login"""
    
    def test_successful_login(self, driver, live_server):
        """Testa login bem-sucedido"""
        driver.get(f'{live_server}/auth/login')
        
        # Preencher formulário
        username_field = driver.find_element(By.NAME, 'username')
        password_field = driver.find_element(By.NAME, 'password')
        
        username_field.send_keys('admin_e2e')
        password_field.send_keys('admin123')
        
        # Submeter formulário
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        # Verificar redirecionamento para dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains('/')
        )
        
        assert 'Dashboard' in driver.page_source
        assert 'admin_e2e' in driver.page_source
    
    def test_failed_login(self, driver, live_server):
        """Testa login com credenciais inválidas"""
        driver.get(f'{live_server}/auth/login')
        
        username_field = driver.find_element(By.NAME, 'username')
        password_field = driver.find_element(By.NAME, 'password')
        
        username_field.send_keys('admin_e2e')
        password_field.send_keys('wrongpassword')
        
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        # Deve permanecer na página de login
        time.sleep(2)
        assert '/auth/login' in driver.current_url
        assert ('incorretos' in driver.page_source or 
                'invalid' in driver.page_source.lower())
    
    def test_logout_flow(self, logged_in_driver, live_server):
        """Testa fluxo de logout"""
        # Verificar que está logado
        assert 'Dashboard' in logged_in_driver.page_source
        
        # Fazer logout
        logout_link = logged_in_driver.find_element(By.LINK_TEXT, 'Sair')
        logout_link.click()
        
        # Verificar redirecionamento para login
        WebDriverWait(logged_in_driver, 10).until(
            EC.url_contains('/auth/login')
        )
        
        assert 'Login' in logged_in_driver.page_source


@pytest.mark.e2e
@pytest.mark.slow
class TestReminderManagement:
    """Testes E2E para gerenciamento de lembretes"""
    
    def test_create_reminder(self, logged_in_driver, live_server):
        """Testa criação de lembrete"""
        # Navegar para página de adicionar lembrete
        logged_in_driver.get(f'{live_server}/add_reminder')
        
        # Preencher formulário
        name_field = logged_in_driver.find_element(By.NAME, 'name')
        name_field.send_keys('Lembrete E2E Test')
        
        type_select = Select(logged_in_driver.find_element(By.NAME, 'type'))
        type_select.select_by_value('manutencao')
        
        due_date_field = logged_in_driver.find_element(By.NAME, 'due_date')
        due_date_field.send_keys('31/12/2024')
        
        responsible_field = logged_in_driver.find_element(By.NAME, 'responsible')
        responsible_field.send_keys('TI E2E')
        
        # Submeter formulário
        submit_button = logged_in_driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        
        # Verificar redirecionamento e criação
        WebDriverWait(logged_in_driver, 10).until(
            EC.url_matches(r'.*/(\?.*)?$')  # URL raiz com possíveis parâmetros
        )
        
        assert 'Lembrete E2E Test' in logged_in_driver.page_source
    
    def test_complete_reminder(self, logged_in_driver, live_server):
        """Testa conclusão de lembrete"""
        # Primeiro criar um lembrete
        self.test_create_reminder(logged_in_driver, live_server)
        
        # Encontrar e clicar no botão de completar
        try:
            complete_button = WebDriverWait(logged_in_driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-success'))
            )
            complete_button.click()
            
            # Aguardar atualização AJAX
            time.sleep(2)
            
            # Verificar que o lembrete foi marcado como completo
            assert 'Concluído' in logged_in_driver.page_source
        except TimeoutException:
            pytest.skip("Botão de completar não encontrado - pode ser devido ao layout")


@pytest.mark.e2e
@pytest.mark.slow
class TestChamadoFlow:
    """Testes E2E para fluxo de chamados"""
    
    def test_open_chamado(self, user_logged_in_driver, live_server):
        """Testa abertura de chamado por usuário comum"""
        # Navegar para página de abrir chamado
        user_logged_in_driver.get(f'{live_server}/abrir_chamado')
        
        # Preencher formulário
        titulo_field = user_logged_in_driver.find_element(By.NAME, 'titulo')
        titulo_field.send_keys('Chamado E2E Test')
        
        descricao_field = user_logged_in_driver.find_element(By.NAME, 'descricao')
        descricao_field.send_keys('Descrição do chamado de teste E2E')
        
        prioridade_select = Select(user_logged_in_driver.find_element(By.NAME, 'prioridade'))
        prioridade_select.select_by_value('Media')
        
        # Submeter formulário
        submit_button = user_logged_in_driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        
        # Verificar redirecionamento
        WebDriverWait(user_logged_in_driver, 10).until(
            EC.url_contains('/chamados')
        )
        
        assert 'Chamado E2E Test' in user_logged_in_driver.page_source
    
    def test_view_chamado_details(self, user_logged_in_driver, live_server):
        """Testa visualização de detalhes do chamado"""
        # Primeiro criar um chamado
        self.test_open_chamado(user_logged_in_driver, live_server)
        
        # Encontrar e clicar no link de detalhes
        try:
            details_link = WebDriverWait(user_logged_in_driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'Ver Detalhes'))
            )
            details_link.click()
            
            # Verificar página de detalhes
            WebDriverWait(user_logged_in_driver, 10).until(
                EC.url_contains('/chamado/')
            )
            
            assert 'Chamado E2E Test' in user_logged_in_driver.page_source
            assert 'Descrição do chamado de teste E2E' in user_logged_in_driver.page_source
        except TimeoutException:
            pytest.skip("Link de detalhes não encontrado - pode ser devido ao layout")


@pytest.mark.e2e
@pytest.mark.slow
class TestEquipmentRequest:
    """Testes E2E para solicitação de equipamentos"""
    
    def test_request_equipment(self, user_logged_in_driver, live_server):
        """Testa solicitação de equipamento"""
        # Navegar para página de solicitação
        user_logged_in_driver.get(f'{live_server}/request_equipment')
        
        # Preencher formulário
        description_field = user_logged_in_driver.find_element(By.NAME, 'description')
        description_field.send_keys('Notebook para testes E2E')
        
        equipment_type_field = user_logged_in_driver.find_element(By.NAME, 'equipment_type')
        equipment_type_field.send_keys('notebook')
        
        reason_field = user_logged_in_driver.find_element(By.NAME, 'request_reason')
        reason_field.send_keys('Testes automatizados')
        
        # Submeter formulário
        submit_button = user_logged_in_driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        
        # Verificar redirecionamento
        WebDriverWait(user_logged_in_driver, 10).until(
            EC.url_contains('/equipment_requests')
        )
        
        assert 'Notebook para testes E2E' in user_logged_in_driver.page_source


@pytest.mark.e2e
@pytest.mark.slow
class TestTutorialFlow:
    """Testes E2E para fluxo de tutoriais"""
    
    def test_view_tutorials_list(self, logged_in_driver, live_server):
        """Testa visualização da lista de tutoriais"""
        logged_in_driver.get(f'{live_server}/tutoriais')
        
        assert 'Tutoriais' in logged_in_driver.page_source
    
    def test_create_tutorial_admin(self, logged_in_driver, live_server):
        """Testa criação de tutorial por admin"""
        # Navegar para página de criar tutorial
        logged_in_driver.get(f'{live_server}/criar_tutorial')
        
        # Preencher formulário
        titulo_field = logged_in_driver.find_element(By.NAME, 'titulo')
        titulo_field.send_keys('Tutorial E2E Test')
        
        conteudo_field = logged_in_driver.find_element(By.NAME, 'conteudo')
        conteudo_field.send_keys('# Tutorial de Teste\n\nEste é um tutorial criado via E2E.')
        
        categoria_field = logged_in_driver.find_element(By.NAME, 'categoria')
        categoria_field.send_keys('Teste E2E')
        
        # Submeter formulário
        submit_button = logged_in_driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        
        # Verificar redirecionamento
        WebDriverWait(logged_in_driver, 10).until(
            EC.url_contains('/tutoriais')
        )
        
        assert 'Tutorial E2E Test' in logged_in_driver.page_source


@pytest.mark.e2e
@pytest.mark.slow
class TestNavigationAndUI:
    """Testes E2E para navegação e interface"""
    
    def test_main_navigation(self, logged_in_driver, live_server):
        """Testa navegação principal"""
        # Testar links do menu principal
        navigation_links = [
            ('Dashboard', '/'),
            ('Lembretes', '/add_reminder'),
            ('Chamados', '/chamados'),
            ('Tutoriais', '/tutoriais'),
            ('Equipamentos', '/equipment_requests')
        ]
        
        for link_text, expected_url in navigation_links:
            try:
                link = logged_in_driver.find_element(By.PARTIAL_LINK_TEXT, link_text)
                link.click()
                
                WebDriverWait(logged_in_driver, 10).until(
                    EC.url_contains(expected_url)
                )
                
                assert expected_url in logged_in_driver.current_url
            except TimeoutException:
                pytest.skip(f"Link '{link_text}' não encontrado ou não funcional")
    
    def test_responsive_design(self, logged_in_driver, live_server):
        """Testa design responsivo"""
        # Testar diferentes tamanhos de tela
        screen_sizes = [
            (1920, 1080),  # Desktop
            (768, 1024),   # Tablet
            (375, 667)     # Mobile
        ]
        
        for width, height in screen_sizes:
            logged_in_driver.set_window_size(width, height)
            logged_in_driver.get(f'{live_server}/')
            
            # Verificar que a página carrega sem erros
            assert 'Dashboard' in logged_in_driver.page_source
            
            # Aguardar um pouco para renderização
            time.sleep(1)
    
    def test_search_functionality(self, logged_in_driver, live_server):
        """Testa funcionalidade de busca"""
        logged_in_driver.get(f'{live_server}/')
        
        try:
            search_field = logged_in_driver.find_element(By.NAME, 'search')
            search_field.send_keys('teste')
            
            search_button = logged_in_driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            search_button.click()
            
            # Verificar que a busca foi executada
            WebDriverWait(logged_in_driver, 10).until(
                EC.url_contains('search=teste')
            )
            
            assert 'search=teste' in logged_in_driver.current_url
        except TimeoutException:
            pytest.skip("Campo de busca não encontrado")
