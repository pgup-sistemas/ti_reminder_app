"""
Testes de integração para as rotas de Analytics API
"""
import pytest
from datetime import date, timedelta


class TestAnalyticsAPIEndpoints:
    """Testes das rotas da API de Analytics"""
    
    def test_dashboard_kpis_sem_autenticacao(self, client):
        """Testa acesso sem autenticação"""
        response = client.get('/api/analytics/dashboard-kpis', follow_redirects=False)
        # Pode ser 302 (redirect) ou 401 (unauthorized)
        assert response.status_code in [302, 401]
    
    def test_dashboard_kpis_endpoint_exists(self, client):
        """Testa se endpoint existe"""
        response = client.get('/api/analytics/dashboard-kpis')
        # Deve redirecionar ou retornar erro de autenticação, não 404
        assert response.status_code != 404
    
    def test_chamados_periodo_endpoint_exists(self, client):
        """Testa se endpoint de período existe"""
        response = client.get('/api/analytics/chamados-periodo')
        assert response.status_code != 404
    
    def test_chamados_prioridade_endpoint_exists(self, client):
        """Testa se endpoint de prioridade existe"""
        response = client.get('/api/analytics/chamados-prioridade')
        assert response.status_code != 404
    
    def test_performance_tecnico_endpoint_exists(self, client):
        """Testa se endpoint de performance existe"""
        response = client.get('/api/analytics/performance-tecnico')
        assert response.status_code != 404
    
    def test_chamados_setor_endpoint_exists(self, client):
        """Testa se endpoint de setor existe"""
        response = client.get('/api/analytics/chamados-setor')
        assert response.status_code != 404
    
    def test_analytics_page_endpoint_exists(self, client):
        """Testa se página analytics existe"""
        response = client.get('/analytics')
        assert response.status_code != 404
    
    def test_all_analytics_routes_registered(self, client):
        """Testa se todas as rotas analytics foram registradas"""
        routes = [
            '/api/analytics/dashboard-kpis',
            '/api/analytics/chamados-periodo',
            '/api/analytics/chamados-prioridade',
            '/api/analytics/performance-tecnico',
            '/api/analytics/chamados-setor',
            '/analytics'
        ]
        
        for route in routes:
            response = client.get(route)
            # Nenhuma deve retornar 404 (Not Found)
            # Pode ser 302 (redirect), 401/403 (auth), ou 200 (ok)
            assert response.status_code != 404, f"Rota {route} não encontrada"
