import io
import pytest


from utils import get_openai_api_key, MISSING_OPENAI_KEY_MSG


def test_get_openai_api_key_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert get_openai_api_key() == "test-key"


def test_get_openai_api_key_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(EnvironmentError) as exc:
        get_openai_api_key()
    assert MISSING_OPENAI_KEY_MSG in str(exc.value)


def test_chat_endpoint_requires_key(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post("/api/chat", data={"message": "hello", "conversation_id": "temp"})
    assert response.status_code == 500


def test_upload_images_requires_key(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    files = {"images": ("test.jpg", io.BytesIO(b"data"), "image/jpeg")}
    response = client.post("/api/upload_images", files=files, data={"conversation_id": "temp"})
    assert response.status_code == 500
