from pathlib import Path
import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from _pytest.monkeypatch import MonkeyPatch

# Ensure project root is on sys.path and as working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
ORIG_CWD = Path.cwd()
os.chdir(PROJECT_ROOT)

from models import Base, User, Conversation

_session_mp = MonkeyPatch()
_session_mp.setenv("SECRET_KEY", "test-secret")
_session_mp.setenv("DATABASE_URL", "sqlite://")
_session_mp.setenv("ADMIN_USERNAME", "admin")
_session_mp.setenv("ADMIN_EMAIL", "admin@example.com")
_session_mp.setenv("ADMIN_PASSWORD", "adminpass")


def pytest_sessionfinish(session, exitstatus):
    _session_mp.undo()
    os.chdir(ORIG_CWD)
@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "adminpass")

# In-memory SQLite database for tests
database_url = "sqlite://"
engine = create_engine(database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture()
def app(set_test_env):
    from database import get_db
    from app import app as fastapi_app

    fastapi_app.dependency_overrides[get_db] = override_get_db
    try:
        yield fastapi_app
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def test_user(db):
    from auth import get_password_hash

    user = User(
        username="tester",
        email="tester@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True,
        is_staff=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture()
def client(app, db, test_user):
    from auth import get_current_active_user

    def override_current_active_user():
        return test_user

    app.dependency_overrides[get_current_active_user] = override_current_active_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_active_user, None)

@pytest.fixture()
def conversation(db, test_user):
    conv = Conversation(client_name="Client", status="nouveau", user_id=test_user.id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv
