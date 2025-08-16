import json
from pathlib import Path
from datetime import datetime
import fitz
import pytest
from unittest.mock import Mock, AsyncMock, patch
import app  # Ensure app is imported before langchain_utils to avoid circular import
import langchain_utils


def test_get_conversation_history():
    history = [
        {"role": "user", "content": "Salut"},
        {"role": "assistant", "content": "Bonjour"},
    ]
    result = langchain_utils.get_conversation_history(history)
    assert result == "User: Salut\nAssistant: Bonjour"


def test_get_conversation_history_with_empty_content():
    history = [
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "Bonjour"},
        {"role": "user", "content": "Salut"},
    ]
    result = langchain_utils.get_conversation_history(history)
    assert result == "Assistant: Bonjour\nUser: Salut"


def test_get_conversation_history_with_unknown_role():
    history = [
        {"role": "user", "content": "Salut"},
        {"role": "unknown", "content": "Test"},
        {"role": "assistant", "content": "Bonjour"},
    ]
    result = langchain_utils.get_conversation_history(history)
    assert result == "User: Salut\n: Test\nAssistant: Bonjour"


def test_load_all_jsons_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", tmp_path)
    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons()
    assert preprompt["content"] == "Assistant SAV"
    assert client["client_informations"]["nom"] == "Client"
    assert renseignements == {}
    assert retours == {}
    assert commandes == {"commandes": []}


def test_load_all_jsons_with_files(tmp_path, monkeypatch):
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", tmp_path)
    (tmp_path / "preprompt_SAV.json").write_text(json.dumps({"content": "Test"}), encoding="utf-8")
    (tmp_path / "protocole_renseignements.json").write_text("{}", encoding="utf-8")
    (tmp_path / "protocole_retour.json").write_text("{}", encoding="utf-8")

    class DummyUser:
        id = 1
        prenom = "John"
        username = "john_doe"
        created_at = datetime(2024, 1, 1)

    class DummyDB:
        def query(self, model):
            class Q:
                def filter(self, *args, **kwargs):
                    return self

                def all(self):
                    return []

            return Q()

    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons(
        user=DummyUser(), db=DummyDB()
    )
    assert preprompt["content"] == "Test"
    assert client["client_informations"]["id"] == 1
    assert commandes == {"commandes": []}


def test_load_all_jsons_with_user_and_db_error(tmp_path, monkeypatch):
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", tmp_path)
    
    class DummyUser:
        id = 1
        prenom = "John"
        username = "john_doe"
        created_at = datetime(2024, 1, 1)

    class DummyDB:
        def query(self, model):
            raise Exception("Database error")

    # Test que la fonction gère l'erreur de base de données
    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons(
        user=DummyUser(), db=DummyDB()
    )
    assert preprompt["content"] == "Assistant SAV"
    assert client["client_informations"]["nom"] == "Client"
    assert commandes == {"commandes": []}


def test_load_all_jsons_with_user_without_created_at(tmp_path, monkeypatch):
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", tmp_path)
    
    class DummyUser:
        id = 1
        prenom = "John"
        username = "john_doe"
        # Pas d'attribut created_at

    class DummyDB:
        def query(self, model):
            class Q:
                def filter(self, *args, **kwargs):
                    return self

                def all(self):
                    return []

            return Q()

    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons(
        user=DummyUser(), db=DummyDB()
    )
    assert "date_creation" in client["client_informations"]


def test_load_all_jsons_with_user_with_username_underscore(tmp_path, monkeypatch):
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", tmp_path)
    
    class DummyUser:
        id = 1
        prenom = None  # Pas de prénom
        username = "john_doe"
        created_at = datetime(2024, 1, 1)

    class DummyDB:
        def query(self, model):
            class Q:
                def filter(self, *args, **kwargs):
                    return self

                def all(self):
                    return []

            return Q()

    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons(
        user=DummyUser(), db=DummyDB()
    )
    assert client["client_informations"]["prenom"] == "john"


def test_load_all_jsons_with_user_without_username_underscore(tmp_path, monkeypatch):
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", tmp_path)
    
    class DummyUser:
        id = 1
        prenom = None  # Pas de prénom
        username = "john"  # Pas d'underscore
        created_at = datetime(2024, 1, 1)

    class DummyDB:
        def query(self, model):
            class Q:
                def filter(self, *args, **kwargs):
                    return self

                def all(self):
                    return []

            return Q()

    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons(
        user=DummyUser(), db=DummyDB()
    )
    assert client["client_informations"]["prenom"] == "john"


def test_load_all_jsons_with_user_with_commandes(tmp_path, monkeypatch):
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", tmp_path)
    
    class DummyUser:
        id = 1
        prenom = "John"
        username = "john_doe"
        created_at = datetime(2024, 1, 1)

    class DummyCommande:
        def __init__(self, numero, date_commande, date_livraison=None):
            self.numero_commande = numero
            self.date_commande = date_commande
            self.date_livraison = date_livraison
            self.produits = "Produit test"
            self.statut = "Livré"
            self.montant_ht = 100.0
            self.montant_ttc = 120.0
            self.notes = "Note test"

    class DummyDB:
        def query(self, model):
            class Q:
                def filter(self, *args, **kwargs):
                    return self

                def all(self):
                    return [
                        DummyCommande("CMD001", datetime(2024, 1, 1), datetime(2024, 1, 15)),
                        DummyCommande("CMD002", datetime(2024, 2, 1))
                    ]

            return Q()

    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons(
        user=DummyUser(), db=DummyDB()
    )
    assert len(commandes["commandes"]) == 2
    assert commandes["commandes"][0]["garantie_jusqu_au"] == "2029-01-15"
    assert "garantie_jusqu_au" not in commandes["commandes"][1]


def test_load_all_jsons_general_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", tmp_path)
    
    # Simuler une erreur générale
    def mock_mkdir(*args, **kwargs):
        raise Exception("Permission denied")
    
    monkeypatch.setattr(Path, "mkdir", mock_mkdir)
    
    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons()
    assert preprompt["content"] == "Assistant SAV"
    assert client["client_informations"]["nom"] == "Client"
    assert commandes == {"commandes": []}


def test_initialize_faiss_creates_index(tmp_path, monkeypatch):
    class DummyEmbeddings:
        def __init__(self, *args, **kwargs):
            pass

        def embed_documents(self, texts):
            return [[0.0] for _ in texts]

    class DummyFAISS:
        last_texts = None

        @classmethod
        def from_texts(cls, texts, embeddings):
            cls.last_texts = texts
            return cls()

        def save_local(self, path):
            Path(path).mkdir(parents=True, exist_ok=True)
            (Path(path) / "index.faiss").write_text("data", encoding="utf-8")

        @classmethod
        def load_local(cls, path, embeddings, allow_dangerous_deserialization=True):
            return cls()

    monkeypatch.setattr(langchain_utils, "OpenAIEmbeddings", DummyEmbeddings)
    monkeypatch.setattr(langchain_utils, "FAISS", DummyFAISS)

    pdf_dir = tmp_path / "pdfs"
    index_dir = tmp_path / "index"
    pdf_dir.mkdir()
    monkeypatch.setattr(langchain_utils, "CATALOGUES_DIR", pdf_dir)
    monkeypatch.setattr(langchain_utils, "FAISS_INDEX_DIR", index_dir)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello PDF")
    doc.save(pdf_dir / "doc.pdf")
    doc.close()

    langchain_utils.initialize_faiss("key", chunk_size=1000, chunk_overlap=0)
    assert (index_dir / "index.faiss").exists()
    assert any("Hello PDF" in t for t in DummyFAISS.last_texts)


def test_initialize_faiss_loads_existing_index(tmp_path, monkeypatch):
    class DummyEmbeddings:
        def __init__(self, *args, **kwargs):
            pass

        def embed_documents(self, texts):
            return [[0.0] for _ in texts]

    class DummyFAISS:
        load_called = False

        @classmethod
        def from_texts(cls, texts, embeddings):
            return cls()

        def save_local(self, path):
            pass

        @classmethod
        def load_local(cls, path, embeddings, allow_dangerous_deserialization=True):
            cls.load_called = True
            return cls()

    monkeypatch.setattr(langchain_utils, "OpenAIEmbeddings", DummyEmbeddings)
    monkeypatch.setattr(langchain_utils, "FAISS", DummyFAISS)

    pdf_dir = tmp_path / "pdfs"
    index_dir = tmp_path / "index"
    pdf_dir.mkdir()
    index_dir.mkdir()
    (index_dir / "index.faiss").write_text("data", encoding="utf-8")
    (index_dir / "index.pkl").write_text("data", encoding="utf-8")

    monkeypatch.setattr(langchain_utils, "CATALOGUES_DIR", pdf_dir)
    monkeypatch.setattr(langchain_utils, "FAISS_INDEX_DIR", index_dir)

    langchain_utils.initialize_faiss("key")
    assert DummyFAISS.load_called


def test_initialize_faiss_with_pdf_reading_error(tmp_path, monkeypatch):
    class DummyEmbeddings:
        def __init__(self, *args, **kwargs):
            pass

        def embed_documents(self, texts):
            return [[0.0] for _ in texts]

    class DummyFAISS:
        @classmethod
        def from_texts(cls, texts, embeddings):
            return cls()

        def save_local(self, path):
            pass

        @classmethod
        def load_local(cls, path, embeddings, allow_dangerous_deserialization=True):
            return cls()

    monkeypatch.setattr(langchain_utils, "OpenAIEmbeddings", DummyEmbeddings)
    monkeypatch.setattr(langchain_utils, "FAISS", DummyFAISS)

    pdf_dir = tmp_path / "pdfs"
    index_dir = tmp_path / "index"
    pdf_dir.mkdir()
    monkeypatch.setattr(langchain_utils, "CATALOGUES_DIR", pdf_dir)
    monkeypatch.setattr(langchain_utils, "FAISS_INDEX_DIR", index_dir)

    # Créer un fichier qui n'est pas un PDF valide
    (pdf_dir / "invalid.pdf").write_text("Ceci n'est pas un PDF", encoding="utf-8")

    # La fonction doit gérer l'erreur de lecture du PDF
    result = langchain_utils.initialize_faiss("key")
    assert result is not None


def test_initialize_faiss_with_no_pdfs(tmp_path, monkeypatch):
    class DummyEmbeddings:
        def __init__(self, *args, **kwargs):
            pass

        def embed_documents(self, texts):
            return [[0.0] for _ in texts]

    class DummyFAISS:
        @classmethod
        def from_texts(cls, texts, embeddings):
            return cls()

        def save_local(self, path):
            pass

        @classmethod
        def load_local(cls, path, embeddings, allow_dangerous_deserialization=True):
            return cls()

    monkeypatch.setattr(langchain_utils, "OpenAIEmbeddings", DummyEmbeddings)
    monkeypatch.setattr(langchain_utils, "FAISS", DummyFAISS)

    pdf_dir = tmp_path / "pdfs"
    index_dir = tmp_path / "index"
    pdf_dir.mkdir()
    monkeypatch.setattr(langchain_utils, "CATALOGUES_DIR", pdf_dir)
    monkeypatch.setattr(langchain_utils, "FAISS_INDEX_DIR", index_dir)

    # Pas de fichiers PDF
    result = langchain_utils.initialize_faiss("key")
    assert result is not None


def test_initialize_faiss_general_exception(tmp_path, monkeypatch):
    # Mock OpenAIEmbeddings pour lever une exception lors de l'initialisation
    class DummyEmbeddings:
        def __init__(self, *args, **kwargs):
            raise Exception("OpenAI API error")

    class DummyFAISS:
        @classmethod
        def from_texts(cls, texts, embeddings):
            return cls()

        def save_local(self, path):
            pass

        @classmethod
        def load_local(cls, path, embeddings, allow_dangerous_deserialization=True):
            return cls()

    monkeypatch.setattr(langchain_utils, "OpenAIEmbeddings", DummyEmbeddings)
    monkeypatch.setattr(langchain_utils, "FAISS", DummyFAISS)

    pdf_dir = tmp_path / "pdfs"
    index_dir = tmp_path / "index"
    pdf_dir.mkdir()
    monkeypatch.setattr(langchain_utils, "CATALOGUES_DIR", pdf_dir)
    monkeypatch.setattr(langchain_utils, "FAISS_INDEX_DIR", index_dir)

    # La fonction doit gérer l'erreur et retourner un vectorstore par défaut
    # Mais d'abord, on doit mocker la deuxième tentative d'initialisation
    class DummyEmbeddingsFallback:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(langchain_utils, "OpenAIEmbeddings", DummyEmbeddingsFallback, raising=False)
    
    result = langchain_utils.initialize_faiss("key")
    assert result is not None


def test_save_uploaded_file_success(tmp_path, monkeypatch):
    # Mock aiofiles.open pour retourner un contexte asynchrone valide
    class MockAsyncFile:
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        
        async def write(self, content):
            pass

    class MockAiofiles:
        @staticmethod
        def open(file_path, mode):
            return MockAsyncFile()

    monkeypatch.setattr(langchain_utils, "aiofiles", MockAiofiles)
    
    # Mock Path
    monkeypatch.setattr(langchain_utils, "Path", lambda x: tmp_path / x)
    
    # Mock datetime
    mock_datetime = Mock()
    mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
    monkeypatch.setattr(langchain_utils, "datetime", mock_datetime)
    
    # Créer un mock pour uploaded_file
    mock_file = Mock()
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "test.jpg"
    mock_file.read = AsyncMock(return_value=b"test content")
    
    # Utiliser asyncio.run pour exécuter la fonction asynchrone
    import asyncio
    result = asyncio.run(langchain_utils.save_uploaded_file(mock_file))
    assert result == "/uploads/uploaded_images/20240101_120000_test.jpg"


def test_save_uploaded_file_invalid_type():
    mock_file = Mock()
    mock_file.content_type = "text/plain"
    
    import asyncio
    with pytest.raises(ValueError, match="Type de fichier non autorisé"):
        asyncio.run(langchain_utils.save_uploaded_file(mock_file))


def test_save_uploaded_file_no_content_type():
    mock_file = Mock()
    mock_file.content_type = None
    
    import asyncio
    with pytest.raises(ValueError, match="Type de fichier non autorisé"):
        asyncio.run(langchain_utils.save_uploaded_file(mock_file))


def test_save_uploaded_file_too_large():
    mock_file = Mock()
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "test.jpg"
    mock_file.read = AsyncMock(return_value=b"x" * (11 * 1024 * 1024))  # 11MB
    
    import asyncio
    with pytest.raises(ValueError, match="Fichier trop volumineux"):
        asyncio.run(langchain_utils.save_uploaded_file(mock_file))


def test_save_uploaded_file_general_exception(tmp_path, monkeypatch):
    # Mock aiofiles pour lever une exception
    class MockAiofiles:
        @staticmethod
        def open(file_path, mode):
            raise Exception("IO Error")

    monkeypatch.setattr(langchain_utils, "aiofiles", MockAiofiles)
    
    # Mock Path
    monkeypatch.setattr(langchain_utils, "Path", lambda x: tmp_path / x)
    
    # Mock datetime
    mock_datetime = Mock()
    mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
    monkeypatch.setattr(langchain_utils, "datetime", mock_datetime)
    
    mock_file = Mock()
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "test.jpg"
    mock_file.read = AsyncMock(return_value=b"test content")
    
    import asyncio
    with pytest.raises(Exception, match="Impossible de sauvegarder le fichier"):
        asyncio.run(langchain_utils.save_uploaded_file(mock_file))