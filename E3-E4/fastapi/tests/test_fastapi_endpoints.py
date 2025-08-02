import io


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Connexion" in response.text


def test_register_page(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert "Inscription Client" in response.text


def test_post_login(client):
    response = client.post(
        "/login",
        data={"username": "tester", "password": "password"},
        allow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/conversations"


def test_post_register(client):
    response = client.post(
        "/register",
        data={"username": "newuser", "email": "new@ex.com", "password": "pass"},
        allow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"].startswith("/login")
    assert "message=" in response.headers["location"]


def test_logout(client):
    response = client.get("/logout", allow_redirects=False)
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
    response = client.get("/client_home", allow_redirects=False)
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
    response = client.get("/", allow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_test_db_endpoint(client):
    response = client.get("/test-db")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "message" in data
