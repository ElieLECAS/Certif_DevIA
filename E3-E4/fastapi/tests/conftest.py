import os
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set required environment variables
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "adminpass")

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from database import get_db
from models import Base, User, Conversation
from auth import get_current_active_user, get_password_hash

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

app.dependency_overrides[get_db] = override_get_db

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
def client(db, test_user):
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
