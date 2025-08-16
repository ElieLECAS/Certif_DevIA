import asyncio

import pytest
from fastapi import Request

import routes
from auth import get_password_hash
from models import User, ClientUser


# ---------------------- ROUTES UTILITIES ----------------------

def test_get_vectorstore(monkeypatch):
    calls = []
    def fake_init(key):
        calls.append(key)
        return "index"
    monkeypatch.setattr(routes, "initialize_faiss", fake_init)
    store1 = routes.get_vectorstore("k1")
    store2 = routes.get_vectorstore("k2")
    assert store1 == "index" and store2 == "index"
    assert calls == ["k1"]


def test_get_or_create_conversation(db, test_user):
    conv = routes.get_or_create_conversation(db, test_user, None, "Client")
    assert conv.client_name == "Client"
    conv2 = routes.get_or_create_conversation(db, test_user, str(conv.id), "Other")
    assert conv2.id == conv.id
    conv3 = routes.get_or_create_conversation(db, test_user, "abc", "New")
    assert conv3.client_name == "New"


def test_authroutes_login_invalid(db):
    auth_routes = routes.AuthRoutes()
    scope = {"type": "http", "query_string": b""}
    request = Request(scope)
    response = asyncio.run(auth_routes.login(request, username="x", password="y", db=db))
    assert response.status_code == 200


def test_authroutes_login_next_redirect(db, test_user, monkeypatch):
    auth_routes = routes.AuthRoutes()
    scope = {"type": "http", "query_string": b"next=/chat"}
    request = Request(scope)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "bad")
    response = asyncio.run(auth_routes.login(request, username=test_user.username, password="password", db=db))
    assert response.status_code == 302
    assert response.headers["location"] == "/chat"


def test_authroutes_login_client_redirect(db):
    auth_routes = routes.AuthRoutes()
    user = User(username="client", email="c@example.com", hashed_password=get_password_hash("pass"), is_active=True)
    db.add(user); db.commit(); db.refresh(user)
    db.add(ClientUser(user_id=user.id, is_client_only=True)); db.commit()
    scope = {"type": "http", "query_string": b""}
    request = Request(scope)
    response = asyncio.run(auth_routes.login(request, username="client", password="pass", db=db))
    assert response.headers["location"] == "/client_home"
