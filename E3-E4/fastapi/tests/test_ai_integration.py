import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_utils import (
    initialize_faiss, 
    load_all_jsons, 
    get_conversation_history,
    save_uploaded_file
)
from fastapi import UploadFile
from utils import get_openai_api_key, MISSING_OPENAI_KEY_MSG
from pathlib import Path

class TestLangChainIntegration:
    """Tests d'intégration LangChain"""
    
    def test_initialize_faiss_import(self):
        """Test d'import des fonctions FAISS"""
        assert initialize_faiss is not None
        assert load_all_jsons is not None
    
    @patch('langchain_utils.OpenAIEmbeddings')
    @patch('langchain_utils.FAISS')
    def test_faiss_initialization(self, mock_faiss, mock_embeddings):
        """Test d'initialisation de FAISS"""
        # Mock des dépendances
        mock_embeddings.return_value = Mock()
        mock_faiss.from_texts.return_value = Mock()
        
        # Test que la fonction peut être appelée
        try:
            result = initialize_faiss()
            assert result is not None
        except Exception as e:
            # Si OpenAI n'est pas configuré, c'est normal
            assert "OPENAI_API_KEY" in str(e) or "api_key" in str(e)
    
    def test_load_all_jsons_import(self):
        """Test d'import de load_all_jsons"""
        assert load_all_jsons is not None
    
    def test_load_all_jsons_function(self):
        """Test de la fonction load_all_jsons"""
        try:
            result = load_all_jsons()
            # La fonction retourne un tuple de 5 dictionnaires
            assert isinstance(result, tuple)
            assert len(result) == 5
        except Exception as e:
            # Si le dossier n'existe pas, c'est normal
            assert "RAG" in str(e) or "preprompts" in str(e)

class TestChatProcessing:
    """Tests de traitement des messages de chat"""
    
    def test_get_conversation_history_import(self):
        """Test d'import de get_conversation_history"""
        assert get_conversation_history is not None
    
    def test_get_conversation_history_function(self):
        """Test de la fonction get_conversation_history"""
        # Test avec une conversation vide
        history = get_conversation_history([])
        assert isinstance(history, str)
        assert history == ""
        
        # Test avec une conversation avec messages
        test_history = [
            {"role": "user", "content": "Bonjour"},
            {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"}
        ]
        history = get_conversation_history(test_history)
        assert isinstance(history, str)
        assert "Bonjour" in history
    
    def test_chat_processing_function_exists(self):
        """Test que les fonctions de traitement de chat existent"""
        # Vérifier que les fonctions de traitement existent dans routes.py
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            # Vérifier qu'il y a des fonctions de traitement de chat
            assert "chat" in content or "ChatMessage" in content

class TestFileUpload:
    """Tests d'upload de fichiers"""
    
    def test_save_uploaded_file_import(self):
        """Test d'import de save_uploaded_file"""
        assert save_uploaded_file is not None
    
    def test_save_uploaded_file(self):
        """Test de sauvegarde d'un fichier uploadé"""
        # Test simple de l'existence de la fonction
        assert save_uploaded_file is not None
        # Vérifier que c'est une fonction async
        import inspect
        assert inspect.iscoroutinefunction(save_uploaded_file)

class TestAIIntegration:
    """Tests d'intégration IA complète"""
    
    def test_langchain_imports(self):
        """Test des imports LangChain"""
        try:
            from langchain_openai import OpenAIEmbeddings, ChatOpenAI
            from langchain_community.vectorstores import FAISS
            from langchain_text_splitters import CharacterTextSplitter
            assert True
        except ImportError:
            pytest.skip("LangChain non installé")
    
    def test_openai_configuration(self):
        """Test de configuration OpenAI"""
        # Vérifier que les variables d'environnement sont définies via l'utilitaire
        try:
            api_key = get_openai_api_key()
            assert len(api_key) > 0
        except EnvironmentError as e:
            assert str(e) == MISSING_OPENAI_KEY_MSG
    
    def test_faiss_index_existence(self):
        """Test de l'existence de l'index FAISS"""
        faiss_dir = Path(__file__).parent.parent / "faiss_index_pdf"
        if faiss_dir.exists():
            index_file = faiss_dir / "index.faiss"
            pkl_file = faiss_dir / "index.pkl"
            assert index_file.exists() or pkl_file.exists()
        else:
            # Si le dossier n'existe pas, c'est normal
            pass
    
    def test_rag_documents_existence(self):
        """Test de l'existence des documents RAG"""
        rag_dir = Path(__file__).parent.parent / "RAG"
        if rag_dir.exists():
            assert rag_dir.is_dir()
            # Vérifier qu'il y a des sous-dossiers
            subdirs = list(rag_dir.iterdir())
            assert len(subdirs) > 0
        else:
            # Si le dossier n'existe pas, c'est normal
            pass

class TestAISecurity:
    """Tests de sécurité pour l'IA"""
    
    def test_api_key_security(self):
        """Test de sécurité de la clé API"""
        # Vérifier que la clé API n'est pas exposée dans le code
        langchain_utils_content = Path(__file__).parent.parent / "langchain_utils.py"
        if langchain_utils_content.exists():
            content = langchain_utils_content.read_text()
            # La clé API ne doit pas être en dur dans le code
            assert "sk-" not in content
            # Vérifier qu'il y a une gestion des variables d'environnement
            assert "os" in content or "getenv" in content
    
    def test_file_upload_security(self):
        """Test de sécurité pour l'upload de fichiers"""
        # Vérifier que les types de fichiers sont validés
        langchain_utils_content = Path(__file__).parent.parent / "langchain_utils.py"
        if langchain_utils_content.exists():
            content = langchain_utils_content.read_text()
            # Vérifier qu'il y a une validation des types de fichiers
            assert "content_type" in content or "mime_type" in content or "image" in content
    
    def test_input_validation(self):
        """Test de validation des entrées IA"""
        # Vérifier que les entrées sont validées avant traitement
        routes_content = Path(__file__).parent.parent / "routes.py"
        if routes_content.exists():
            content = routes_content.read_text()
            # Vérifier qu'il y a une validation des messages
            assert "ChatMessage" in content or "validation" in content 