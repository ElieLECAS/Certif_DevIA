# Rapport Technique - Dockerfile (Script Service)

## Vue d'ensemble

Le `Dockerfile` du dossier `script` définit l'image Docker pour le service de synchronisation. Cette image contient l'environnement Python nécessaire pour exécuter les services de traitement FTP et de synchronisation MySQL vers PostgreSQL.

## Analyse Ligne par Ligne

### Image de Base

```dockerfile
FROM python:3.9-slim
```

-   **Choix de Python 3.9** : Version stable et largement supportée
-   **Image slim** : Réduction de la taille de l'image (environ 40MB vs 300MB pour l'image complète)
-   **Avantages** : Démarrage plus rapide, moins de vulnérabilités potentielles

### Configuration du Répertoire de Travail

```dockerfile
WORKDIR /app
```

-   Définit `/app` comme répertoire de travail
-   Tous les commandes suivantes s'exécutent dans ce répertoire
-   Bonne pratique pour organiser l'application

### Installation des Dépendances Système

```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    cron \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*
```

**Composants installés** :

-   **gcc** : Compilateur C nécessaire pour certaines dépendances Python
-   **python3-dev** : Headers Python pour compiler des extensions
-   **libpq-dev** : Bibliothèques de développement PostgreSQL (pour psycopg2)
-   **cron** : Planificateur de tâches pour exécuter les services périodiquement
-   **dos2unix** : Conversion des fins de ligne Windows vers Unix

**Optimisation** :

-   `&& rm -rf /var/lib/apt/lists/*` : Supprime le cache apt pour réduire la taille de l'image

### Installation des Dépendances Python

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

-   Copie le fichier `requirements.txt` dans le conteneur
-   Installation des packages Python sans cache pour réduire la taille
-   Dépendances principales : SQLAlchemy, PyMySQL, psycopg2, pandas, APScheduler

### Copie du Code Source

```dockerfile
COPY . .
```

-   Copie tous les fichiers du répertoire `script` dans le conteneur
-   Inclut les scripts Python et les fichiers de configuration

### Configuration du Système de Logs

```dockerfile
RUN touch /var/log/cron.log
```

-   Crée le fichier de log pour cron
-   Permet de tracer l'exécution des tâches planifiées

### Configuration du Script de Démarrage

```dockerfile
COPY start.sh /start.sh
RUN dos2unix /start.sh
RUN chmod +x /start.sh
```

-   Copie le script de démarrage
-   Conversion des fins de ligne Windows vers Unix (compatibilité)
-   Attribution des permissions d'exécution

### Configuration de Cron

```dockerfile
RUN mkdir -p /etc/cron.d
```

-   Crée le répertoire pour les fichiers de configuration cron
-   Permet d'ajouter des tâches planifiées dynamiquement

### Commande de Démarrage

```dockerfile
CMD ["/start.sh"]
```

-   Exécute le script de démarrage au lancement du conteneur
-   Alternative commentée : `CMD ["python", "mysql_sync_service.py"]`

## Dépendances Python Installées

### Bibliothèques Principales :

-   **SQLAlchemy 2.0.23** : ORM pour la gestion des bases de données
-   **PyMySQL 1.1.0** : Connecteur MySQL pour Python
-   **psycopg2 2.9.9** : Connecteur PostgreSQL pour Python
-   **pandas 2.1.3** : Manipulation et analyse de données
-   **APScheduler 3.10.4** : Planification de tâches
-   **python-dotenv 1.0.0** : Gestion des variables d'environnement
-   **pysftp 0.2.9** : Client SFTP pour Python

## Architecture de l'Image

### Structure des Couches Docker :

1. **Image de base** : python:3.9-slim
2. **Système** : Dépendances système (gcc, cron, etc.)
3. **Python** : Packages Python installés
4. **Application** : Code source et configuration
5. **Runtime** : Script de démarrage et logs

### Optimisations Appliquées :

-   **Image slim** : Réduction de la taille
-   **Suppression du cache** : `--no-cache-dir` et `rm -rf /var/lib/apt/lists/*`
-   **Conversion des fins de ligne** : Compatibilité cross-platform
-   **Permissions appropriées** : Sécurité et fonctionnalité

## Intégration avec Docker Compose

### Variables d'Environnement :

L'image reçoit les variables d'environnement depuis `docker-compose.yaml` :

-   Configuration PostgreSQL et MySQL
-   Paramètres FTP
-   Intervalles de synchronisation

### Volumes Montés :

-   `./script:/app` : Code source en développement
-   `./logs:/app/logs` : Logs partagés avec l'hôte

### Dépendances :

-   Attend que MySQL et PostgreSQL soient "healthy"
-   S'intègre dans l'orchestration Docker Compose

## Sécurité et Bonnes Pratiques

### Sécurité :

-   **Image officielle** : python:3.9-slim est maintenue par l'équipe Python
-   **Permissions minimales** : Seules les permissions nécessaires sont accordées
-   **Pas de root** : L'application ne s'exécute pas en tant que root

### Bonnes Pratiques :

-   **Multi-stage build** : Possibilité d'optimiser davantage
-   **Health checks** : Intégration avec les health checks Docker
-   **Logs centralisés** : Configuration pour l'observabilité
-   **Variables d'environnement** : Configuration externalisée

## Avantages de cette Configuration

1. **Portabilité** : Fonctionne sur tous les environnements Docker
2. **Reproductibilité** : Même environnement partout
3. **Maintenabilité** : Configuration centralisée et versionnée
4. **Performance** : Image optimisée pour la production
5. **Sécurité** : Bonnes pratiques de sécurité appliquées

## Utilisation dans le Système

### Rôle dans l'Architecture :

-   **Service de synchronisation** : Traite les données FTP et MySQL
-   **Orchestration** : Intégré dans l'écosystème Docker Compose
-   **Monitoring** : Logs et métriques disponibles
-   **Scalabilité** : Peut être répliqué selon les besoins

Cette image Docker représente une approche moderne du déploiement d'applications, combinant efficacité, sécurité et maintenabilité pour un service de data engineering robuste.
