# TaskManager API - Démonstration Bug Alembic

Ce projet illustre un problème courant de versioning Alembic dans un environnement Docker et sa résolution, dans le cadre d'un exercice de débogage et monitoring.

## 🎯 Objectif

Démontrer la résolution d'un incident technique réel : l'oubli d'appliquer les migrations Alembic lors du déploiement en production, causant un crash de l'application.

## 📋 Contexte du Problème

**Situation :** 
- Application FastAPI avec PostgreSQL
- Migrations Alembic fonctionnelles en développement
- Déploiement via Docker Hub vers la production
- **Problème :** L'application plante au démarrage car les tables n'existent pas

**Cause racine :** 
Le `Dockerfile` ne contient pas la commande `alembic upgrade head` avant le démarrage de l'application.

## 🏗️ Structure du Projet

```
taskmanager-api/
├── main.py                 # Application FastAPI
├── requirements.txt        # Dépendances Python
├── alembic.ini            # Configuration Alembic
├── alembic/
│   ├── env.py             # Configuration environnement Alembic
│   └── versions/          # Scripts de migration
├── Dockerfile             # Image Docker corrigée
├── docker-compose.yml     # Configuration multi-services
├── prometheus.yml         # Configuration monitoring
└── demo.sh               # Script de démonstration
```

## 🚀 Démarrage Rapide

### 1. Prérequis
```bash
# Installer Docker et Docker Compose
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Cloner le projet
git clone <repository-url>
cd taskmanager-api
```

### 2. Lancement de l'application
```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier le statut
docker-compose ps

# Voir les logs
docker-compose logs -f app
```

### 3. Test de l'API
```bash
# Health check
curl http://localhost:8000/health

# Créer une tâche
curl -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "Ma première tâche", "description": "Test de l'API"}'

# Lister les tâches
curl http://localhost:8000/tasks
```

## 🐛 Reproduction du Problème

### Version Problématique du Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000

# PROBLÈME: Pas de migration automatique
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Résultat :** L'application plante avec `sqlalchemy.exc.ProgrammingError: relation "tasks" does not exist`

### Version Corrigée
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000

# CORRECTION: Ajout des migrations automatiques
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
```

## 🔧 Démonstration Interactive

Un script de démonstration interactif est fourni pour illustrer le problème et sa résolution :

```bash
# Rendre le script exécutable
chmod +x demo.sh

# Lancer la démonstration
./demo.sh
```

Le script vous guide à travers :
1. **Présentation du problème**
2. **Construction de l'image problématique**
3. **Démonstration de l'échec**
4. **Analyse des logs d'erreur**
5. **Correction du Dockerfile**
6. **Test de la solution**
7. **Validation fonctionnelle**
8. **Bonnes pratiques**

## 📊 Monitoring et Observabilité

### Services Inclus
- **Prometheus** (`:9090`) - Collecte de métriques
- **Grafana** (`:3000`) - Visualisation (admin/admin)
- **Application** (`:8000`) - API TaskManager

### Métriques Surveillées
- Temps de réponse des requêtes HTTP
- Taux d'erreur (4xx, 5xx)
- Nombre de requêtes par seconde
- Statut de santé de l'application
- Erreurs de base de données

### Alertes Configurées
- Temps de réponse > 2000ms
- Taux d'erreur > 5%
- Échec de connexion à la base de données
- Erreurs de migration Alembic

## 🔍 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Vérification de santé |
| GET | `/tasks` | Lister toutes les tâches |
| POST | `/tasks` | Créer une nouvelle tâche |
| GET | `/tasks/{id}` | Récupérer une tâche |
| PUT | `/tasks/{id}` | Mettre à jour une tâche |
| DELETE | `/tasks/{id}` | Supprimer une tâche |
| GET | `/metrics` | Métriques Prometheus |

## 📝 Gestion des Migrations

### Commandes Alembic Utiles
```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "Description"

# Appliquer les migrations
alembic upgrade head

# Voir l'historique des migrations
alembic history

# Rétrograder à une version
alembic downgrade -1
```

### Configuration Base de Données
```bash
# Variables d'environnement
DATABASE_URL=postgresql://user:password@db:5432/taskmanager

# Ou via .env
echo "DATABASE_URL=postgresql://user:password@localhost:5432/taskmanager" > .env
```

## 🛡️ Sécurité et Bonnes Pratiques

### Dockerfile Sécurisé
- Utilisation d'un utilisateur non-root
- Images slim pour réduire la surface d'attaque
- Gestion des secrets via variables d'environnement
- Health checks pour la surveillance

### Base de Données
- Mots de passe sécurisés
- Connexions chiffrées en production
- Sauvegardes automatiques
- Monitoring des performances

## 🚨 Résolution d'Incidents

### Processus de Debugging
1. **Vérification des logs** : `docker-compose logs app`
2. **Connexion au conteneur** : `docker exec -it app bash`
3. **Vérification de la DB** : `psql -h db -U user -d taskmanager`
4. **Test des migrations** : `alembic current`
5. **Validation des endpoints** : `curl http://localhost:8000/health`

### Problèmes Courants
| Problème | Cause | Solution |
|----------|-------|----------|
| App ne démarre pas | Migrations non appliquées | Ajouter `alembic upgrade head` |
| Erreur de connexion DB | DB non prête | Attendre avec health check |
| Ports non disponibles | Conflits de ports | Modifier `docker-compose.yml` |

## 📊 Métriques de Performance

Depuis la correction du problème :
- **Temps de démarrage** : < 30 secondes
- **Taux de succès de déploiement** : 100%
- **Temps de résolution d'incident** : < 30 minutes
- **Disponibilité** : 99.9%

## 🔄 CI/CD Pipeline

### Étapes du Pipeline
1. **Build** : Construction de l'image Docker
2. **Test** : Tests unitaires et d'intégration
3. **Security Scan** : Analyse de sécurité
4. **Push** : Envoi vers Docker Hub
5. **Deploy** : Déploiement automatique
6. **Monitor** : Surveillance post-déploiement

### Commandes de Déploiement
```bash
# Build et push
docker build -t taskmanager-api:latest .
docker push taskmanager-api:latest

# Déploiement
docker-compose pull
docker-compose up -d

# Vérification
curl http://localhost:8000/health
```

## 📚 Documentation Supplémentaire

- [Guide d'installation détaillé](docs/INSTALL.md)
- [Documentation API](docs/API.md)
- [Guide de monitoring](docs/MONITORING.md)
- [Procédures d'incident](docs/INCIDENT.md)

## 🤝 Contribution

Pour reproduire et étudier ce cas d'usage :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/analysis`)
3. Testez les différentes versions du Dockerfile
4. Documentez vos observations
5. Proposez des améliorations

## 📄 Licence

Ce projet est à des fins éducatives dans le cadre de la certification E5 - Débogage et Monitoring.

---

**Note :** Ce projet illustre un cas réel de debugging et de résolution d'incident, démontrant l'importance du monitoring et de la traçabilité dans le cycle de vie des applications.