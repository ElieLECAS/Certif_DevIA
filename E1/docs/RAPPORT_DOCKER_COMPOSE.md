# Rapport Technique - Docker Compose

## Vue d'ensemble

Le fichier `docker-compose.yaml` est le cœur de l'architecture du projet E1. Il définit une infrastructure complète de services conteneurisés pour la gestion des données de commandes de volets roulants. Cette architecture suit les principes DevOps et microservices.

## Architecture des Services

### 1. Service FTP (`ftp`)

**Image**: `fauria/vsftpd`
**Ports exposés**:

-   21 (port de contrôle FTP)
-   21000-21010 (ports passifs pour le transfert de données)

**Configuration**:

-   Utilise des variables d'environnement pour la configuration
-   Volume monté : `./logs` vers `/home/vsftpd/${FTP_USER}`
-   Redémarrage automatique sauf arrêt manuel

**Rôle dans le système**:
Le serveur FTP sert de point de collecte centralisé pour les fichiers de logs des machines de production. Les centres d'usinage (machines de fabrication) envoient leurs fichiers de logs via FTP vers ce serveur, où ils sont ensuite traités par le service de synchronisation.

### 2. Base de données PostgreSQL (`db`)

**Image**: `postgres:15`
**Port**: Variable `${POSTGRES_PORT}` (défaut 5432)
**Volumes**: `pgdata` (persistance des données)

**Healthcheck**:

```yaml
healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
```

**Rôle**:
Base de données principale pour stocker les données traitées des logs FTP et les métriques de production. PostgreSQL est choisi pour sa robustesse et ses capacités avancées de requêtes.

### 3. Base de données MySQL (`mysql_db`)

**Image**: `mysql:8.0`
**Port**: 3306
**Volumes**:

-   `mysql_data` (persistance)
-   `./init.sql` (script d'initialisation)

**Configuration**:

-   Base de données : `db_commandes`
-   Utilisateur : `fenetre_user`
-   Script d'initialisation automatique

**Rôle**:
Base de données legacy contenant les données métier des commandes de volets roulants. Cette base simule un système existant dont les données doivent être synchronisées vers PostgreSQL.

### 4. Service de Synchronisation (`sync_service`)

**Build**: `./script` (image personnalisée)
**Dépendances**:

-   `mysql_db` (condition: service_healthy)
-   `db` (condition: service_healthy)

**Variables d'environnement**:

-   Configuration PostgreSQL et MySQL
-   Configuration FTP
-   Paramètres de synchronisation

**Rôle**:
Service central qui orchestre la synchronisation des données entre les différentes sources (FTP, MySQL) vers PostgreSQL. Il exécute deux services Python en parallèle via cron.

### 5. API FastAPI (`api`)

**Build**: `./api`
**Port**: 8000
**Dépendances**: `db` (condition: service_healthy)

**Rôle**:
Interface REST pour exposer les données traitées et permettre l'intégration avec d'autres systèmes.

## Gestion des Volumes

```yaml
volumes:
    pgdata: # Données PostgreSQL persistantes
    mysql_data: # Données MySQL persistantes
```

## Orchestration et Dépendances

### Ordre de démarrage

1. **FTP** et **MySQL** démarrent en premier
2. **PostgreSQL** démarre avec healthcheck
3. **Sync Service** attend que MySQL et PostgreSQL soient "healthy"
4. **API** attend que PostgreSQL soit "healthy"

### Healthchecks

Les healthchecks garantissent que les services sont réellement opérationnels avant que les services dépendants ne démarrent.

## Sécurité et Configuration

### Variables d'environnement

Le système utilise des variables d'environnement pour :

-   Séparer la configuration du code
-   Faciliter le déploiement dans différents environnements
-   Sécuriser les informations sensibles (mots de passe, etc.)

### Isolation des conteneurs

Chaque service fonctionne dans son propre conteneur, garantissant :

-   Isolation des processus
-   Gestion indépendante des ressources
-   Facilité de maintenance et mise à jour

## Avantages de cette Architecture

1. **Scalabilité** : Chaque service peut être mis à l'échelle indépendamment
2. **Maintenabilité** : Services isolés facilitent le debugging et les mises à jour
3. **Robustesse** : Healthchecks et redémarrage automatique
4. **Flexibilité** : Configuration via variables d'environnement
5. **Observabilité** : Logs centralisés et monitoring possible

## Flux de Données

```
[Machines de Production] → FTP → Sync Service → PostgreSQL → API
[MySQL Legacy] → Sync Service → PostgreSQL → API
```

Cette architecture permet une intégration transparente entre un système legacy (MySQL) et un nouveau système moderne (PostgreSQL) tout en collectant des données en temps réel via FTP.
