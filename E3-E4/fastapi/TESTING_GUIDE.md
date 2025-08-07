# 🧪 Guide de Tests FastAPI

Ce guide explique comment utiliser et exécuter les tests du projet FastAPI avec les métriques Prometheus et le monitoring Grafana.

## 📋 Table des Matières

1. [Types de Tests](#types-de-tests)
2. [Exécution des Tests](#exécution-des-tests)
3. [Tests de Métriques](#tests-de-métriques)
4. [Tests d'Authentification](#tests-dauthentification)
5. [Tests de Base de Données](#tests-de-base-de-données)
6. [Tests RAG](#tests-rag)
7. [Configuration](#configuration)
8. [Rapports](#rapports)
9. [Dépannage](#dépannage)

## 🎯 Types de Tests

### Tests Unitaires
- **Fichier**: `test_fastapi_endpoints.py`
- **Description**: Tests des endpoints FastAPI de base
- **Marqueur**: `@pytest.mark.unit`

### Tests de Métriques
- **Fichier**: `test_metrics.py`
- **Description**: Tests des métriques Prometheus
- **Marqueur**: `@pytest.mark.metrics`

### Tests d'Authentification
- **Fichier**: `test_auth_and_db.py`
- **Description**: Tests d'authentification et de base de données
- **Marqueur**: `@pytest.mark.auth`

### Tests RAG
- **Fichier**: `test_rag_functionality.py`
- **Description**: Tests des fonctionnalités RAG
- **Marqueur**: `@pytest.mark.rag`

## 🚀 Exécution des Tests

### Commande de Base
```bash
# Exécuter tous les tests
python -m pytest

# Exécuter avec verbosité
python -m pytest -v

# Exécuter avec couverture
python -m pytest --cov=. --cov-report=html
```

### Script Avancé
```bash
# Utiliser le script personnalisé
python run_all_tests.py

# Options disponibles
python run_all_tests.py --help

# Exécuter avec toutes les vérifications
python run_all_tests.py --all

# Exécuter avec couverture et rapports
python run_all_tests.py --coverage --html-report
```

### Tests par Catégorie
```bash
# Tests de métriques uniquement
python -m pytest -m metrics

# Tests d'authentification
python -m pytest -m auth

# Tests RAG
python -m pytest -m rag

# Tests de performance
python -m pytest -m performance

# Exclure les tests lents
python -m pytest -m "not slow"
```

## 📊 Tests de Métriques

### Métriques Testées

1. **Endpoint /metrics**
   - Vérification de l'existence
   - Format Prometheus correct
   - Contenu des métriques

2. **Métriques de Requêtes**
   - `http_requests_total`
   - `http_request_duration_seconds`
   - `http_requests_in_flight`

3. **Métriques d'Erreurs**
   - `http_errors_total`
   - Types d'erreurs (client, server, exception)

4. **Labels des Métriques**
   - Méthode HTTP (GET, POST, etc.)
   - Endpoint
   - Statut de réponse

### Exemple de Test
```python
def test_metrics_endpoint_exists(self, client: TestClient):
    """Test que l'endpoint /metrics existe et retourne des données."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
```

## 🔐 Tests d'Authentification

### Fonctionnalités Testées

1. **Hachage des Mots de Passe**
   - Vérification du hachage bcrypt
   - Validation des mots de passe

2. **Connexion**
   - Connexion réussie
   - Connexion échouée
   - Gestion des erreurs

3. **Inscription**
   - Création d'utilisateur
   - Validation des données
   - Gestion des doublons

4. **Base de Données**
   - Création d'utilisateurs
   - Création de conversations
   - Création de messages
   - Relations entre entités

### Exemple de Test
```python
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
```

## 🗄️ Tests de Base de Données

### Opérations Testées

1. **CRUD Utilisateurs**
   - Création, lecture, mise à jour, suppression
   - Contraintes d'unicité
   - Validation des champs

2. **CRUD Conversations**
   - Création et gestion des conversations
   - Relations avec les utilisateurs
   - Statuts des conversations

3. **CRUD Messages**
   - Création de messages
   - Ordre chronologique
   - Relations avec les conversations

4. **Performance**
   - Insertions en masse
   - Requêtes complexes
   - Temps de réponse

### Exemple de Test
```python
def test_conversation_creation(self, db: Session):
    """Test de création de conversation."""
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
    db.refresh(conversation)
    
    assert conversation.id is not None
    assert conversation.client_name == "Test Client"
    assert conversation.status == "active"
```

## 🤖 Tests RAG

### Fonctionnalités Testées

1. **Endpoints RAG**
   - `/chat` (interface)
   - `/api/chat` (API)
   - Gestion des conversations

2. **Gestion des Conversations**
   - Fermeture de conversations
   - Réinitialisation du chat
   - Mise à jour des noms de clients

3. **Opérations de Base de Données**
   - Stockage des messages
   - Création automatique de conversations
   - Ordre des messages

4. **Gestion d'Erreurs**
   - JSON malformé
   - Champs manquants
   - Types invalides

5. **Performance**
   - Temps de réponse
   - Contexte important
   - Requêtes concurrentes

### Exemple de Test
```python
def test_chat_api_endpoint(self, client: TestClient, db: Session):
    """Test de l'endpoint API de chat."""
    # Créer un utilisateur et une conversation
    user = User(username="testuser", email="test@example.com", 
                hashed_password="hashed_password", is_active=True)
    db.add(user)
    db.commit()
    
    conversation = Conversation(
        client_name="Test Client",
        status="active",
        user_id=user.id
    )
    db.add(conversation)
    db.commit()
    
    # Tester l'API de chat
    response = client.post(
        "/api/chat",
        json={
            "message": "Bonjour, j'ai un problème avec mon produit",
            "conversation_id": str(conversation.id)
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data
```

## ⚙️ Configuration

### Fichier pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Marqueurs personnalisés
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    metrics: marks tests as metrics tests
    auth: marks tests as authentication tests
    database: marks tests as database tests
    rag: marks tests as RAG functionality tests
    performance: marks tests as performance tests
    security: marks tests as security tests

# Configuration des rapports
addopts = 
    --cov=.
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
    --junitxml=test-results.xml
    --html=test-report.html
```

### Variables d'Environnement
```bash
# Base de données de test
TEST_DATABASE_URL=sqlite:///./test.db

# Configuration de test
TESTING=True
DEBUG=False

# Métriques de test
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
```

## 📈 Rapports

### Types de Rapports

1. **Rapport HTML** (`test-report.html`)
   - Interface web interactive
   - Détails des tests
   - Graphiques de performance

2. **Rapport de Couverture** (`htmlcov/index.html`)
   - Couverture de code
   - Lignes manquantes
   - Branches non testées

3. **Rapport JUnit** (`test-results.xml`)
   - Format XML standard
   - Intégration CI/CD
   - Compatible avec les outils de reporting

4. **Rapport Personnalisé** (`test_summary.html`)
   - Vue d'ensemble
   - Métriques testées
   - Points d'attention

### Génération des Rapports
```bash
# Rapport HTML complet
python -m pytest --html=test-report.html --self-contained-html

# Rapport de couverture
python -m pytest --cov=. --cov-report=html

# Rapport JUnit pour CI/CD
python -m pytest --junitxml=test-results.xml

# Tous les rapports
python run_all_tests.py --coverage --html-report --junit-report
```

## 🔧 Dépannage

### Problèmes Courants

1. **Tests qui Échouent**
   ```bash
   # Vérifier la configuration
   python -m pytest --collect-only
   
   # Exécuter avec plus de détails
   python -m pytest -vv
   
   # Vérifier les fixtures
   python -m pytest --setup-show
   ```

2. **Problèmes de Base de Données**
   ```bash
   # Réinitialiser la base de test
   rm test.db
   
   # Vérifier les migrations
   alembic upgrade head
   ```

3. **Problèmes de Métriques**
   ```bash
   # Vérifier l'endpoint /metrics
   curl http://localhost:8000/metrics
   
   # Vérifier Prometheus
   curl http://localhost:9090/api/v1/targets
   ```

4. **Problèmes de Performance**
   ```bash
   # Exécuter les tests de performance
   python -m pytest -m performance
   
   # Vérifier les timeouts
   python -m pytest --timeout=600
   ```

### Logs et Debugging

1. **Activer les Logs**
   ```bash
   python -m pytest --log-cli-level=DEBUG
   ```

2. **Debugger les Tests**
   ```python
   import pdb; pdb.set_trace()  # Point d'arrêt
   ```

3. **Vérifier les Fixtures**
   ```bash
   python -m pytest --setup-show -v
   ```

## 📚 Ressources Additionnelles

- [Documentation pytest](https://docs.pytest.org/)
- [Documentation FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Documentation Prometheus Client](https://github.com/prometheus/client_python)
- [Guide de Couverture de Code](https://coverage.readthedocs.io/)

---

*Ce guide est mis à jour régulièrement avec les nouvelles fonctionnalités de test.*