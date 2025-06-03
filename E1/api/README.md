# API Production Industrielle

API CRUD FastAPI pour la gestion des données de production des centres d'usinage.

## Description

Cette API expose les données de production stockées dans PostgreSQL et permet de :

-   Gérer les centres d'usinage (CRUD)
-   Consulter les sessions de production
-   Accéder aux données de jobs, périodes d'attente/arrêt et pièces produites
-   Obtenir des statistiques de production

## Structure de la base de données

L'API expose les tables suivantes :

-   `centre_usinage` : Informations sur les machines
-   `session_production` : Sessions de production journalières
-   `job_profil` : Profils des jobs exécutés
-   `periode_attente` : Périodes d'attente des machines
-   `periode_arret` : Périodes d'arrêt des machines
-   `piece_production` : Détails des pièces produites

## Installation et démarrage

### Avec Docker (recommandé)

1. Assurez-vous que le service PostgreSQL est démarré
2. Construisez et démarrez l'API :

```bash
docker-compose up api
```

### Installation locale

1. Installez les dépendances :

```bash
pip install -r requirements.txt
```

2. Configurez les variables d'environnement :

```bash
export DB_HOST=localhost
export DB_NAME=production_db
export DB_USER=postgres
export DB_PASS=password
```

3. Démarrez l'API :

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Documentation de l'API

Une fois l'API démarrée, la documentation interactive est disponible à :

-   **Swagger UI** : http://localhost:8000/docs
-   **ReDoc** : http://localhost:8000/redoc

## Endpoints principaux

### Centres d'usinage

-   `GET /centres-usinage/` : Liste des centres d'usinage
-   `GET /centres-usinage/{id}` : Détails d'un centre avec ses sessions
-   `POST /centres-usinage/` : Créer un nouveau centre
-   `PUT /centres-usinage/{id}` : Mettre à jour un centre
-   `DELETE /centres-usinage/{id}` : Supprimer un centre

### Sessions de production

-   `GET /sessions-production/` : Liste des sessions (avec filtres)
-   `GET /sessions-production/{id}` : Détails d'une session
-   `POST /sessions-production/` : Créer une nouvelle session
-   `PUT /sessions-production/{id}` : Mettre à jour une session
-   `DELETE /sessions-production/{id}` : Supprimer une session

### Statistiques

-   `GET /stats/production-summary` : Résumé global de production
-   `GET /stats/production-by-centre/{id}` : Statistiques par centre

### Santé de l'API

-   `GET /health` : Vérification de l'état de l'API

## Filtres disponibles

### Sessions de production

-   `centre_usinage_id` : Filtrer par centre d'usinage
-   `date_debut` : Date de début (format YYYY-MM-DD)
-   `date_fin` : Date de fin (format YYYY-MM-DD)
-   `skip` : Nombre d'éléments à ignorer (pagination)
-   `limit` : Nombre maximum d'éléments à retourner

### Pièces de production

-   `session_id` : Filtrer par session
-   `date_debut` : Date/heure de début (format ISO)
-   `date_fin` : Date/heure de fin (format ISO)

## Exemples d'utilisation

### Récupérer tous les centres d'usinage actifs

```bash
curl -X GET "http://localhost:8000/centres-usinage/"
```

### Créer un nouveau centre d'usinage

```bash
curl -X POST "http://localhost:8000/centres-usinage/" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "CU-001",
    "type_cu": "PVC",
    "description": "Centre d'usinage PVC principal"
  }'
```

### Récupérer les sessions de production d'un centre

```bash
curl -X GET "http://localhost:8000/sessions-production/?centre_usinage_id=1&date_debut=2024-01-01&date_fin=2024-01-31"
```

### Obtenir les statistiques globales

```bash
curl -X GET "http://localhost:8000/stats/production-summary"
```

## Configuration

### Variables d'environnement

| Variable  | Description             | Défaut      |
| --------- | ----------------------- | ----------- |
| `DB_HOST` | Hôte PostgreSQL         | `localhost` |
| `DB_NAME` | Nom de la base          | -           |
| `DB_USER` | Utilisateur PostgreSQL  | -           |
| `DB_PASS` | Mot de passe PostgreSQL | -           |

### CORS

L'API est configurée pour accepter les requêtes de toutes les origines en développement.
En production, modifiez la configuration CORS dans `main.py`.

## Développement

### Structure du projet

```
api/
├── main.py          # Application FastAPI principale
├── database.py      # Configuration SQLAlchemy
├── models.py        # Modèles de données
├── schemas.py       # Schémas Pydantic
├── crud.py          # Opérations CRUD
├── requirements.txt # Dépendances Python
├── Dockerfile       # Image Docker
└── README.md        # Documentation
```

### Tests

Pour tester l'API, vous pouvez utiliser :

-   L'interface Swagger à http://localhost:8000/docs
-   Des outils comme Postman ou curl
-   Les tests automatisés (à implémenter)

## Sécurité

⚠️ **Important** : Cette API est configurée pour le développement. Pour la production :

-   Configurez l'authentification/autorisation
-   Limitez les origines CORS
-   Utilisez HTTPS
-   Configurez des variables d'environnement sécurisées
-   Implémentez la limitation de taux (rate limiting)
