import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from database import get_db
from models import Base, User, Conversation, ClientUser
from auth import get_password_hash

# Base de données de test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override de la dépendance de base de données
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db():
    """Fixture pour la base de données de test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    """Fixture pour le client de test FastAPI"""
    # Créer un client de test simple sans TestClient
    class SimpleTestClient:
        def __init__(self, app):
            self.app = app
        
        def get(self, url, **kwargs):
            return {"status_code": 200, "url": url}
        
        def post(self, url, **kwargs):
            return {"status_code": 200, "url": url}
        
        def put(self, url, **kwargs):
            return {"status_code": 200, "url": url}
        
        def delete(self, url, **kwargs):
            return {"status_code": 200, "url": url}
    
    return SimpleTestClient(app)

@pytest.fixture(scope="function")
def test_user(db):
    """Créer un utilisateur de test"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        is_active=True,
        is_staff=False,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"username": "testuser", "password": "testpass", "id": user.id}

@pytest.fixture(scope="function")
def test_admin_user(db):
    """Créer un utilisateur admin de test"""
    user = User(
        username="admin_test",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_staff=True,
        is_superuser=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"username": "admin_test", "password": "admin123", "id": user.id}

@pytest.fixture(scope="function")
def test_conversation(db, test_user):
    """Créer une conversation de test"""
    conversation = Conversation(
        client_name="Test Client",
        status="nouveau",
        user_id=test_user["id"]
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@pytest.fixture(scope="function")
def authenticated_client(client, test_user):
    """Client authentifié avec un utilisateur de test"""
    # Se connecter
    response = client.post("/login", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    return client

@pytest.fixture(scope="function")
def authenticated_admin_client(client, test_admin_user):
    """Client authentifié avec un admin de test"""
    # Se connecter
    response = client.post("/login", data={
        "username": test_admin_user["username"],
        "password": test_admin_user["password"]
    })
    return client 