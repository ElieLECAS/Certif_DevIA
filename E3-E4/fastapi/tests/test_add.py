import asyncio
import importlib
import runpy
import sys
from datetime import timedelta, datetime

import asyncio
import pytest
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import (
    authenticate_user,
    create_access_token,
    get_client_user,
    get_current_active_user,
    get_current_user,
    get_password_hash,
    verify_password,
    is_client_only,
    is_staff_or_admin,
)
from models import Base, User, ClientUser, Conversation, Commande
from database import get_db

import app
import monitoring_utils as mu
import routes
from jose import jwt

openai_requests_total = app.openai_requests_total
openai_request_tokens = app.openai_request_tokens
openai_response_tokens = app.openai_response_tokens
faiss_search_results_count = app.faiss_search_results_count
chatbot_conversations_total = app.chatbot_conversations_total
chatbot_messages_total = app.chatbot_messages_total

monitor_openai_call = mu.monitor_openai_call
monitor_faiss_search = mu.monitor_faiss_search
track_conversation_status = mu.track_conversation_status
track_message_type = mu.track_message_type
OpenAIMonitor = mu.OpenAIMonitor
FAISSMonitor = mu.FAISSMonitor
get_monitoring_stats = mu.get_monitoring_stats


# ---------------------- AUTH TESTS ----------------------

def test_password_hash_and_verify():
    hashed = get_password_hash("secret")
    assert verify_password("secret", hashed)
    assert not verify_password("wrong", hashed)


def test_authenticate_user_and_helpers(db, test_user):
    assert authenticate_user(db, test_user.username, "password")
    assert not authenticate_user(db, "nouser", "password")
    assert not authenticate_user(db, test_user.username, "bad")

    # client profile for user
    profile = ClientUser(user_id=test_user.id, is_client_only=True)
    db.add(profile)
    db.commit()
    db.refresh(profile)

    assert get_client_user(db, test_user) == profile
    assert is_client_only(test_user, db)
    assert is_staff_or_admin(test_user)


def test_create_access_token_and_get_current_user(db, test_user):
    token = create_access_token({"sub": test_user.username}, expires_delta=timedelta(minutes=5))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    user = asyncio.run(get_current_user(request, db, credentials))
    assert user.username == test_user.username


def test_get_current_user_from_cookie(db, test_user):
    token = create_access_token({"sub": test_user.username}, expires_delta=timedelta(minutes=5))
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    request._cookies = {"access_token": token}
    user = asyncio.run(get_current_user(request, db, None))
    assert user.username == test_user.username


def test_get_current_active_user_inactive(db, test_user):
    test_user.is_active = False
    db.commit()
    with pytest.raises(HTTPException):
        asyncio.run(get_current_active_user(test_user))


# ---------------------- DATABASE TEST ----------------------

def test_get_db_closes_session():
    gen = get_db()
    db = next(gen)
    assert db.is_active
    gen.close()  # trigger finally block


# ---------------------- MONITORING UTILITIES ----------------------


def test_monitor_openai_call_success():
    class Result:
        class Usage:
            prompt_tokens = 2
            completion_tokens = 3
        usage = Usage()

    @monitor_openai_call(model="gpt-test", endpoint="chat/completions")
    async def dummy():
        return Result()

    base_total = openai_requests_total.labels(model="gpt-test", endpoint="chat/completions", status="success")._value.get()
    base_prompt = openai_request_tokens.labels(model="gpt-test", endpoint="chat/completions")._value.get()
    base_completion = openai_response_tokens.labels(model="gpt-test", endpoint="chat/completions")._value.get()

    res = asyncio.run(dummy())
    assert isinstance(res, Result)
    assert openai_requests_total.labels(model="gpt-test", endpoint="chat/completions", status="success")._value.get() == base_total + 1
    assert openai_request_tokens.labels(model="gpt-test", endpoint="chat/completions")._value.get() == base_prompt + 2
    assert openai_response_tokens.labels(model="gpt-test", endpoint="chat/completions")._value.get() == base_completion + 3


def test_monitor_openai_call_error():
    @monitor_openai_call(model="gpt-test", endpoint="chat/completions")
    async def dummy():
        raise ValueError("boom")

    base_err = openai_requests_total.labels(model="gpt-test", endpoint="chat/completions", status="error")._value.get()
    with pytest.raises(ValueError):
        asyncio.run(dummy())
    assert openai_requests_total.labels(model="gpt-test", endpoint="chat/completions", status="error")._value.get() == base_err + 1


def test_monitor_faiss_search_success():
    @monitor_faiss_search(operation="search")
    def dummy():
        return [1, 2, 3]

    base = faiss_search_results_count.labels(operation="search")._value.get()
    res = dummy()
    assert res == [1, 2, 3]
    assert faiss_search_results_count.labels(operation="search")._value.get() == base + 3


def test_monitor_faiss_search_error():
    @monitor_faiss_search(operation="search")
    def dummy():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        dummy()


def test_tracking_helpers():
    base_status = chatbot_conversations_total.labels(status="nouveau")._value.get()
    track_conversation_status("nouveau")
    assert chatbot_conversations_total.labels(status="nouveau")._value.get() == base_status + 1

    base_type = chatbot_messages_total.labels(type="user")._value.get()
    track_message_type("user")
    assert chatbot_messages_total.labels(type="user")._value.get() == base_type + 1


def test_openai_monitor_contexts():
    base = openai_requests_total.labels(model="gpt-4o-mini", endpoint="chat/completions", status="success")._value.get()
    with OpenAIMonitor(model="gpt-4o-mini"):
        pass
    assert openai_requests_total.labels(model="gpt-4o-mini", endpoint="chat/completions", status="success")._value.get() == base + 1

    base_err = openai_requests_total.labels(model="gpt-4o-mini", endpoint="chat/completions", status="error")._value.get()
    with pytest.raises(RuntimeError):
        with OpenAIMonitor(model="gpt-4o-mini"):
            raise RuntimeError("oops")
    assert openai_requests_total.labels(model="gpt-4o-mini", endpoint="chat/completions", status="error")._value.get() == base_err + 1


def test_faiss_monitor_contexts():
    with FAISSMonitor(operation="similarity_search"):
        pass
    with pytest.raises(ValueError):
        with FAISSMonitor(operation="similarity_search"):
            raise ValueError("bad")


def test_get_monitoring_stats():
    class Dummy:
        def __init__(self, value=0):
            self.value = value
        def sum(self):
            return self.value

    # Patch metrics to provide _value with sum()
    for metric in [openai_requests_total, faiss_search_results_count, chatbot_conversations_total, chatbot_messages_total]:
        metric._value = Dummy()

    stats = get_monitoring_stats()
    assert {"openai_requests_total", "faiss_searches_total", "chatbot_conversations_total", "chatbot_messages_total"} <= stats.keys()


# ---------------------- CREATE TEST USERS SCRIPT ----------------------


def test_create_and_list_test_users(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    ctu = importlib.import_module("create_test_users")
    ctu.SessionLocal = TestingSessionLocal
    import builtins
    monkeypatch.setattr(builtins, "print", lambda *args, **kwargs: None)

    # create admin for list_test_users roles coverage
    with TestingSessionLocal() as db:
        admin = User(
            username="admin", email="admin@example.com", hashed_password=get_password_hash("admin"),
            is_active=False, is_staff=True, is_superuser=True
        )
        db.add(admin)
        db.commit()

    # run twice to hit "exists" branches
    ctu.create_test_users()
    ctu.create_test_users()
    ctu.list_test_users()

    with TestingSessionLocal() as db:
        assert db.query(User).count() == 3
        assert db.query(Commande).count() == 4


# ---------------------- MODELS HELPERS ----------------------

def test_conversation_methods():
    conv = Conversation(client_name="Client")
    conv.add_message("user", "hello")
    conv.add_message("assistant", "hi", image_path="path.png")
    assert conv.history[0]["content"] == "hello"
    assert conv.history[1]["image_path"] == "path.png"
    assert conv.updated_at is None
    conv.set_status("en_cours")
    assert conv.status == "en_cours"
    assert isinstance(conv.updated_at, datetime)


def test_commande_repr():
    cmd = Commande(numero_commande="CMD1", user_id=1, montant_ht=10, montant_ttc=12)
    assert repr(cmd) == "<Commande CMD1>"


# Additional auth edge cases

def test_access_token_expire_minutes_invalid(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "bad")
    import importlib.util
    spec = importlib.util.find_spec("auth")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ACCESS_TOKEN_EXPIRE_MINUTES == 30


def test_create_access_token_default_expiry():
    token = create_access_token({"sub": "tester"})
    assert isinstance(token, str)


def test_get_current_user_missing_token(db):
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(request, db, None))


def test_get_current_user_invalid_username(db):
    token = create_access_token({"sub": "ghost"}, expires_delta=timedelta(minutes=5))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(request, db, credentials))


def test_get_current_user_bad_token(db):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token")
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(request, db, credentials))


def test_get_current_active_user_success(test_user):
    result = asyncio.run(get_current_active_user(test_user))
    assert result == test_user


def test_get_current_user_missing_sub(db):
    token = jwt.encode({"exp": datetime.utcnow() + timedelta(minutes=5)}, "test-secret", algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    with pytest.raises(HTTPException):
        asyncio.run(get_current_user(request, db, credentials))


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


def test_create_default_admin_function():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    with TestSession() as db:
        app.create_default_admin(db)
        app.create_default_admin(db)
        assert db.query(User).filter(User.username == "admin").first() is not None


def test_create_test_users_main(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    import create_test_users as ctu
    ctu.SessionLocal = TestSession
    import builtins
    monkeypatch.setattr(builtins, "print", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["create_test_users.py"])
    runpy.run_module("create_test_users", run_name="__main__")
    monkeypatch.setattr(sys, "argv", ["create_test_users.py", "list"])
    runpy.run_module("create_test_users", run_name="__main__")