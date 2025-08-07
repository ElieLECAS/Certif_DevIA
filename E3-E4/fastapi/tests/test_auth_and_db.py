import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User, Conversation, Message
from auth import get_password_hash, verify_password


class TestAuthentication:
    """Tests pour l'authentification."""
    
    def test_password_hashing(self):
        """Test que le hachage des mots de passe fonctionne."""
        password = "test_password"
        hashed = get_password_hash(password)
        
        # Vérifier que le hash est différent du mot de passe original
        assert hashed != password
        assert hashed.startswith("$2b$")
        
        # Vérifier que la vérification fonctionne
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)
    
    def test_login_success(self, client: TestClient, db: Session):
        """Test de connexion réussie."""
        # Créer un utilisateur de test
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Tenter la connexion
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "testpass"},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"
    
    def test_login_failure(self, client: TestClient, db: Session):
        """Test de connexion échouée."""
        # Créer un utilisateur de test
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Tenter la connexion avec un mauvais mot de passe
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "wrongpass"},
            follow_redirects=False
        )
        
        assert response.status_code == 200  # Retourne la page de login avec erreur
    
    def test_register_success(self, client: TestClient, db: Session):
        """Test d'inscription réussie."""
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "newpass123"
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert response.headers["location"].startswith("/login")
        
        # Vérifier que l'utilisateur a été créé en base
        user = db.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.email == "new@example.com"
        assert verify_password("newpass123", user.hashed_password)
    
    def test_register_duplicate_username(self, client: TestClient, db: Session):
        """Test d'inscription avec un nom d'utilisateur déjà existant."""
        # Créer un utilisateur existant
        user = User(
            username="existinguser",
            email="existing@example.com",
            hashed_password=get_password_hash("pass"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Tenter d'inscrire un utilisateur avec le même nom
        response = client.post(
            "/register",
            data={
                "username": "existinguser",
                "email": "new@example.com",
                "password": "newpass123"
            },
            follow_redirects=False
        )
        
        assert response.status_code == 200  # Retourne la page avec erreur
    
    def test_logout(self, client: TestClient):
        """Test de déconnexion."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"


class TestDatabaseOperations:
    """Tests pour les opérations de base de données."""
    
    def test_user_creation(self, db: Session):
        """Test de création d'utilisateur."""
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
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
    
    def test_conversation_creation(self, db: Session):
        """Test de création de conversation."""
        # Créer un utilisateur d'abord
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Créer une conversation
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        assert conversation.id is not None
        assert conversation.client_name == "Test Client"
        assert conversation.status == "active"
        assert conversation.user_id == user.id
    
    def test_message_creation(self, db: Session):
        """Test de création de message."""
        # Créer un utilisateur et une conversation
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Créer un message
        message = Message(
            content="Test message",
            role="user",
            conversation_id=conversation.id
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        assert message.id is not None
        assert message.content == "Test message"
        assert message.role == "user"
        assert message.conversation_id == conversation.id
    
    def test_conversation_relationships(self, db: Session):
        """Test des relations entre utilisateur, conversation et messages."""
        # Créer un utilisateur
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Créer une conversation
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Créer plusieurs messages
        messages = [
            Message(content="Message 1", role="user", conversation_id=conversation.id),
            Message(content="Message 2", role="assistant", conversation_id=conversation.id),
            Message(content="Message 3", role="user", conversation_id=conversation.id)
        ]
        
        for message in messages:
            db.add(message)
        db.commit()
        
        # Vérifier les relations
        user_conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
        assert len(user_conversations) == 1
        assert user_conversations[0].client_name == "Test Client"
        
        conversation_messages = db.query(Message).filter(Message.conversation_id == conversation.id).all()
        assert len(conversation_messages) == 3
    
    def test_user_deletion_cascade(self, db: Session):
        """Test que la suppression d'un utilisateur supprime ses conversations."""
        # Créer un utilisateur avec des conversations
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Supprimer l'utilisateur
        db.delete(user)
        db.commit()
        
        # Vérifier que la conversation a été supprimée
        remaining_conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
        assert len(remaining_conversations) == 0


class TestDatabaseConstraints:
    """Tests pour les contraintes de base de données."""
    
    def test_unique_username(self, db: Session):
        """Test que les noms d'utilisateur sont uniques."""
        user1 = User(
            username="testuser",
            email="test1@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user1)
        db.commit()
        
        # Tenter de créer un utilisateur avec le même nom
        user2 = User(
            username="testuser",
            email="test2@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user2)
        
        # Cela devrait lever une exception
        with pytest.raises(Exception):
            db.commit()
    
    def test_unique_email(self, db: Session):
        """Test que les emails sont uniques."""
        user1 = User(
            username="user1",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user1)
        db.commit()
        
        # Tenter de créer un utilisateur avec le même email
        user2 = User(
            username="user2",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user2)
        
        # Cela devrait lever une exception
        with pytest.raises(Exception):
            db.commit()
    
    def test_required_fields(self, db: Session):
        """Test que les champs requis sont présents."""
        # Tenter de créer un utilisateur sans nom d'utilisateur
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user)
        
        # Cela devrait lever une exception
        with pytest.raises(Exception):
            db.commit()


class TestDatabasePerformance:
    """Tests pour les performances de base de données."""
    
    def test_bulk_insert_performance(self, db: Session):
        """Test de performance pour l'insertion en masse."""
        import time
        
        # Créer plusieurs utilisateurs
        users = []
        for i in range(100):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                hashed_password=get_password_hash("testpass"),
                is_active=True
            )
            users.append(user)
        
        start_time = time.time()
        db.add_all(users)
        db.commit()
        end_time = time.time()
        
        # Vérifier que l'insertion est rapide
        assert (end_time - start_time) < 5.0  # Moins de 5 secondes
        
        # Vérifier que tous les utilisateurs ont été créés
        user_count = db.query(User).count()
        assert user_count >= 100
    
    def test_query_performance(self, db: Session):
        """Test de performance pour les requêtes."""
        # Créer des données de test
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        conversation = Conversation(
            client_name="Test Client",
            status="active",
            user_id=user.id
        )
        db.add(conversation)
        db.commit()
        
        # Créer plusieurs messages
        messages = []
        for i in range(50):
            message = Message(
                content=f"Message {i}",
                role="user" if i % 2 == 0 else "assistant",
                conversation_id=conversation.id
            )
            messages.append(message)
        
        db.add_all(messages)
        db.commit()
        
        # Test de performance pour les requêtes
        import time
        
        start_time = time.time()
        user_conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
        end_time = time.time()
        
        assert (end_time - start_time) < 1.0  # Moins d'1 seconde
        assert len(user_conversations) == 1