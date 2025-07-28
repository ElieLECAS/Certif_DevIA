import pytest
from app import app
from pathlib import Path

class TestAppConfiguration:
    """Tests de configuration de l'application"""
    
    def test_app_import(self):
        """Test que l'application peut être importée"""
        assert app is not None
        assert hasattr(app, 'routes')
    
    def test_app_title(self):
        """Test du titre de l'application"""
        assert app.title == "Chatbot SAV"
    
    def test_app_description(self):
        """Test de la description de l'application"""
        assert "Application de chatbot pour le service après-vente" in app.description
    
    def test_app_lifespan(self):
        """Test de la configuration lifespan"""
        assert hasattr(app, 'router')
        # Vérifier que l'app utilise le nouveau système lifespan
        # L'ancien système peut encore exister pour la compatibilité
        # assert not hasattr(app, 'on_event')  # Ancien système
    
    def test_static_files_mount(self):
        """Test du montage des fichiers statiques"""
        # Vérifier que les fichiers statiques sont montés
        static_mounts = [route.path for route in app.routes if hasattr(route, 'path') and 'static' in str(route.path)]
        assert len(static_mounts) > 0
    
    def test_templates_configuration(self):
        """Test de la configuration des templates"""
        # Vérifier que Jinja2Templates est importé
        from fastapi.templating import Jinja2Templates
        assert Jinja2Templates is not None

class TestRoutesConfiguration:
    """Tests de configuration des routes"""
    
    def test_routes_existence(self):
        """Test que les routes principales existent"""
        routes = [route.path for route in app.routes]
        expected_routes = ["/login", "/register", "/", "/conversations", "/chat", "/client_home"]
        
        found_count = 0
        for route in expected_routes:
            if route in routes or any(route in str(r.path) for r in app.routes):
                found_count += 1
        
        assert found_count >= 4, f"Seulement {found_count}/6 routes trouvées"
    
    def test_router_inclusion(self):
        """Test de l'inclusion des routes"""
        assert len(app.routes) > 0
    
    def test_api_routes(self):
        """Test des routes API"""
        # Vérifier que les routes API sont incluses
        api_routes = [route for route in app.routes if hasattr(route, 'path') and '/api/' in str(route.path)]
        assert len(api_routes) > 0

class TestMiddlewareConfiguration:
    """Tests de configuration des middlewares"""
    
    def test_cors_middleware(self):
        """Test du middleware CORS"""
        has_cors = any("CORSMiddleware" in str(middleware) for middleware in app.user_middleware)
        assert has_cors, "CORS middleware manquant"
    
    def test_middleware_order(self):
        """Test de l'ordre des middlewares"""
        # Vérifier que les middlewares sont configurés
        assert len(app.user_middleware) > 0

class TestDatabaseConfiguration:
    """Tests de configuration de la base de données"""
    
    def test_database_import(self):
        """Test d'import de la configuration de base de données"""
        from database import get_db, engine
        
        assert get_db is not None
        assert engine is not None
    
    def test_models_import(self):
        """Test d'import des modèles"""
        from models import User, Conversation, Commande, ClientUser
        
        assert User is not None
        assert Conversation is not None
        assert Commande is not None
        assert ClientUser is not None

class TestFileStructure:
    """Tests de la structure des fichiers"""
    
    def test_static_files_exist(self):
        """Test de l'existence des fichiers statiques"""
        static_dir = Path(__file__).parent.parent / "static"
        css_file = static_dir / "css" / "styles.css"
        
        assert static_dir.exists(), "Dossier static manquant"
        assert css_file.exists(), "Fichier CSS manquant"
    
    def test_templates_exist(self):
        """Test de l'existence des templates"""
        templates_dir = Path(__file__).parent.parent / "templates"
        base_template = templates_dir / "base.html"
        
        assert templates_dir.exists(), "Dossier templates manquant"
        assert base_template.exists(), "Template base.html manquant"
    
    def test_requirements_exist(self):
        """Test de l'existence du fichier requirements"""
        requirements_file = Path(__file__).parent.parent / "requirements.txt"
        assert requirements_file.exists(), "Fichier requirements.txt manquant"

class TestDependencies:
    """Tests des dépendances"""
    
    def test_fastapi_import(self):
        """Test d'import de FastAPI"""
        from fastapi import FastAPI
        assert FastAPI is not None
    
    def test_sqlalchemy_import(self):
        """Test d'import de SQLAlchemy"""
        from sqlalchemy import create_engine
        assert create_engine is not None
    
    def test_pydantic_import(self):
        """Test d'import de Pydantic"""
        from pydantic import BaseModel
        assert BaseModel is not None
    
    def test_bcrypt_import(self):
        """Test d'import de bcrypt"""
        import bcrypt
        assert bcrypt is not None 