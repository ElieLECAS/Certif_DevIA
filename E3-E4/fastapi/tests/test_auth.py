import asyncio
import importlib.util
from datetime import timedelta, datetime

import pytest
from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

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
from models import ClientUser


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


# Additional auth edge cases


def test_access_token_expire_minutes_invalid(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "bad")
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
