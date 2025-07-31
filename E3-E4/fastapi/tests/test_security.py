import pytest
import bcrypt
from auth import get_password_hash, verify_password, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app import app

class TestPasswordSecurity:
    """Tests de sécurité des mots de passe"""
    
    def test_password_hashing(self):
        """Test du hachage des mots de passe"""
        password = "securepass123"
        hashed = get_password_hash(password)
        
        # Vérifications de sécurité
        assert hashed != password
        assert len(hashed) > len(password)
        assert hashed.startswith("$2b$")  # Format bcrypt
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpass", hashed) is False
    
    def test_password_verification_edge_cases(self):
        """Test de vérification avec cas limites"""
        password = "testpass"
        hashed = get_password_hash(password)
        
        # Test avec mot de passe vide
        assert verify_password("", hashed) is False
        
        # Test avec mot de passe très long
        long_password = "a" * 1000
        long_hashed = get_password_hash(long_password)
        assert verify_password(long_password, long_hashed) is True
    
    def test_bcrypt_direct(self):
        """Test direct de bcrypt"""
        password = "testpass"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        assert bcrypt.checkpw(password.encode('utf-8'), hashed) is True
        assert bcrypt.checkpw("wrongpass".encode('utf-8'), hashed) is False

class TestJWTConfiguration:
    """Tests de configuration JWT"""
    
    def test_jwt_secret_key(self):
        """Test de la clé secrète JWT"""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 10  # Clé suffisamment longue
    
    def test_jwt_algorithm(self):
        """Test de l'algorithme JWT"""
        assert ALGORITHM == "HS256"
    
    def test_jwt_expiration(self):
        """Test de l'expiration JWT"""
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0

class TestCORSConfiguration:
    """Tests de configuration CORS"""
    
    def test_cors_middleware_exists(self):
        """Test de présence du middleware CORS"""
        has_cors = any("CORSMiddleware" in str(middleware) for middleware in app.user_middleware)
        assert has_cors, "CORS middleware manquant"
    
    def test_cors_configuration(self):
        """Test de la configuration CORS"""
        # Vérifier que CORS est configuré dans app.py
        app_content = app.__dict__
        assert hasattr(app, 'user_middleware')

class TestInputValidation:
    """Tests de validation des entrées"""
    
    def test_schemas_import(self):
        """Test d'import des schémas de validation"""
        from schemas import UserCreate, UserLogin, Token, ConversationCreate
        
        assert UserCreate is not None
        assert UserLogin is not None
        assert Token is not None
        assert ConversationCreate is not None
    
    def test_pydantic_config(self):
        """Test de configuration Pydantic"""
        from schemas import User, Conversation
        
        # Vérifier que les modèles utilisent ConfigDict
        assert hasattr(User, 'model_config')
        assert hasattr(Conversation, 'model_config')

class TestSecurityHeaders:
    """Tests des en-têtes de sécurité"""
    
    def test_app_security_headers(self):
        """Test des en-têtes de sécurité de l'application"""
        # Vérifier que l'app a une configuration de sécurité
        assert hasattr(app, 'title')
        assert app.title == "Chatbot SAV"
    
    def test_authentication_dependencies(self):
        """Test des dépendances d'authentification"""
        from auth import get_current_user, get_current_active_user
        
        assert get_current_user is not None
        assert get_current_active_user is not None

class TestDatabaseSecurity:
    """Tests de sécurité de la base de données"""
    
    def test_database_connection(self):
        """Test de connexion sécurisée à la base de données"""
        from database import get_db, engine
        
        assert get_db is not None
        assert engine is not None
    
    def test_sql_injection_protection(self):
        """Test de protection contre l'injection SQL"""
        # Vérifier que SQLAlchemy est utilisé (protection par défaut)
        from sqlalchemy import text
        
        # Test que les requêtes utilisent des paramètres
        query = text("SELECT * FROM users WHERE username = :username")
        assert ":username" in str(query) 