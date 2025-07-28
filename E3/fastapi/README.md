# Chatbot SAV - Application FastAPI

Une application de chatbot pour le service après-vente utilisant FastAPI, PostgreSQL, OpenAI et FAISS pour la recherche sémantique.

## 🚀 Fonctionnalités

-   **Chat IA intelligent** : Utilise GPT-4o-mini d'OpenAI pour des réponses contextuelles
-   **Recherche sémantique** : FAISS pour la recherche dans la base de connaissances
-   **Gestion des utilisateurs** : Authentification JWT avec rôles (clients/admins)
-   **Upload d'images** : Support des images dans les conversations
-   **Interface moderne** : Interface responsive avec Bootstrap 5
-   **Gestion des conversations** : Historique et résumés automatiques
-   **Base de données** : PostgreSQL avec SQLAlchemy ORM

## 🛠️ Technologies utilisées

-   **Backend** : FastAPI, SQLAlchemy, PostgreSQL
-   **IA** : OpenAI GPT-4o-mini, LangChain, FAISS
-   **Frontend** : HTML5, CSS3, JavaScript, Bootstrap 5
-   **Authentification** : JWT (JSON Web Tokens)
-   **Containerisation** : Docker & Docker Compose

## 📋 Prérequis

-   Docker et Docker Compose
-   Clé API OpenAI
-   Python 3.11+ (pour le développement local)

## 🚀 Installation et démarrage

### 1. Cloner le repository

```bash
git clone <votre-repo>
cd E3
```

### 2. Configuration des variables d'environnement

Copiez le fichier d'exemple et configurez vos variables :

```bash
cp env_example.txt .env
```

Modifiez le fichier `.env` avec vos valeurs :

```env
DATABASE_URL=postgresql://postgres:password@db:5432/chatbot_sav
SECRET_KEY=your-super-secret-key-change-in-production
OPENAI_API_KEY=your-openai-api-key-here
DEBUG=True
ENVIRONMENT=development
```

### 3. Lancement avec Docker Compose

```bash
# Construire et lancer les services
docker-compose up --build

# Ou en arrière-plan
docker-compose up -d --build
```

L'application sera accessible à : http://localhost:8000

## 🧪 Tests et qualité

### Exécution des tests

```bash
# Lancer tous les tests
python run_tests.py

# Ou depuis le dossier tests
cd tests
python run_all_tests.py

# Tests spécifiques
python -m pytest test_working.py -v
python -m pytest test_basic.py -v
python test_simple.py
```

### Structure des tests

```
tests/
├── test_working.py          # 19 tests fonctionnels
├── test_basic.py            # 7 tests basiques
├── test_auth.py             # Tests d'authentification
├── test_api_endpoints.py    # Tests des endpoints
├── test_simple.py           # Tests simples
├── run_all_tests.py         # Script principal
└── README.md               # Documentation
```

### Couverture de code

Les tests couvrent :

-   ✅ Authentification et autorisation (JWT, bcrypt)
-   ✅ Endpoints de l'API (routes, réponses HTTP)
-   ✅ Gestion des conversations et commandes
-   ✅ Upload d'images et fichiers
-   ✅ Validation des données (Pydantic)
-   ✅ Gestion d'erreurs et sécurité
-   ✅ Configuration et middleware

**Objectif de couverture** : 80% minimum

### Audit de sécurité

Le script inclut un audit de sécurité qui vérifie :

-   Configuration JWT (secret key, algorithm)
-   Hachage des mots de passe (bcrypt)
-   Configuration CORS (middleware)
-   Validation des données (Pydantic schemas)

## 👤 Comptes par défaut

### Comptes par défaut

#### Compte Administrateur

Un compte administrateur est créé automatiquement au premier démarrage :

-   **Username** : `admin`
-   **Password** : `admin123`
-   **Email** : `admin@chatbot-sav.com`
-   **Rôles** : Staff + Superuser

#### Utilisateurs de test

Pour créer des utilisateurs de test avec leurs données, utilisez le script :

```bash
# Créer les utilisateurs de test
python create_test_users.py

# Lister les utilisateurs de test
python create_test_users.py list
```

Cela créera :

-   **Martin Dupont** : `martin` / `client123` (2 commandes)
-   **Sophie Martin** : `sophie` / `client123` (2 commandes)

### Créer d'autres utilisateurs admin

Vous pouvez créer d'autres utilisateurs administrateur avec le script :

```bash
# Utiliser les valeurs par défaut
python create_admin.py

# Ou spécifier des valeurs personnalisées
python create_admin.py monadmin motdepasse123 monadmin@example.com

# Lister tous les utilisateurs
python create_admin.py list
```

### 4. Initialisation des données (optionnel)

Les données d'exemple sont créées automatiquement au premier démarrage. Vous pouvez personnaliser les fichiers dans le dossier `data/` :

-   `data/preprompt.json` : Instructions système pour l'IA
-   `data/renseignements.json` : FAQ et procédures
-   `data/retours.json` : Politique de retours
-   `data/commandes.json` : Informations sur les commandes
-   `data/documents/` : Documents pour la recherche FAISS

## 📁 Structure du projet

```
E3/
├── app.py                 # Application FastAPI principale
├── models.py             # Modèles SQLAlchemy
├── schemas.py            # Schémas Pydantic
├── routes.py             # Routes et endpoints
├── auth.py               # Authentification JWT
├── langchain_utils.py    # Utilitaires LangChain/FAISS
├── templates/            # Templates HTML
│   ├── base.html
│   ├── login.html
│   ├── client_register.html
│   ├── client_home.html
│   ├── openai_chat.html
│   ├── conversations_list.html
│   └── conversation_detail.html
├── static/               # Fichiers statiques
│   ├── css/styles.css
│   └── js/main.js
├── data/                 # Données de configuration
├── uploads/              # Fichiers uploadés
├── uploads/              # Images uploadées
├── docker-compose.yml    # Configuration Docker
├── Dockerfile           # Image Docker
├── requirements.txt     # Dépendances Python
└── README.md           # Ce fichier
```

## 🔧 Développement local

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Lancement en mode développement

```bash
# Avec PostgreSQL local
export DATABASE_URL="postgresql://username:password@localhost:5432/chatbot_sav"
export OPENAI_API_KEY="your-api-key"
export SECRET_KEY="your-secret-key"

# Lancer l'application
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 👥 Utilisation

### 1. Création d'un compte

-   Accédez à http://localhost:8000
-   Cliquez sur "Inscription" pour créer un compte client
-   Ou connectez-vous si vous avez déjà un compte

### 2. Chat avec l'assistant

-   Une fois connecté, cliquez sur "Chat" dans la sidebar
-   Tapez votre question dans la zone de texte
-   Vous pouvez également envoyer des images via le bouton trombone
-   Utilisez "Nouveau Chat" pour recommencer une conversation
-   Cliquez sur "Terminer la conversation" pour générer un résumé

### 3. Interface administrateur

Les utilisateurs avec les droits `is_staff` ou `is_superuser` peuvent :

-   Voir toutes les conversations dans "Conversations"
-   Filtrer par statut (nouveau, en cours, terminé)
-   Consulter les détails de chaque conversation
-   Générer des résumés automatiques

## 🔐 Authentification

L'application utilise JWT pour l'authentification :

-   Les tokens sont stockés dans des cookies HTTPOnly
-   Durée de vie : 30 minutes
-   Rafraîchissement automatique lors de l'utilisation

### Rôles utilisateurs

-   **Client** : Peut utiliser le chat et voir ses propres conversations
-   **Staff/Admin** : Peut gérer toutes les conversations et accéder aux fonctions d'administration

## 🤖 Configuration de l'IA

### Modèle OpenAI

-   **Modèle** : gpt-4o-mini
-   **Tokens max** : 500
-   **Température** : 0.4 (pour des réponses cohérentes)

### Base de connaissances FAISS

-   Index vectoriel pour la recherche sémantique
-   Documents stockés dans `data/documents/`
-   Rechargement automatique des nouveaux documents

## 📊 Base de données

### Tables principales

-   **users** : Utilisateurs de l'application
-   **client_users** : Profils clients
-   **conversations** : Conversations avec l'IA

### Migrations

Les tables sont créées automatiquement au démarrage via SQLAlchemy.

## 🐳 Docker

### Services

-   **web** : Application FastAPI
-   **db** : PostgreSQL 15
-   **volumes** : Persistance des données

### Commandes utiles

```bash
# Voir les logs
docker-compose logs -f

# Redémarrer un service
docker-compose restart web

# Accéder au shell du conteneur
docker-compose exec web bash

# Sauvegarder la base de données
docker-compose exec db pg_dump -U postgres chatbot_sav > backup.sql
```

## 🔧 Personnalisation

### Ajout de nouveaux documents

1. Placez vos fichiers `.txt` dans `data/documents/`
2. Redémarrez l'application pour recharger l'index FAISS

### Modification du prompt système

Éditez `data/preprompt.json` :

```json
{
    "content": "Votre nouveau prompt système pour l'IA..."
}
```

### Personnalisation de l'interface

-   CSS : `static/css/styles.css`
-   JavaScript : `static/js/main.js`
-   Templates : `templates/*.html`

## 🚨 Sécurité

-   Changez `SECRET_KEY` en production
-   Utilisez HTTPS en production
-   Configurez un firewall pour PostgreSQL
-   Limitez les uploads de fichiers
-   Validez toutes les entrées utilisateur

## 📈 Monitoring et logs

Les logs sont disponibles via Docker :

```bash
docker-compose logs -f web
```

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour toute question ou problème :

1. Consultez la documentation
2. Vérifiez les issues GitHub
3. Créez une nouvelle issue si nécessaire

## 📚 Ressources

-   [FastAPI Documentation](https://fastapi.tiangolo.com/)
-   [OpenAI API](https://platform.openai.com/docs)
-   [LangChain Documentation](https://python.langchain.com/)
-   [FAISS Documentation](https://faiss.ai/)
-   [Bootstrap 5](https://getbootstrap.com/docs/5.0/)

---

**Développé avec ❤️ pour améliorer l'expérience du service après-vente**
