"""
Testes de integração para endpoints de Performance e RFID
"""
import pytest


class TestPerformanceEndpoints:
    """Testes para endpoints relacionados a performance"""

    def test_performance_dashboard_requires_auth(self, client):
        response = client.get("/performance/dashboard")
        assert response.status_code in [302, 401]

    def test_performance_dashboard_requires_admin_ti(self, user_authenticated_client):
        response = user_authenticated_client.get("/performance/dashboard")
        # Deve redirecionar por falta de permissão (403 convertido em redirect)
        assert response.status_code in [302, 403]

    def test_performance_dashboard_authorized(self, authenticated_client):
        response = authenticated_client.get("/performance/dashboard")
        assert response.status_code == 200

    def test_performance_metrics_api_requires_auth(self, client):
        response = client.get("/api/performance/metrics")
        assert response.status_code in [302, 401]

    def test_performance_metrics_api_requires_admin_ti(self, user_authenticated_client):
        response = user_authenticated_client.get("/api/performance/metrics")
        assert response.status_code == 403

    def test_performance_metrics_api_authorized(self, authenticated_client):
        response = authenticated_client.get("/api/performance/metrics")
        assert response.status_code == 200


class TestRFIDEndpoints:
    """Testes para endpoints relacionados a RFID"""

    def test_rfid_dashboard_requires_auth(self, client):
        response = client.get("/rfid/dashboard")
        assert response.status_code in [302, 401]

    def test_rfid_dashboard_requires_admin_ti(self, user_authenticated_client):
        response = user_authenticated_client.get("/rfid/dashboard")
        assert response.status_code in [302, 403]

    def test_rfid_dashboard_authorized(self, authenticated_client):
        response = authenticated_client.get("/rfid/dashboard")
        assert response.status_code == 200

    def test_rfid_status_api_requires_auth(self, client):
        response = client.get("/api/rfid/status")
        assert response.status_code in [302, 401]

    def test_rfid_status_api_requires_admin_ti(self, user_authenticated_client):
        response = user_authenticated_client.get("/api/rfid/status")
        assert response.status_code == 403

    def test_rfid_status_api_authorized(self, authenticated_client):
        response = authenticated_client.get("/api/rfid/status")
        assert response.status_code == 200

    def test_rfid_scan_requires_admin_ti(self, user_authenticated_client):
        response = user_authenticated_client.post("/rfid/scan", json={"rfid_tag": "123", "reader_id": "reader1"})
        assert response.status_code == 403

    def test_rfid_scan_authorized(self, authenticated_client):
        response = authenticated_client.post("/rfid/scan", json={"rfid_tag": "123", "reader_id": "reader1"})
        # Pode ser sucesso ou outro erro, mas não deve ser 403
        assert response.status_code != 403


class TestCertificationsEndpoints:
    """Testes para endpoints relacionados a certificações"""

    def test_certifications_dashboard_requires_auth(self, client):
        response = client.get("/certifications/dashboard")
        assert response.status_code in [302, 401]

    def test_certifications_dashboard_requires_admin_ti(self, user_authenticated_client):
        response = user_authenticated_client.get("/certifications/dashboard")
        assert response.status_code in [302, 403]

    def test_certifications_dashboard_authorized(self, authenticated_client):
        response = authenticated_client.get("/certifications/dashboard")
        assert response.status_code == 200

    def test_certifications_leaderboard_api_requires_admin_ti(self, user_authenticated_client):
        response = user_authenticated_client.get("/api/certifications/leaderboard")
        assert response.status_code == 403

    def test_certifications_leaderboard_api_authorized(self, authenticated_client):
        response = authenticated_client.get("/api/certifications/leaderboard")
        assert response.status_code == 200
