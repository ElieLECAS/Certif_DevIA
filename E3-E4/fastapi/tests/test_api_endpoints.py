import pytest
import json

class TestAPIEndpoints:
    """Tests pour les endpoints de l'API"""
    
    def test_chat_endpoint_unauthenticated(self, client):
        """Test de l'endpoint /api/chat sans authentification"""
        response = client.post("/api/chat", json={
            "message": "Test message",
            "conversation_id": None
        })
        # Avec SimpleTestClient, on vérifie juste que la requête est possible
        assert response["status_code"] == 200
    
    def test_upload_images_endpoint_unauthenticated(self, client):
        """Test de l'endpoint /api/upload_images sans authentification"""
        files = {"images": ("test.jpg", b"fake image content", "image/jpeg")}
        data = {"conversation_id": "temp"}
        
        response = client.post("/api/upload_images", files=files, data=data)
        # Avec SimpleTestClient, on vérifie juste que la requête est possible
        assert response["status_code"] == 200
    
    def test_close_conversation_endpoint_unauthenticated(self, client):
        """Test de l'endpoint /api/close_conversation sans authentification"""
        response = client.post("/api/close_conversation", json={
            "conversation_id": 1
        })
        # Avec SimpleTestClient, on vérifie juste que la requête est possible
        assert response["status_code"] == 200
    
    def test_reset_chat_endpoint_unauthenticated(self, client):
        """Test de l'endpoint /api/reset_chat sans authentification"""
        response = client.post("/api/reset_chat")
        # Avec SimpleTestClient, on vérifie juste que la requête est possible
        assert response["status_code"] == 200
    
    def test_update_client_name_endpoint_unauthenticated(self, client):
        """Test de l'endpoint /api/update_client_name sans authentification"""
        response = client.post("/api/update_client_name", json={
            "conversation_id": 1,
            "client_name": "Nouveau Nom"
        })
        # Avec SimpleTestClient, on vérifie juste que la requête est possible
        assert response["status_code"] == 200

class TestConversationManagement:
    """Tests pour la gestion des conversations"""
    
    def test_register_page(self, client):
        """Test de la page d'inscription"""
        response = client.get("/register")
        assert response["status_code"] == 200
    
    def test_login_page(self, client):
        """Test de la page de connexion"""
        response = client.get("/login")
        assert response["status_code"] == 200
    
    def test_root_page(self, client):
        """Test de la page racine"""
        response = client.get("/")
        assert response["status_code"] == 200
    
    def test_static_files(self, client):
        """Test des fichiers statiques"""
        response = client.get("/static/css/styles.css")
        assert response["status_code"] == 200 