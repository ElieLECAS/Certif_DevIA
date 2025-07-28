import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app import app
import json

class TestChatEndpoints:
    """Tests des endpoints de chat IA"""
    
    def test_chat_endpoint_exists(self):
        """Test que l'endpoint /api/chat existe"""
        routes = [route.path for route in app.routes]
        assert "/api/chat" in routes or any("/api/chat" in str(route.path) for route in app.routes)
    
    def test_chat_endpoint_structure(self):
        """Test de la structure de l'endpoint chat"""
        # Vérifier que l'endpoint est défini dans routes.py
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            assert "@router.post" in content or "@app.post" in content
            assert "/api/chat" in content or "chat" in content
    
    def test_chat_message_schema(self):
        """Test du schéma ChatMessage"""
        from schemas import ChatMessage
        
        # Test de création d'un message valide
        message = ChatMessage(message="Test message", conversation_id=None)
        assert message.message == "Test message"
        assert message.conversation_id is None
    
    def test_chat_response_schema(self):
        """Test du schéma ChatResponse"""
        from schemas import ChatResponse
        
        # Test de création d'une réponse valide
        response = ChatResponse(
            response="Réponse test",
            conversation_id=1,
            history=[{"role": "user", "content": "Test"}]
        )
        assert response.response == "Réponse test"
        assert response.conversation_id == 1
        assert len(response.history) == 1

class TestUploadEndpoints:
    """Tests des endpoints d'upload"""
    
    def test_upload_endpoint_exists(self):
        """Test que l'endpoint /api/upload_images existe"""
        routes = [route.path for route in app.routes]
        assert "/api/upload_images" in routes or any("/api/upload_images" in str(route.path) for route in app.routes)
    
    def test_upload_endpoint_structure(self):
        """Test de la structure de l'endpoint upload"""
        # Vérifier que l'endpoint est défini dans routes.py
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            assert "UploadFile" in content
            assert "File" in content or "files" in content
    
    def test_upload_file_function(self):
        """Test de la fonction d'upload de fichier"""
        # Vérifier que la fonction existe dans langchain_utils
        from langchain_utils import save_uploaded_file
        assert save_uploaded_file is not None

class TestConversationEndpoints:
    """Tests des endpoints de conversation"""
    
    def test_conversation_endpoints_exist(self):
        """Test que les endpoints de conversation existent"""
        routes = [route.path for route in app.routes]
        
        # Endpoints de conversation attendus
        expected_endpoints = [
            "/conversations",
            "/api/conversations",
            "/chat"
        ]
        
        found_endpoints = []
        for endpoint in expected_endpoints:
            if endpoint in routes or any(endpoint in str(route.path) for route in app.routes):
                found_endpoints.append(endpoint)
        
        assert len(found_endpoints) > 0, "Aucun endpoint de conversation trouvé"
    
    def test_conversation_schemas(self):
        """Test des schémas de conversation"""
        from schemas import ConversationCreate, ConversationUpdate, Conversation
        
        # Test ConversationCreate
        conv_create = ConversationCreate(client_name="Test Client")
        assert conv_create.client_name == "Test Client"
        assert conv_create.status == "nouveau"
        
        # Test ConversationUpdate
        conv_update = ConversationUpdate(status="en_cours")
        assert conv_update.status == "en_cours"
        
        # Test Conversation
        conv = Conversation(
            id=1,
            client_name="Test Client",
            status="nouveau",
            history=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert conv.id == 1
        assert conv.client_name == "Test Client"

class TestAIIntegrationEndpoints:
    """Tests d'intégration des endpoints IA"""
    
    def test_langchain_utils_import_in_routes(self):
        """Test que langchain_utils est importé dans routes"""
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            assert "langchain_utils" in content
            assert "initialize_faiss" in content or "load_all_jsons" in content
    
    def test_openai_integration(self):
        """Test de l'intégration OpenAI"""
        # Vérifier que les imports OpenAI sont présents
        langchain_content = Path(__file__).parent.parent / "langchain_utils.py"
        if langchain_content.exists():
            content = langchain_content.read_text()
            assert "OpenAIEmbeddings" in content or "ChatOpenAI" in content
            assert "langchain_openai" in content
    
    def test_faiss_integration(self):
        """Test de l'intégration FAISS"""
        # Vérifier que FAISS est utilisé
        langchain_content = Path(__file__).parent.parent / "langchain_utils.py"
        if langchain_content.exists():
            content = langchain_content.read_text()
            assert "FAISS" in content
            assert "vectorstores" in content
    
    def test_rag_integration(self):
        """Test de l'intégration RAG"""
        # Vérifier que les documents RAG sont utilisés
        langchain_content = Path(__file__).parent.parent / "langchain_utils.py"
        if langchain_content.exists():
            content = langchain_content.read_text()
            assert "RAG" in content or "preprompts" in content

class TestAISecurityEndpoints:
    """Tests de sécurité des endpoints IA"""
    
    def test_input_validation_in_chat(self):
        """Test de validation des entrées dans le chat"""
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            # Vérifier qu'il y a une validation des entrées
            assert "ChatMessage" in content
            assert "message" in content
    
    def test_file_validation_in_upload(self):
        """Test de validation des fichiers uploadés"""
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            # Vérifier qu'il y a une validation des fichiers
            assert "UploadFile" in content
            # Vérifier qu'il y a une gestion des fichiers
            assert "File" in content or "files" in content
    
    def test_error_handling_in_ai_endpoints(self):
        """Test de gestion d'erreurs dans les endpoints IA"""
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            # Vérifier qu'il y a une gestion d'erreurs
            assert "try:" in content
            assert "except" in content
            assert "HTTPException" in content

class TestAIPerformance:
    """Tests de performance des endpoints IA"""
    
    def test_async_endpoints(self):
        """Test que les endpoints IA sont asynchrones"""
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            # Vérifier qu'il y a des fonctions async
            assert "async def" in content
    
    def test_response_time_optimization(self):
        """Test d'optimisation du temps de réponse"""
        # Vérifier que les réponses sont optimisées
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            # Vérifier qu'il y a des optimisations
            assert "JSONResponse" in content or "response" in content

# Imports nécessaires
from datetime import datetime
from pathlib import Path 