import json
from pathlib import Path
from datetime import datetime
import fitz
import app  # Ensure app is imported before langchain_utils to avoid circular import
import langchain_utils


def test_get_conversation_history():
    history = [
        {"role": "user", "content": "Salut"},
        {"role": "assistant", "content": "Bonjour"},
    ]
    result = langchain_utils.get_conversation_history(history)
    assert result == "User: Salut\nAssistant: Bonjour"


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