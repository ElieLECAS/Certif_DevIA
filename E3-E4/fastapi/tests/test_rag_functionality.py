import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User, Conversation, Message
import json
import os


class TestRAGEndpoints:
    """Tests pour les endpoints RAG."""
    
    def test_chat_endpoint_exists(self, client: TestClient):
        """Test que l'endpoint /chat existe."""
        response = client.get("/chat")
        assert response.status_code == 200
        assert "chat-layout" in response.text
    
    def test_chat_api_endpoint(self, client: TestClient, db: Session):
        """Test de l'endpoint API de chat."""
        # Créer un utilisateur et une conversation
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Tester l'API de chat
        response = client.post(
            "/api/chat",
            json={
                "message": "Bonjour, j'ai un problème avec mon produit",
                "conversation_id": str(conversation.id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
    
    def test_chat_without_conversation(self, client: TestClient):
        """Test de chat sans conversation existante."""
        response = client.post(
            "/api/chat",
            json={
                "message": "Bonjour, j'ai un problème",
                "conversation_id": "temp"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
    
    def test_chat_with_invalid_conversation(self, client: TestClient):
        """Test de chat avec une conversation invalide."""
        response = client.post(
            "/api/chat",
            json={
                "message": "Test message",
                "conversation_id": "invalid_id"
            }
        )
        
        # Devrait retourner une erreur ou créer une nouvelle conversation
        assert response.status_code in [200, 400, 404]
    
    def test_chat_message_format(self, client: TestClient):
        """Test du format des messages de chat."""
        response = client.post(
            "/api/chat",
            json={
                "message": "Test message",
                "conversation_id": "temp"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure de la réponse
        required_fields = ["response", "conversation_id"]
        for field in required_fields:
            assert field in data
    
    def test_chat_with_empty_message(self, client: TestClient):
        """Test de chat avec un message vide."""
        response = client.post(
            "/api/chat",
            json={
                "message": "",
                "conversation_id": "temp"
            }
        )
        
        # Devrait retourner une erreur ou un message par défaut
        assert response.status_code in [200, 400]
    
    def test_chat_with_long_message(self, client: TestClient):
        """Test de chat avec un message très long."""
        long_message = "A" * 10000  # Message de 10k caractères
        
        response = client.post(
            "/api/chat",
            json={
                "message": long_message,
                "conversation_id": "temp"
            }
        )
        
        # Devrait gérer les messages longs
        assert response.status_code in [200, 400, 413]  # 413 = Payload Too Large


class TestConversationManagement:
    """Tests pour la gestion des conversations."""
    
    def test_close_conversation(self, client: TestClient, db: Session):
        """Test de fermeture de conversation."""
        # Créer un utilisateur et une conversation
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Fermer la conversation
        response = client.post(
            "/api/close_conversation",
            json={"conversation_id": str(conversation.id)}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Vérifier que la conversation est fermée en base
        db.refresh(conversation)
        assert conversation.status == "closed"
    
    def test_close_nonexistent_conversation(self, client: TestClient):
        """Test de fermeture d'une conversation inexistante."""
        response = client.post(
            "/api/close_conversation",
            json={"conversation_id": "nonexistent"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_reset_chat(self, client: TestClient):
        """Test de réinitialisation du chat."""
        response = client.post("/api/reset_chat")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "conversation_id" in data
    
    def test_update_client_name(self, client: TestClient, db: Session):
        """Test de mise à jour du nom du client."""
        # Créer un utilisateur et une conversation
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Old Name",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Mettre à jour le nom
        response = client.post(
            "/api/update_client_name",
            json={
                "conversation_id": str(conversation.id),
                "client_name": "New Name"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Vérifier que le nom a été mis à jour en base
        db.refresh(conversation)
        assert conversation.client_name == "New Name"


class TestRAGDatabaseOperations:
    """Tests pour les opérations de base de données liées au RAG."""
    
    def test_message_storage(self, client: TestClient, db: Session):
        """Test que les messages sont stockés en base de données."""
        # Créer un utilisateur et une conversation
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Envoyer un message
        client.post(
            "/api/chat",
            json={
                "message": "Test message",
                "conversation_id": str(conversation.id)
            }
        )
        
        # Vérifier que le message a été stocké
        messages = db.query(Message).filter(Message.conversation_id == conversation.id).all()
        assert len(messages) >= 1
        
        # Vérifier le contenu du message
        user_message = next((msg for msg in messages if msg.role == "user"), None)
        assert user_message is not None
        assert user_message.content == "Test message"
    
    def test_conversation_creation_from_chat(self, client: TestClient, db: Session):
        """Test que les conversations sont créées automatiquement lors du chat."""
        # Créer un utilisateur
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Envoyer un message avec conversation_id "temp"
        response = client.post(
            "/api/chat",
            json={
                "message": "Test message",
                "conversation_id": "temp"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier qu'une nouvelle conversation a été créée
        if "conversation_id" in data and data["conversation_id"] != "temp":
            conversation = db.query(Conversation).filter(
                Conversation.id == int(data["conversation_id"])
            ).first()
            assert conversation is not None
            assert conversation.status == "active"
    
    def test_message_ordering(self, client: TestClient, db: Session):
        """Test que les messages sont dans le bon ordre."""
        # Créer un utilisateur et une conversation
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Envoyer plusieurs messages
        messages = ["Message 1", "Message 2", "Message 3"]
        for message in messages:
            client.post(
                "/api/chat",
                json={
                    "message": message,
                    "conversation_id": str(conversation.id)
                }
            )
        
        # Vérifier l'ordre des messages
        db_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at).all()
        
        # Vérifier qu'il y a au moins les messages utilisateur
        user_messages = [msg for msg in db_messages if msg.role == "user"]
        assert len(user_messages) >= len(messages)
        
        # Vérifier l'ordre des messages utilisateur
        for i, message in enumerate(messages):
            if i < len(user_messages):
                assert user_messages[i].content == message


class TestRAGErrorHandling:
    """Tests pour la gestion d'erreurs dans le RAG."""
    
    def test_chat_with_malformed_json(self, client: TestClient):
        """Test de chat avec un JSON malformé."""
        response = client.post(
            "/api/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_chat_with_missing_fields(self, client: TestClient):
        """Test de chat avec des champs manquants."""
        response = client.post(
            "/api/chat",
            json={"message": "Test message"}
            # conversation_id manquant
        )
        
        assert response.status_code == 422
    
    def test_chat_with_invalid_field_types(self, client: TestClient):
        """Test de chat avec des types de champs invalides."""
        response = client.post(
            "/api/chat",
            json={
                "message": 123,  # Devrait être une string
                "conversation_id": "temp"
            }
        )
        
        assert response.status_code == 422
    
    def test_chat_rate_limiting(self, client: TestClient):
        """Test de limitation de débit pour le chat."""
        # Envoyer plusieurs messages rapidement
        for i in range(10):
            response = client.post(
                "/api/chat",
                json={
                    "message": f"Message {i}",
                    "conversation_id": "temp"
                }
            )
            
            # Tous les messages devraient être traités
            assert response.status_code in [200, 429]  # 429 = Too Many Requests


class TestRAGPerformance:
    """Tests pour les performances du RAG."""
    
    def test_chat_response_time(self, client: TestClient):
        """Test du temps de réponse du chat."""
        import time
        
        start_time = time.time()
        response = client.post(
            "/api/chat",
            json={
                "message": "Test message",
                "conversation_id": "temp"
            }
        )
        end_time = time.time()
        
        assert response.status_code == 200
        # Le temps de réponse devrait être raisonnable
        assert (end_time - start_time) < 30.0  # Moins de 30 secondes
    
    def test_chat_with_large_context(self, client: TestClient, db: Session):
        """Test de chat avec un contexte important."""
        # Créer un utilisateur et une conversation
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Créer beaucoup de messages pour avoir un contexte important
        for i in range(20):
            message = Message(
                content=f"Message {i} avec du contenu pour tester le contexte",
                role="user" if i % 2 == 0 else "assistant",
                conversation_id=conversation.id
            )
            db.add(message)
        db.commit()
        
        # Tester le chat avec ce contexte
        import time
        start_time = time.time()
        response = client.post(
            "/api/chat",
            json={
                "message": "Test avec contexte important",
                "conversation_id": str(conversation.id)
            }
        )
        end_time = time.time()
        
        assert response.status_code == 200
        # Le temps de réponse devrait rester raisonnable même avec beaucoup de contexte
        assert (end_time - start_time) < 60.0  # Moins de 60 secondes
    
    def test_concurrent_chat_requests(self, client: TestClient):
        """Test de requêtes de chat concurrentes."""
        import threading
        import time
        
        results = []
        errors = []
        
        def send_chat_request():
            try:
                response = client.post(
                    "/api/chat",
                    json={
                        "message": "Test concurrent",
                        "conversation_id": "temp"
                    }
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Lancer plusieurs requêtes simultanément
        threads = []
        for i in range(5):
            thread = threading.Thread(target=send_chat_request)
            threads.append(thread)
            thread.start()
        
        # Attendre que toutes les requêtes se terminent
        for thread in threads:
            thread.join()
        
        # Vérifier les résultats
        assert len(errors) == 0, f"Erreurs lors des requêtes concurrentes: {errors}"
        assert len(results) == 5
        assert all(status == 200 for status in results)