import pytest
from unittest.mock import Mock, patch
from datetime import date

from app.services.dashboard_service import DashboardService
from app.services.permission_manager import PermissionManager


class TestDashboardRefactor:
    """Testes para a refatoração do dashboard"""

    def test_dashboard_service_creation(self):
        """Testa se o DashboardService pode ser criado"""
        service = DashboardService()
        assert service is not None

    def test_permission_manager_creation(self):
        """Testa se o PermissionManager pode ser criado"""
        manager = PermissionManager()
        assert manager is not None

    @patch('app.services.permission_manager.session')
    def test_get_user_permissions_admin(self, mock_session):
        """Testa obtenção de permissões para admin"""
        mock_session.get.side_effect = lambda key, default=None: {
            'is_admin': True,
            'is_ti': False,
            'user_id': 1,
            'username': 'admin'
        }.get(key, default)

        permissions = PermissionManager.get_user_permissions()

        assert permissions['is_admin'] is True
        assert permissions['is_ti'] is False
        assert permissions['user_id'] == 1
        assert permissions['can_view_all'] is True
        assert permissions['can_edit_all'] is True

    @patch('app.services.permission_manager.session')
    def test_get_user_permissions_regular_user(self, mock_session):
        """Testa obtenção de permissões para usuário comum"""
        mock_session.get.side_effect = lambda key, default=None: {
            'is_admin': False,
            'is_ti': False,
            'user_id': 2,
            'username': 'user'
        }.get(key, default)

        permissions = PermissionManager.get_user_permissions()

        assert permissions['is_admin'] is False
        assert permissions['is_ti'] is False
        assert permissions['user_id'] == 2
        assert permissions['can_view_all'] is False
        assert permissions['can_edit_all'] is False

    def test_dashboard_service_get_filtered_data_structure(self):
        """Testa se get_filtered_data retorna estrutura correta"""
        filters = {
            'task_status': '',
            'reminder_status': '',
            'chamado_status': '',
            'start_date': None,
            'end_date': None,
            'sector_id': None,
            'user_id': None,
        }

        permissions = {
            'is_admin': True,
            'is_ti': False,
            'user_id': 1,
            'can_view_all': True,
        }

        # Mock das queries para evitar acesso ao banco
        with patch('app.services.dashboard_service.db.session.query') as mock_query:
            # Mock das estatísticas
            mock_stats_result = Mock()
            mock_stats_result.total = 10
            mock_stats_result.done = 5
            mock_stats_result.pending = 3
            mock_stats_result.expired = 2

            mock_query.return_value.select_from.return_value.first.return_value = mock_stats_result

            # Mock dos setores
            with patch('app.services.dashboard_service.Sector.query') as mock_sector_query:
                mock_sector = Mock()
                mock_sector.id = 1
                mock_sector.name = 'TI'
                mock_sector_query.order_by.return_value.all.return_value = [mock_sector]

                # Mock dos tutoriais
                with patch('app.services.dashboard_service.Tutorial.query') as mock_tutorial_query:
                    mock_tutorial = Mock()
                    mock_tutorial.id = 1
                    mock_tutorial.titulo = 'Tutorial 1'
                    mock_tutorial_query.all.return_value = [mock_tutorial]

                    # Mock das visualizações
                    with patch('app.services.dashboard_service.VisualizacaoTutorial.query') as mock_vis_query:
                        mock_vis = Mock()
                        mock_vis.tutorial_id = 1
                        mock_vis_query.all.return_value = [mock_vis]

                        # Mock dos feedbacks
                        with patch('app.services.dashboard_service.FeedbackTutorial.query') as mock_feedback_query:
                            mock_feedback = Mock()
                            mock_feedback.util = True
                            mock_feedback.tutorial_id = 1
                            mock_feedback_query.all.return_value = [mock_feedback]

                            # Executa o teste
                            result = DashboardService.get_filtered_data(filters, permissions)

                            # Verifica estrutura do resultado
                            assert 'stats' in result
                            assert 'chart_data' in result
                            assert 'sla_data' in result
                            assert 'filters' in result
                            assert 'permissions' in result

                            # Verifica estrutura das estatísticas
                            assert 'tasks' in result['stats']
                            assert 'reminders' in result['stats']
                            assert 'chamados' in result['stats']
                            assert 'equipamentos' in result['stats']

                            # Verifica estrutura dos gráficos
                            assert 'evolution' in result['chart_data']
                            assert 'sectors' in result['chart_data']
                            assert 'tutorials' in result['chart_data']

    def test_dashboard_service_filters_application(self):
        """Testa se os filtros são aplicados corretamente"""
        filters = {
            'task_status': 'done',
            'reminder_status': 'pending',
            'chamado_status': 'Aberto',
            'start_date': date.today(),
            'end_date': date.today(),
            'sector_id': 1,
            'user_id': 1,
        }

        permissions = {
            'is_admin': True,
            'is_ti': False,
            'user_id': 1,
            'can_view_all': True,
        }

        # Este teste verifica se os métodos de aplicação de filtros existem
        # Uma implementação completa exigiria mocks mais complexos
        assert hasattr(DashboardService, '_apply_task_filters')
        assert hasattr(DashboardService, '_apply_reminder_filters')
        assert hasattr(DashboardService, '_apply_chamado_filters')
        assert hasattr(DashboardService, '_apply_date_filters')

    def test_permission_manager_methods_exist(self):
        """Testa se os métodos principais do PermissionManager existem"""
        assert hasattr(PermissionManager, 'get_user_permissions')
        assert hasattr(PermissionManager, 'get_user_sector')
        assert hasattr(PermissionManager, 'can_user_access_task')
        assert hasattr(PermissionManager, 'can_user_access_reminder')
        assert hasattr(PermissionManager, 'can_user_access_chamado')
        assert hasattr(PermissionManager, 'can_user_edit_task')
        assert hasattr(PermissionManager, 'can_user_manage_users')
        assert hasattr(PermissionManager, 'can_user_view_sla')