# Rapport Technique - Service de Traitement des Logs FTP (ftp_log_service.py)

## Vue d'ensemble

Le service `ftp_log_service.py` est un composant central du système de data engineering qui collecte, traite et analyse les fichiers de logs des centres d'usinage (machines de production) via FTP. Ce service transforme des données brutes de production en métriques structurées stockées dans PostgreSQL.

## Architecture du Service

### 1. Classe FTPLogService

**Rôle principal** : Orchestrateur du processus de collecte et traitement des logs

**Responsabilités** :

-   Connexion aux services (FTP, PostgreSQL)
-   Gestion du cycle de vie des données
-   Traitement et analyse des logs
-   Sauvegarde des métriques

### 2. Configuration et Initialisation

```python
def __init__(self):
    # Configuration FTP
    self.ftp_host = os.getenv('FTP_HOST')
    self.ftp_user = os.getenv('FTP_USER')
    self.ftp_pass = os.getenv('FTP_PASS')

    # Configuration PostgreSQL
    self.db_host = os.getenv('POSTGRES_HOST')
    self.db_name = os.getenv('POSTGRES_DB')
    self.db_user = os.getenv('POSTGRES_USER')
    self.db_pass = os.getenv('POSTGRES_PASSWORD')

    # Mapping des dossiers FTP vers types de machines
    self.cu_directories = {
        'DEM12 (PVC)': 'DEM12',
        'DEMALU (ALU)': 'DEMALU',
        'SU12 (HYBRIDE)': 'SU12'
    }
```

**Avantages** :

-   **Configuration externalisée** : Variables d'environnement
-   **Flexibilité** : Mapping configurable des dossiers
-   **Maintenabilité** : Séparation claire des responsabilités

## Gestion des Connexions

### 1. Connexion PostgreSQL

```python
def connect_db(self):
    try:
        self.conn = psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_pass
        )
        self.cur = self.conn.cursor()
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la connexion à la base de données: {e}")
        return False
```

**Fonctionnalités** :

-   **Gestion d'erreurs** : Try/catch avec logging
-   **Curseur** : Interface pour les requêtes SQL
-   **Validation** : Retour booléen pour la gestion d'erreurs

### 2. Connexion FTP

```python
def connect_ftp(self):
    try:
        self.ftp = ftplib.FTP(self.ftp_host)
        self.ftp.login(self.ftp_user, self.ftp_pass)
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la connexion FTP: {e}")
        self.ftp = None
        return False
```

**Caractéristiques** :

-   **Protocole FTP** : Transfert de fichiers standard
-   **Authentification** : Login/password
-   **Gestion d'erreurs** : Nettoyage en cas d'échec

## Structure de la Base de Données

### Tables Créées :

#### 1. `centre_usinage`

```sql
CREATE TABLE IF NOT EXISTS centre_usinage (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    type_cu VARCHAR(50) NOT NULL,
    description TEXT,
    actif BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `session_production`

```sql
CREATE TABLE IF NOT EXISTS session_production (
    id SERIAL PRIMARY KEY,
    centre_usinage_id INTEGER REFERENCES centre_usinage(id),
    date_production DATE NOT NULL,
    heure_premiere_piece TIMESTAMP,
    heure_derniere_piece TIMESTAMP,
    total_pieces INTEGER DEFAULT 0,
    duree_production_totale DECIMAL(10,4),
    taux_occupation DECIMAL(5,2),
    fichier_log_source VARCHAR(255),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(centre_usinage_id, date_production)
);
```

#### 3. Tables de Détails

-   `job_profil` : Profils de jobs de production
-   `periode_attente` : Périodes d'attente des machines
-   `periode_arret` : Périodes d'arrêt des machines
-   `piece_production` : Détails de chaque pièce produite

## Traitement des Données FTP

### 1. Découverte des Dossiers

```python
def get_cu_directories_from_ftp(self, ftp):
    all_dirs = ftp.nlst()
    cu_dirs = []
    for directory in all_dirs:
        if directory in self.cu_directories:
            cu_dirs.append(directory)
            cu_type = self.cu_directories[directory]
            logger.info(f"✅ Dossier trouvé: {directory} -> Type: {cu_type}")
    return cu_dirs
```

**Fonctionnalités** :

-   **Listage automatique** : Découverte des dossiers disponibles
-   **Filtrage intelligent** : Mapping vers les types de machines
-   **Logging détaillé** : Traçabilité des découvertes

### 2. Collecte des Fichiers LOG

```python
def get_log_files_from_directory(self, ftp, directory):
    ftp.cwd(directory)
    files = ftp.nlst()
    log_files = [f for f in files if f.endswith('.LOG')]
    ftp.cwd('/')
    return log_files
```

**Caractéristiques** :

-   **Navigation sécurisée** : Retour à la racine après chaque opération
-   **Filtrage par extension** : Seuls les fichiers .LOG
-   **Gestion d'erreurs** : Nettoyage en cas de problème

### 3. Téléchargement des Fichiers

```python
def download_log_file_from_directory(self, ftp, directory, filename):
    log_content_bytes = bytearray()

    def handle_binary(data):
        log_content_bytes.extend(data)

    ftp.retrbinary(f'RETR {filename}', handle_binary)
    log_content = log_content_bytes.decode('latin-1')
    return log_content
```

**Optimisations** :

-   **Mode binaire** : Évite les problèmes d'encodage
-   **Encodage latin-1** : Compatible avec tous les caractères
-   **Gestion mémoire** : Accumulation progressive des données

## Analyse des Données

### 1. Parsing des Logs

Le service analyse les fichiers LOG pour extraire :

-   **Horodatages** : Moments de production
-   **Identifiants de pièces** : Numérotation séquentielle
-   **Profils de jobs** : Types de production
-   **Périodes d'attente/arrêt** : Temps d'arrêt des machines

### 2. Calcul des Métriques

**Métriques calculées** :

-   **Temps de production effectif** : Temps réel de fabrication
-   **Taux d'occupation** : Pourcentage d'utilisation de la machine
-   **Temps d'attente** : Périodes d'inactivité
-   **Nombre de pièces** : Production totale par session

### 3. Algorithmes d'Analyse

```python
def analyze_machine_performance(self, data, log_file_name, cu_type):
    # Analyse temporelle des données
    # Calcul des métriques de performance
    # Identification des patterns de production
    # Génération des rapports de performance
```

**Fonctionnalités avancées** :

-   **Analyse temporelle** : Traitement des séries temporelles
-   **Détection d'anomalies** : Identification des problèmes
-   **Optimisation** : Suggestions d'amélioration

## Sauvegarde des Données

### 1. Insertion en Base

```python
def save_to_database(self, results, cu_type, log_file_name, directory):
    # Insertion des données de session
    # Sauvegarde des métriques
    # Gestion des contraintes d'unicité
    # Validation des données
```

**Caractéristiques** :

-   **Transactions** : Atomicité des opérations
-   **Contraintes d'unicité** : Évite les doublons
-   **Validation** : Vérification de l'intégrité des données

### 2. Gestion des Erreurs

-   **Rollback automatique** : En cas d'erreur
-   **Logging détaillé** : Traçabilité des opérations
-   **Récupération** : Mécanismes de retry

## Orchestration du Processus

### 1. Méthode Principale

```python
def process_all_logs(self, delete_after_processing=True):
    # 1. Connexion aux services
    # 2. Découverte des dossiers FTP
    # 3. Collecte des fichiers LOG
    # 4. Traitement et analyse
    # 5. Sauvegarde en base
    # 6. Nettoyage (suppression des fichiers traités)
```

### 2. Gestion du Cycle de Vie

**Étapes du processus** :

1. **Initialisation** : Connexions et vérifications
2. **Collecte** : Récupération des fichiers FTP
3. **Traitement** : Analyse et calcul des métriques
4. **Sauvegarde** : Insertion en PostgreSQL
5. **Nettoyage** : Suppression des fichiers traités
6. **Fermeture** : Libération des ressources

## Gestion des Erreurs et Robustesse

### 1. Mécanismes de Récupération

-   **Reconnexion automatique** : En cas de perte de connexion
-   **Retry intelligent** : Tentatives multiples avec délai
-   **Isolation des erreurs** : Une erreur n'affecte pas les autres fichiers

### 2. Logging et Monitoring

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

**Avantages** :

-   **Traçabilité complète** : Toutes les opérations loggées
-   **Debugging facilité** : Informations détaillées
-   **Monitoring** : Métriques de performance

## Performance et Optimisations

### 1. Optimisations Appliquées

-   **Téléchargement binaire** : Performance FTP optimisée
-   **Traitement par lots** : Gestion efficace de la mémoire
-   **Connexions persistantes** : Réutilisation des connexions
-   **Index de base de données** : Requêtes optimisées

### 2. Métriques de Performance

-   **Temps de traitement** : Mesurable par fichier
-   **Taux de succès** : Pourcentage de fichiers traités
-   **Utilisation mémoire** : Optimisée pour les gros fichiers
-   **Débit** : Nombre de fichiers par minute

## Sécurité

### 1. Bonnes Pratiques

-   **Variables d'environnement** : Pas de secrets en dur
-   **Connexions sécurisées** : FTP avec authentification
-   **Validation des données** : Vérification des entrées
-   **Permissions minimales** : Principe du moindre privilège

### 2. Gestion des Risques

-   **Isolation des erreurs** : Une erreur n'affecte pas le système
-   **Nettoyage automatique** : Libération des ressources
-   **Logs sécurisés** : Pas de secrets dans les logs

## Intégration avec l'Écosystème

### 1. Docker Compose

-   **Variables d'environnement** : Configuration externalisée
-   **Health checks** : Intégration avec les health checks
-   **Volumes** : Partage des logs avec l'hôte

### 2. Cron

-   **Exécution périodique** : Toutes les 5 minutes
-   **Gestion des erreurs** : Retry automatique
-   **Monitoring** : Logs centralisés

## Avantages de cette Architecture

1. **Scalabilité** : Peut traiter de nombreux fichiers
2. **Robustesse** : Gestion d'erreurs complète
3. **Observabilité** : Logs détaillés et métriques
4. **Maintenabilité** : Code modulaire et bien structuré
5. **Performance** : Optimisations multiples
6. **Sécurité** : Bonnes pratiques appliquées

## Cas d'Usage Réels

### 1. Industrie Manufacturière

-   **Suivi de production** : Monitoring en temps réel
-   **Optimisation** : Identification des goulots d'étranglement
-   **Maintenance prédictive** : Détection des problèmes

### 2. Data Engineering

-   **ETL** : Extraction, Transformation, Loading
-   **Data Lake** : Stockage structuré des données
-   **Analytics** : Métriques de performance

Ce service représente une solution complète de data engineering pour l'industrie manufacturière, combinant collecte de données, traitement en temps réel et stockage structuré pour l'analyse et l'optimisation des processus de production.
