import pytest


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/login", "Connexion"),
        ("/register", "Inscription Client"),
    ],
)
def test_page_routes(client, path, expected):
    response = client.get(path)
    assert response.status_code == 200
    assert expected in response.text


def test_post_login(client):
    response = client.post(
        "/login",
        data={"username": "tester", "password": "password"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_post_register(client):
    response = client.post(
        "/register",
        data={"username": "newuser", "email": "new@ex.com", "password": "pass"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"].startswith("/login")
    assert "message=" in response.headers["location"]


def test_logout(client):
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_conversations_page(client):
    response = client.get("/conversations")
    assert response.status_code == 200
    assert "Liste des conversations SAV" in response.text


def test_conversation_detail(client, conversation):
    response = client.get(f"/conversation/{conversation.id}")
    assert response.status_code == 200
    assert f"Conversation #{conversation.id}" in response.text


def test_client_home_page(client):
    response = client.get("/client_home", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/conversations"


def test_chat_page(client):
    response = client.get("/chat")
    assert response.status_code == 200
    assert "chat-layout" in response.text


def test_close_conversation_temp(client):
    response = client.post(
        "/api/close_conversation",
        data={"conversation_id": "temp"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Aucune conversation active \u00e0 cl\u00f4turer",
    }


def test_reset_chat(client):
    response = client.post("/api/reset_chat")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "conversation_id": "temp"}


def test_update_client_name(client, conversation):
    response = client.post(
        "/api/update_client_name",
        data={"conversation_id": str(conversation.id), "client_name": "Updated"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Nom du client mis \u00e0 jour avec succ\u00e8s",
    }


def test_root_redirect(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_test_db_endpoint(client):
    response = client.get("/test-db")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "message" in data


def test_chat_skips_reasking_identifiers(client, db, monkeypatch):
    import routes
    import langchain_openai
    from types import SimpleNamespace

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    contexts = []

    class DummyLLM:
        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, ctx):
            contexts.append(ctx)
            return SimpleNamespace(content="ok")

    class DummyVectorstore:
        def similarity_search(self, query, k=5):
            return []

    dummy_vs = DummyVectorstore()
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", DummyLLM)
    monkeypatch.setattr(routes, "get_vectorstore", lambda api_key: dummy_vs)

    # Premier message sans identifiants -> etape_1 présente
    resp1 = client.post("/api/chat", data={"message": "Bonjour", "conversation_id": "temp"})
    assert resp1.status_code == 200
    conv_id = str(resp1.json()["conversation_id"])
    assert "etape_1" in contexts[-1]

    # Fournir numéro de commande et position
    resp2 = client.post(
        "/api/chat",
        data={"message": "Ma commande CMD2024-001 position 2", "conversation_id": conv_id},
    )
    assert resp2.status_code == 200
    assert "etape_1" not in contexts[-1]

    from models import Conversation as ConvModel

    conv = db.query(ConvModel).filter_by(id=int(conv_id)).first()
    assert conv.numero_commande == "CMD2024-001"
    assert conv.position_chassis == "2"

    # Message suivant : etape_1 toujours absente
    resp3 = client.post(
        "/api/chat", data={"message": "merci", "conversation_id": conv_id}
    )
    assert resp3.status_code == 200
    assert "etape_1" not in contexts[-1]
