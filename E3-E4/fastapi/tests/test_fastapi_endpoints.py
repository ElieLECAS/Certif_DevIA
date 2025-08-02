import io


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_register_page(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_post_login(client):
    response = client.post("/login", data={"username": "tester", "password": "password"}, allow_redirects=False)
    assert response.status_code == 302


def test_post_register(client):
    response = client.post(
        "/register",
        data={"username": "newuser", "email": "new@ex.com", "password": "pass"},
        allow_redirects=False,
    )
    assert response.status_code == 302


def test_logout(client):
    response = client.get("/logout", allow_redirects=False)
    assert response.status_code == 302


def test_conversations_page(client):
    response = client.get("/conversations")
    assert response.status_code == 200


def test_conversation_detail(client, conversation):
    response = client.get(f"/conversation/{conversation.id}")
    assert response.status_code == 200


def test_client_home_page(client):
    response = client.get("/client_home")
    assert response.status_code == 200


def test_chat_page(client):
    response = client.get("/chat")
    assert response.status_code == 200


def test_close_conversation_temp(client):
    response = client.post("/api/close_conversation", data={"conversation_id": "temp"})
    assert response.status_code == 200


def test_reset_chat(client):
    response = client.post("/api/reset_chat")
    assert response.status_code == 200


def test_update_client_name(client, conversation):
    response = client.post(
        "/api/update_client_name",
        data={"conversation_id": str(conversation.id), "client_name": "Updated"},
    )
    assert response.status_code == 200


def test_root_redirect(client):
    response = client.get("/", allow_redirects=False)
    assert response.status_code == 302


def test_test_db_endpoint(client):
    response = client.get("/test-db")
    assert response.status_code == 200
