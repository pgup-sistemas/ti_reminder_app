"""
Testes unitários para o AnalyticsService
"""
import pytest
from datetime import datetime, timedelta, date
from app.services.analytics.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Testes do serviço de analytics"""
    
    def test_get_dashboard_kpis(self, app):
        """Testa KPIs do dashboard"""
        with app.app_context():
            kpis = AnalyticsService.get_dashboard_kpis()
            
            # Verificar estrutura de retorno
            assert isinstance(kpis, dict)
            assert 'chamados_abertos' in kpis
            assert 'chamados_mes' in kpis
            assert 'variacao_percentual' in kpis
            assert 'sla_taxa' in kpis
            assert 'satisfacao_media' in kpis
            assert 'lembretes_ativos' in kpis
            assert 'lembretes_vencidos' in kpis
            assert 'equipamentos_uso' in kpis
            
            # Verificar tipos
            assert isinstance(kpis['chamados_abertos'], int)
            assert isinstance(kpis['sla_taxa'], (int, float))
    
    def test_get_chamados_por_periodo(self, app):
        """Testa busca de chamados por período"""
        with app.app_context():
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            result = AnalyticsService.get_chamados_por_periodo(
                start_date, end_date, group_by='day'
            )
            
            # Verificar estrutura
            assert isinstance(result, list)
            if result:
                assert 'periodo' in result[0]
                assert 'total' in result[0]
    
    def test_get_sla_compliance(self, app):
        """Testa cálculo de SLA"""
        with app.app_context():
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            result = AnalyticsService.get_sla_compliance(start_date, end_date)
            
            # Verificar estrutura
            assert isinstance(result, dict)
            assert 'total' in result
            assert 'cumpridos' in result
            assert 'nao_cumpridos' in result
            assert 'taxa' in result
            
            # Verificar lógica
            assert result['total'] == result['cumpridos'] + result['nao_cumpridos']
            assert 0 <= result['taxa'] <= 100
    
    def test_get_performance_por_tecnico(self, app):
        """Testa performance por técnico"""
        with app.app_context():
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            result = AnalyticsService.get_performance_por_tecnico(start_date, end_date)
            
            # Verificar estrutura
            assert isinstance(result, list)
            if result:
                tecnico = result[0]
                assert 'tecnico' in tecnico
                assert 'total' in tecnico
                assert 'tempo_medio' in tecnico
                assert 'sla_taxa' in tecnico
    
    def test_get_chamados_por_prioridade(self, app):
        """Testa distribuição por prioridade"""
        with app.app_context():
            result = AnalyticsService.get_chamados_por_prioridade()
            
            assert isinstance(result, list)
            if result:
                assert 'prioridade' in result[0]
                assert 'total' in result[0]
    
    def test_get_chamados_por_setor(self, app):
        """Testa distribuição por setor"""
        with app.app_context():
            result = AnalyticsService.get_chamados_por_setor()
            
            assert isinstance(result, list)
            if result:
                assert 'setor' in result[0]
                assert 'total' in result[0]
    
    def test_get_tempo_medio_resolucao(self, app):
        """Testa cálculo de tempo médio"""
        from decimal import Decimal
        
        with app.app_context():
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            result = AnalyticsService.get_tempo_medio_resolucao(start_date, end_date)
            
            # Aceita int, float ou Decimal (retorno do PostgreSQL)
            assert isinstance(result, (int, float, Decimal))
            assert float(result) >= 0
    
    def test_get_satisfacao_mensal(self, app):
        """Testa evolução da satisfação"""
        with app.app_context():
            result = AnalyticsService.get_satisfacao_mensal(meses=6)
            
            assert isinstance(result, list)
            if result:
                assert 'mes' in result[0]
                assert 'media' in result[0]
                assert 1 <= result[0]['media'] <= 5
