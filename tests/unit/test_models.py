"""
Testes unitários para os models do TI Reminder App
"""
import pytest
from datetime import datetime, timedelta, date
from app.models import (
    User, Sector, Reminder, Task, Chamado, ComentarioChamado,
    Tutorial, EquipmentRequest, SlaConfig
)
from app import db


@pytest.mark.unit
class TestUser:
    """Testes para o model User"""
    
    def test_create_user(self, db_session):
        """Testa criação de usuário"""
        user = User(
            username='testuser',
            email='test@example.com',
            is_admin=False,
            is_ti=False,
            ativo=True
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('password123')
        assert not user.is_admin
        assert not user.is_ti
        assert user.ativo
    
    def test_password_hashing(self, db_session):
        """Testa hash e verificação de senha"""
        user = User(username='test', email='test@test.com')
        user.set_password('secret')
        
        assert user.password_hash != 'secret'
        assert user.check_password('secret')
        assert not user.check_password('wrong')
    
    def test_reset_token_generation(self, db_session, regular_user):
        """Testa geração de token de reset"""
        token = regular_user.generate_reset_token()
        
        assert token is not None
        assert len(token) == 64  # hex token de 32 bytes = 64 chars
        assert regular_user.reset_token == token
        assert regular_user.reset_token_expiry is not None
        assert regular_user.verify_reset_token(token)
    
    def test_reset_token_expiry(self, db_session, regular_user):
        """Testa expiração do token de reset"""
        token = regular_user.generate_reset_token()
        
        # Simular token expirado
        regular_user.reset_token_expiry = datetime.utcnow() - timedelta(hours=2)
        db_session.commit()
        
        assert not regular_user.verify_reset_token(token)
    
    def test_clear_reset_token(self, db_session, regular_user):
        """Testa limpeza do token de reset"""
        regular_user.generate_reset_token()
        regular_user.clear_reset_token()
        
        assert regular_user.reset_token is None
        assert regular_user.reset_token_expiry is None


@pytest.mark.unit
class TestSector:
    """Testes para o model Sector"""
    
    def test_create_sector(self, db_session):
        """Testa criação de setor"""
        sector = Sector(name='Recursos Humanos')
        db_session.add(sector)
        db_session.commit()
        
        assert sector.id is not None
        assert sector.name == 'Recursos Humanos'
    
    def test_sector_unique_name(self, db_session):
        """Testa unicidade do nome do setor"""
        sector1 = Sector(name='TI')
        sector2 = Sector(name='TI')
        
        db_session.add(sector1)
        db_session.commit()
        
        db_session.add(sector2)
        with pytest.raises(Exception):  # Violação de constraint UNIQUE
            db_session.commit()


@pytest.mark.unit
class TestReminder:
    """Testes para o model Reminder"""
    
    def test_create_reminder(self, db_session, regular_user, sample_sector):
        """Testa criação de lembrete"""
        reminder = Reminder(
            name='Backup Semanal',
            type='manutencao',
            due_date=date.today() + timedelta(days=7),
            responsible='TI',
            frequency='semanal',
            user_id=regular_user.id,
            sector_id=sample_sector.id
        )
        
        db_session.add(reminder)
        db_session.commit()
        
        assert reminder.id is not None
        assert reminder.name == 'Backup Semanal'
        assert reminder.type == 'manutencao'
        assert not reminder.completed
        assert not reminder.notified
        assert reminder.status == 'ativo'
    
    def test_reminder_relationships(self, db_session, regular_user, sample_sector):
        """Testa relacionamentos do lembrete"""
        reminder = Reminder(
            name='Test Reminder',
            type='test',
            due_date=date.today(),
            responsible='Test',
            user_id=regular_user.id,
            sector_id=sample_sector.id
        )
        
        db_session.add(reminder)
        db_session.commit()
        
        assert reminder.usuario == regular_user
        assert reminder.sector == sample_sector
        assert reminder in regular_user.reminders
        assert reminder in sample_sector.reminders


@pytest.mark.unit
class TestChamado:
    """Testes para o model Chamado"""
    
    def test_create_chamado(self, db_session, regular_user, ti_user, sample_sector):
        """Testa criação de chamado"""
        chamado = Chamado(
            titulo='Problema no computador',
            descricao='O computador não liga',
            status='Aberto',
            prioridade='Media',
            solicitante_id=regular_user.id,
            setor_id=sample_sector.id,
            responsavel_ti_id=ti_user.id
        )
        
        db_session.add(chamado)
        db_session.commit()
        
        assert chamado.id is not None
        assert chamado.titulo == 'Problema no computador'
        assert chamado.status == 'Aberto'
        assert chamado.prioridade == 'Media'
        assert chamado.data_abertura is not None
        assert chamado.solicitante == regular_user
        assert chamado.responsavel_ti == ti_user
    
    def test_chamado_sla_calculation(self, db_session, regular_user, sample_sector):
        """Testa cálculo de SLA do chamado"""
        chamado = Chamado(
            titulo='Teste SLA',
            descricao='Teste',
            prioridade='Alta',
            solicitante_id=regular_user.id,
            setor_id=sample_sector.id
        )
        
        db_session.add(chamado)
        db_session.commit()
        
        chamado.calcular_sla()
        
        assert chamado.prazo_sla is not None
        # Para prioridade Alta, deve ser 4 horas após abertura
        expected_sla = chamado.data_abertura + timedelta(hours=4)
        assert abs((chamado.prazo_sla - expected_sla).total_seconds()) < 60
    
    def test_chamado_status_sla(self, db_session, regular_user, sample_sector):
        """Testa status visual do SLA"""
        chamado = Chamado(
            titulo='Teste Status SLA',
            descricao='Teste',
            prioridade='Critica',
            solicitante_id=regular_user.id,
            setor_id=sample_sector.id
        )
        
        db_session.add(chamado)
        db_session.commit()
        
        # Sem SLA definido
        assert chamado.status_sla == 'normal'
        
        # Com SLA futuro
        chamado.prazo_sla = datetime.utcnow() + timedelta(hours=2)
        assert chamado.status_sla == 'normal'
        
        # SLA próximo do vencimento (menos de 1 hora)
        chamado.prazo_sla = datetime.utcnow() + timedelta(minutes=30)
        assert chamado.status_sla == 'atencao'
        
        # SLA vencido
        chamado.prazo_sla = datetime.utcnow() - timedelta(hours=1)
        assert chamado.status_sla == 'vencido'
        
        # SLA cumprido
        chamado.sla_cumprido = True
        assert chamado.status_sla == 'cumprido'
    
    def test_marcar_primeira_resposta(self, db_session, regular_user, sample_sector):
        """Testa marcação da primeira resposta"""
        chamado = Chamado(
            titulo='Teste Primeira Resposta',
            descricao='Teste',
            prioridade='Media',
            solicitante_id=regular_user.id,
            setor_id=sample_sector.id
        )
        
        db_session.add(chamado)
        db_session.commit()
        
        chamado.calcular_sla()
        chamado.marcar_primeira_resposta()
        
        assert chamado.data_primeira_resposta is not None
        assert chamado.tempo_resposta_horas is not None
        assert chamado.sla_cumprido is not None


@pytest.mark.unit
class TestEquipmentRequest:
    """Testes para o model EquipmentRequest"""
    
    def test_create_equipment_request(self, db_session, regular_user):
        """Testa criação de solicitação de equipamento"""
        request = EquipmentRequest(
            description='Notebook para desenvolvimento',
            equipment_type='notebook',
            request_reason='Novo funcionário',
            requester_id=regular_user.id
        )
        
        db_session.add(request)
        db_session.commit()
        
        assert request.id is not None
        assert request.description == 'Notebook para desenvolvimento'
        assert request.status == 'Solicitado'
        assert request.requester == regular_user
        assert request.request_date is not None
    
    def test_equipment_request_permissions(self, db_session, regular_user, admin_user, ti_user, sample_sector):
        """Testa permissões da solicitação de equipamento"""
        request = EquipmentRequest(
            description='Test Equipment',
            requester_id=regular_user.id
        )
        
        db_session.add(request)
        db_session.commit()
        
        # Solicitante pode editar
        assert request.can_be_edited_by(regular_user)
        
        # Admin pode aprovar e editar
        assert request.can_be_approved_by(admin_user)
        assert request.can_be_edited_by(admin_user)
        
        # TI pode aprovar e editar
        assert request.can_be_approved_by(ti_user)
        assert request.can_be_edited_by(ti_user)
        
        # Outro usuário não pode
        other_user = User(
            username='other', 
            email='other@test.com',
            password_hash='hashed_password',
            sector_id=sample_sector.id
        )
        db_session.add(other_user)
        db_session.commit()
        
        assert not request.can_be_approved_by(other_user)
        assert not request.can_be_edited_by(other_user)


@pytest.mark.unit
class TestSlaConfig:
    """Testes para o model SlaConfig"""
    
    def test_get_tempo_sla(self, db_session):
        """Testa obtenção do tempo de SLA por prioridade"""
        # As configurações padrão já foram criadas no conftest
        assert SlaConfig.get_tempo_sla('Critica') == 2
        assert SlaConfig.get_tempo_sla('Alta') == 4
        assert SlaConfig.get_tempo_sla('Media') == 24
        assert SlaConfig.get_tempo_sla('Baixa') == 72
        
        # Prioridade inexistente deve retornar padrão
        assert SlaConfig.get_tempo_sla('Inexistente') == 24
    
    def test_criar_configuracoes_padrao(self, db_session):
        """Testa criação das configurações padrão"""
        # Limpar configurações existentes
        SlaConfig.query.delete()
        db_session.commit()
        
        # Recriar configurações padrão
        SlaConfig.criar_configuracoes_padrao()
        
        configs = SlaConfig.query.all()
        assert len(configs) == 4
        
        prioridades = [config.prioridade for config in configs]
        assert 'Critica' in prioridades
        assert 'Alta' in prioridades
        assert 'Media' in prioridades
        assert 'Baixa' in prioridades


@pytest.mark.unit
class TestTutorial:
    """Testes para o model Tutorial"""
    
    def test_create_tutorial(self, db_session, admin_user):
        """Testa criação de tutorial"""
        tutorial = Tutorial(
            titulo='Como resetar senha',
            conteudo='# Tutorial\n\nPasso 1: ...',
            categoria='Autenticação',
            autor_id=admin_user.id
        )
        
        db_session.add(tutorial)
        db_session.commit()
        
        assert tutorial.id is not None
        assert tutorial.titulo == 'Como resetar senha'
        assert tutorial.categoria == 'Autenticação'
        assert tutorial.autor == admin_user
        assert tutorial.data_criacao is not None
    
    def test_tutorial_relationships(self, db_session, admin_user):
        """Testa relacionamentos do tutorial"""
        tutorial = Tutorial(
            titulo='Test Tutorial',
            conteudo='Content',
            autor_id=admin_user.id
        )
        
        db_session.add(tutorial)
        db_session.commit()
        
        assert tutorial in admin_user.tutoriais
