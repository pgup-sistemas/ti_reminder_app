"""
Testes de integração para as rotas do TI Reminder App
"""
import pytest
from flask import url_for
from app.models import User, Sector, Reminder, Chamado, EquipmentRequest, Tutorial
from datetime import date, timedelta


@pytest.mark.integration
class TestAuthenticationRoutes:
    """Testes para rotas de autenticação"""
    
    def test_login_required_redirect(self, client):
        """Testa redirecionamento para login quando não autenticado"""
        response = client.get('/')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_admin_required_redirect(self, user_authenticated_client):
        """Testa redirecionamento quando usuário comum tenta acessar área admin"""
        response = user_authenticated_client.get('/admin/users')
        assert response.status_code == 302


@pytest.mark.integration
class TestMainRoutes:
    """Testes para rotas principais"""
    
    def test_index_authenticated(self, authenticated_client):
        """Testa acesso à página inicial autenticado"""
        response = authenticated_client.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_index_with_search(self, authenticated_client, db_session, admin_user, sample_sector):
        """Testa busca na página inicial"""
        # Criar um lembrete para buscar
        reminder = Reminder(
            name='Backup Teste',
            type='manutencao',
            due_date=date.today() + timedelta(days=1),
            responsible='TI',
            user_id=admin_user.id,
            sector_id=sample_sector.id
        )
        db_session.add(reminder)
        db_session.commit()
        
        response = authenticated_client.get('/?search=backup')
        assert response.status_code == 200
        assert b'Backup Teste' in response.data


@pytest.mark.integration
class TestReminderRoutes:
    """Testes para rotas de lembretes"""
    
    def test_add_reminder_get(self, authenticated_client):
        """Testa acesso ao formulário de adicionar lembrete"""
        response = authenticated_client.get('/add_reminder')
        assert response.status_code == 200
        assert b'Adicionar Lembrete' in response.data
    
    def test_add_reminder_post(self, authenticated_client, db_session, sample_sector):
        """Testa criação de lembrete via POST"""
        data = {
            'name': 'Teste Lembrete',
            'type': 'manutencao',
            'due_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'responsible': 'TI',
            'frequency': 'semanal',
            'sector_id': sample_sector.id
        }
        
        response = authenticated_client.post('/add_reminder', data=data)
        assert response.status_code == 302  # Redirect após sucesso
        
        # Verificar se foi criado
        reminder = Reminder.query.filter_by(name='Teste Lembrete').first()
        assert reminder is not None
        assert reminder.type == 'manutencao'
    
    def test_edit_reminder(self, authenticated_client, db_session, admin_user, sample_sector):
        """Testa edição de lembrete"""
        reminder = Reminder(
            name='Lembrete Original',
            type='manutencao',
            due_date=date.today() + timedelta(days=1),
            responsible='TI',
            user_id=admin_user.id,
            sector_id=sample_sector.id
        )
        db_session.add(reminder)
        db_session.commit()
        
        # GET - formulário de edição
        response = authenticated_client.get(f'/edit_reminder/{reminder.id}')
        assert response.status_code == 200
        assert b'Lembrete Original' in response.data
        
        # POST - atualizar lembrete
        data = {
            'name': 'Lembrete Editado',
            'type': 'backup',
            'due_date': reminder.due_date.strftime('%Y-%m-%d'),
            'responsible': 'TI',
            'sector_id': sample_sector.id
        }
        
        response = authenticated_client.post(f'/edit_reminder/{reminder.id}', data=data)
        assert response.status_code == 302
        
        # Verificar alteração
        db_session.refresh(reminder)
        assert reminder.name == 'Lembrete Editado'
        assert reminder.type == 'backup'
    
    def test_delete_reminder(self, authenticated_client, db_session, admin_user, sample_sector):
        """Testa exclusão de lembrete"""
        reminder = Reminder(
            name='Lembrete para Deletar',
            type='teste',
            due_date=date.today(),
            responsible='TI',
            user_id=admin_user.id,
            sector_id=sample_sector.id
        )
        db_session.add(reminder)
        db_session.commit()
        reminder_id = reminder.id
        
        response = authenticated_client.post(f'/delete_reminder/{reminder_id}')
        assert response.status_code == 302
        
        # Verificar se foi deletado
        deleted_reminder = Reminder.query.get(reminder_id)
        assert deleted_reminder is None


@pytest.mark.integration
class TestChamadoRoutes:
    """Testes para rotas de chamados"""
    
    def test_chamados_list(self, authenticated_client):
        """Testa listagem de chamados"""
        response = authenticated_client.get('/chamados')
        assert response.status_code == 200
        assert b'Chamados' in response.data
    
    def test_abrir_chamado_get(self, user_authenticated_client):
        """Testa acesso ao formulário de abrir chamado"""
        response = user_authenticated_client.get('/abrir_chamado')
        assert response.status_code == 200
        assert b'Abrir Chamado' in response.data
    
    def test_abrir_chamado_post(self, user_authenticated_client, db_session, regular_user, sample_sector):
        """Testa abertura de chamado via POST"""
        data = {
            'titulo': 'Problema no Sistema',
            'descricao': 'O sistema está apresentando erro',
            'prioridade': 'Media',
            'setor_id': sample_sector.id
        }
        
        response = user_authenticated_client.post('/abrir_chamado', data=data)
        assert response.status_code == 302
        
        # Verificar se foi criado
        chamado = Chamado.query.filter_by(titulo='Problema no Sistema').first()
        assert chamado is not None
        assert chamado.solicitante_id == regular_user.id
        assert chamado.status == 'Aberto'
    
    def test_chamado_detail(self, authenticated_client, db_session, regular_user, sample_sector):
        """Testa visualização de detalhes do chamado"""
        chamado = Chamado(
            titulo='Chamado Teste',
            descricao='Descrição do teste',
            prioridade='Alta',
            solicitante_id=regular_user.id,
            setor_id=sample_sector.id
        )
        db_session.add(chamado)
        db_session.commit()
        
        response = authenticated_client.get(f'/chamado/{chamado.id}')
        assert response.status_code == 200
        assert b'Chamado Teste' in response.data
        assert 'Descrição do teste'.encode('utf-8') in response.data


@pytest.mark.integration
class TestEquipmentRoutes:
    """Testes para rotas de equipamentos"""
    
    def test_equipment_requests_list(self, authenticated_client):
        """Testa listagem de solicitações de equipamento"""
        response = authenticated_client.get('/equipment_requests')
        assert response.status_code == 200
        assert 'Solicitações de Equipamento'.encode('utf-8') in response.data
    
    def test_request_equipment_get(self, user_authenticated_client):
        """Testa acesso ao formulário de solicitação de equipamento"""
        response = user_authenticated_client.get('/request_equipment')
        assert response.status_code == 200
        assert b'Solicitar Equipamento' in response.data
    
    def test_request_equipment_post(self, user_authenticated_client, db_session, regular_user):
        """Testa solicitação de equipamento via POST"""
        data = {
            'description': 'Notebook para desenvolvimento',
            'equipment_type': 'notebook',
            'request_reason': 'Novo funcionário',
            'destination_sector': 'TI'
        }
        
        response = user_authenticated_client.post('/request_equipment', data=data)
        assert response.status_code == 302
        
        # Verificar se foi criado
        request = EquipmentRequest.query.filter_by(description='Notebook para desenvolvimento').first()
        assert request is not None
        assert request.requester_id == regular_user.id
        assert request.status == 'Solicitado'


@pytest.mark.integration
class TestTutorialRoutes:
    """Testes para rotas de tutoriais"""
    
    def test_tutorials_list(self, authenticated_client):
        """Testa listagem de tutoriais"""
        response = authenticated_client.get('/tutoriais')
        assert response.status_code == 200
        assert b'Tutoriais' in response.data
    
    def test_create_tutorial_admin_only(self, user_authenticated_client):
        """Testa que apenas admin pode criar tutorial"""
        response = user_authenticated_client.get('/criar_tutorial')
        assert response.status_code == 302  # Redirect por falta de permissão
    
    def test_create_tutorial_get(self, authenticated_client):
        """Testa acesso ao formulário de criar tutorial (admin)"""
        response = authenticated_client.get('/criar_tutorial')
        assert response.status_code == 200
        assert b'Criar Tutorial' in response.data
    
    def test_create_tutorial_post(self, authenticated_client, db_session, admin_user):
        """Testa criação de tutorial via POST"""
        data = {
            'titulo': 'Tutorial de Teste',
            'conteudo': '# Tutorial\n\nEste é um tutorial de teste.',
            'categoria': 'Teste'
        }
        
        response = authenticated_client.post('/criar_tutorial', data=data)
        assert response.status_code == 302
        
        # Verificar se foi criado
        tutorial = Tutorial.query.filter_by(titulo='Tutorial de Teste').first()
        assert tutorial is not None
        assert tutorial.autor_id == admin_user.id
    
    def test_tutorial_detail(self, authenticated_client, db_session, admin_user):
        """Testa visualização de tutorial"""
        tutorial = Tutorial(
            titulo='Tutorial Detalhado',
            conteudo='# Conteúdo\n\nDetalhes do tutorial.',
            categoria='Teste',
            autor_id=admin_user.id
        )
        db_session.add(tutorial)
        db_session.commit()
        
        response = authenticated_client.get(f'/tutorial/{tutorial.id}')
        assert response.status_code == 200
        assert b'Tutorial Detalhado' in response.data


@pytest.mark.integration
class TestAPIRoutes:
    """Testes para rotas de API/AJAX"""
    
    def test_complete_reminder_ajax(self, authenticated_client, db_session, admin_user, sample_sector):
        """Testa conclusão de lembrete via AJAX"""
        reminder = Reminder(
            name='Lembrete AJAX',
            type='teste',
            due_date=date.today(),
            responsible='TI',
            user_id=admin_user.id,
            sector_id=sample_sector.id
        )
        db_session.add(reminder)
        db_session.commit()
        
        response = authenticated_client.post(
            f'/complete_reminder/{reminder.id}',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        
        # Verificar se foi marcado como completo
        db_session.refresh(reminder)
        assert reminder.completed
    
    def test_toggle_task_ajax(self, authenticated_client, db_session, admin_user, sample_sector):
        """Testa toggle de tarefa via AJAX"""
        from app.models import Task
        
        task = Task(
            description='Tarefa AJAX',
            responsible='TI',
            user_id=admin_user.id,
            sector_id=sample_sector.id
        )
        db_session.add(task)
        db_session.commit()
        
        response = authenticated_client.post(
            f'/toggle_task/{task.id}',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        
        # Verificar se foi marcado como completo
        db_session.refresh(task)
        assert task.completed


@pytest.mark.integration
class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    def test_404_error(self, authenticated_client):
        """Testa página não encontrada"""
        response = authenticated_client.get('/pagina_inexistente')
        assert response.status_code == 404
    
    def test_access_nonexistent_reminder(self, authenticated_client):
        """Testa acesso a lembrete inexistente"""
        response = authenticated_client.get('/edit_reminder/99999')
        assert response.status_code == 404
    
    def test_access_nonexistent_chamado(self, authenticated_client):
        """Testa acesso a chamado inexistente"""
        response = authenticated_client.get('/chamado/99999')
        assert response.status_code == 404
