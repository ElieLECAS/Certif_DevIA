import json
import types
import sys
from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings

# Stub monitoring_utils to avoid circular imports during tests
stub = types.ModuleType("monitoring_utils")

def _noop_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

class _NoopContextManager:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

stub.monitor_faiss_search = _noop_decorator
stub.monitor_openai_call = _noop_decorator
stub.track_conversation_status = lambda *a, **k: None
stub.track_message_type = lambda *a, **k: None
stub.OpenAIMonitor = _NoopContextManager
stub.FAISSMonitor = _NoopContextManager
sys.modules["monitoring_utils"] = stub

import langchain_utils
import routes


class DummyEmbeddings(Embeddings):
    def __init__(self, *args, **kwargs):
        pass
    def embed_documents(self, texts):
        return [[float(i)] for i in range(len(texts))]

    def embed_query(self, text):
        return [0.0]


def create_pdf(path: Path, text: str) -> None:
    import fitz  # PyMuPDF

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_initialize_faiss_creates_index(tmp_path, monkeypatch):
    pdf_dir = tmp_path / "pdfs"
    index_dir = tmp_path / "index"
    pdf_dir.mkdir()

    create_pdf(pdf_dir / "test.pdf", "Bonjour FAISS")

    monkeypatch.setattr(langchain_utils, "OpenAIEmbeddings", DummyEmbeddings)
    monkeypatch.setattr(langchain_utils, "CATALOGUES_DIR", pdf_dir)
    monkeypatch.setattr(langchain_utils, "FAISS_INDEX_DIR", index_dir)

    vectorstore = langchain_utils.initialize_faiss("fake-key")

    assert (index_dir / "index.faiss").exists()
    results = vectorstore.similarity_search("Bonjour", k=1)
    assert results and "Bonjour FAISS" in results[0].page_content


def test_load_json_reads_file(tmp_path):
    data = {"x": 1}
    path = tmp_path / "file.json"
    path.write_text(json.dumps(data))
    assert langchain_utils.load_json(path) == data


def test_load_all_jsons_defaults_when_missing(tmp_path, monkeypatch):
    base = tmp_path / "preprompts"
    base.mkdir()
    monkeypatch.setattr(langchain_utils, "PREPROMPTS_DIR", base)

    preprompt, client, renseignements, retours, commandes = langchain_utils.load_all_jsons()

    assert "content" in preprompt
    assert isinstance(renseignements, dict) and isinstance(retours, dict)


def test_get_conversation_history_formats_messages():
    history = [
        {"role": "user", "content": "Salut"},
        {"role": "assistant", "content": "Bonjour"},
        {"role": "system", "content": "Regles"},
    ]
    text = langchain_utils.get_conversation_history(history)
    assert "User: Salut" in text
    assert "Assistant: Bonjour" in text
    assert "System: Regles" in text


def test_get_vectorstore_caches(monkeypatch):
    calls = []

    def fake_init(key):
        calls.append(key)
        return {"vs": True}

    monkeypatch.setattr(routes, "initialize_faiss", fake_init)
    monkeypatch.setattr(routes, "_vectorstore", None)

    vs1 = routes.get_vectorstore("k")
    vs2 = routes.get_vectorstore("k")

    assert vs1 is vs2
    assert calls == ["k"]
