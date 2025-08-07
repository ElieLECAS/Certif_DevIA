import pytest
import re
from fastapi.testclient import TestClient


class TestMetrics:
    """Tests pour les métriques Prometheus."""
    
    def test_metrics_endpoint_exists(self, client: TestClient):
        """Test que l'endpoint /metrics existe et retourne des données."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
        
        # Vérifier que le contenu contient des métriques Prometheus
        content = response.text
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content
        assert "http_requests_in_flight" in content
        assert "http_errors_total" in content
    
    def test_metrics_format(self, client: TestClient):
        """Test que les métriques sont au format Prometheus correct."""
        response = client.get("/metrics")
        content = response.text
        
        # Vérifier le format des métriques
        lines = content.split('\n')
        metric_lines = [line for line in lines if line and not line.startswith('#')]
        
        for line in metric_lines:
            # Format: metric_name{label="value"} value
            assert re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*\{[^}]*\}[^#]*$', line) or \
                   re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*\s+[0-9.]+$', line)
    
    def test_request_metrics_increment(self, client: TestClient):
        """Test que les métriques de requêtes s'incrémentent correctement."""
        # Faire une requête
        response = client.get("/login")
        assert response.status_code == 200
        
        # Vérifier que les métriques ont été mises à jour
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        # Chercher la métrique pour cette requête
        assert 'http_requests_total{method="GET",endpoint="/login",status="200"}' in content
    
    def test_error_metrics(self, client: TestClient):
        """Test que les métriques d'erreur sont collectées."""
        # Faire une requête qui va échouer
        response = client.get("/nonexistent_endpoint")
        assert response.status_code == 404
        
        # Vérifier que l'erreur est enregistrée
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        # Chercher la métrique d'erreur
        assert 'http_errors_total{method="GET",endpoint="/nonexistent_endpoint",status="404",error_type="client_error"}' in content
    
    def test_duration_metrics(self, client: TestClient):
        """Test que les métriques de durée sont collectées."""
        # Faire une requête
        response = client.get("/login")
        assert response.status_code == 200
        
        # Vérifier que la métrique de durée existe
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        # Chercher la métrique de durée
        assert 'http_request_duration_seconds{method="GET",endpoint="/login"}' in content
    
    def test_in_flight_metrics(self, client: TestClient):
        """Test que les métriques de requêtes en cours fonctionnent."""
        # Vérifier que la métrique existe
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        # Chercher la métrique de requêtes en cours
        assert 'http_requests_in_flight' in content


class TestMetricsMiddleware:
    """Tests pour le middleware de collecte des métriques."""
    
    def test_middleware_collects_metrics(self, client: TestClient):
        """Test que le middleware collecte les métriques pour toutes les requêtes."""
        endpoints = ["/login", "/register", "/conversations", "/chat"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Peu importe le statut, les métriques doivent être collectées
        
        # Vérifier que toutes les métriques sont présentes
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        for endpoint in endpoints:
            assert f'endpoint="{endpoint}"' in content
    
    def test_middleware_handles_exceptions(self, client: TestClient):
        """Test que le middleware gère correctement les exceptions."""
        # Faire une requête qui pourrait causer une exception
        response = client.get("/nonexistent_endpoint")
        assert response.status_code == 404
        
        # Vérifier que les métriques d'erreur sont collectées
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        assert 'http_errors_total' in content


class TestMetricsLabels:
    """Tests pour les labels des métriques."""
    
    def test_method_labels(self, client: TestClient):
        """Test que les labels de méthode HTTP sont corrects."""
        methods = ["GET", "POST"]
        endpoints = ["/login", "/register"]
        
        for method in methods:
            for endpoint in endpoints:
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, data={})
                
                # Vérifier que la métrique a le bon label de méthode
                metrics_response = client.get("/metrics")
                content = metrics_response.text
                
                assert f'method="{method}"' in content
    
    def test_status_labels(self, client: TestClient):
        """Test que les labels de statut HTTP sont corrects."""
        # Faire des requêtes avec différents statuts
        client.get("/login")  # 200
        client.get("/nonexistent")  # 404
        
        # Vérifier que les labels de statut sont corrects
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        assert 'status="200"' in content
        assert 'status="404"' in content
    
    def test_endpoint_labels(self, client: TestClient):
        """Test que les labels d'endpoint sont corrects."""
        endpoints = ["/login", "/register", "/conversations", "/chat"]
        
        for endpoint in endpoints:
            client.get(endpoint)
        
        # Vérifier que tous les endpoints sont présents dans les métriques
        metrics_response = client.get("/metrics")
        content = metrics_response.text
        
        for endpoint in endpoints:
            assert f'endpoint="{endpoint}"' in content


class TestMetricsPerformance:
    """Tests pour les performances des métriques."""
    
    def test_metrics_response_time(self, client: TestClient):
        """Test que l'endpoint /metrics répond rapidement."""
        import time
        
        start_time = time.time()
        response = client.get("/metrics")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Moins d'1 seconde
    
    def test_metrics_memory_usage(self, client: TestClient):
        """Test que les métriques n'utilisent pas trop de mémoire."""
        # Faire plusieurs requêtes pour générer des métriques
        for i in range(10):
            client.get(f"/login?test={i}")
        
        # Vérifier que l'endpoint /metrics fonctionne toujours
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Vérifier que la taille de la réponse est raisonnable
        content_length = len(response.content)
        assert content_length < 100000  # Moins de 100KB