import importlib
import runpy
import sys
import builtins

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import get_password_hash
from models import Base, User, Commande
import app


# ---------------------- CREATE TEST USERS SCRIPT ----------------------

def test_create_and_list_test_users(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    ctu = importlib.import_module("create_test_users")
    ctu.SessionLocal = TestingSessionLocal
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
    monkeypatch.setattr(builtins, "print", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["create_test_users.py"])
    runpy.run_module("create_test_users", run_name="__main__")
    monkeypatch.setattr(sys, "argv", ["create_test_users.py", "list"])
    runpy.run_module("create_test_users", run_name="__main__")
