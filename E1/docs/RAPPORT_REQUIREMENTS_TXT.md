# Rapport Technique - Requirements.txt

## Vue d'ensemble

Le fichier `requirements.txt` définit toutes les dépendances Python nécessaires pour le service de synchronisation. Ces bibliothèques permettent la gestion des bases de données, le traitement des données, la planification des tâches et la communication avec les services externes.

## Analyse Détaillée des Dépendances

### 1. SQLAlchemy 2.0.23

**Rôle** : ORM (Object-Relational Mapping) pour la gestion des bases de données

**Fonctionnalités utilisées** :

-   **Gestion des connexions** : Pool de connexions automatique
-   **Requêtes SQL** : Interface Python pour les requêtes SQL
-   **Mapping objet-relationnel** : Conversion automatique entre objets Python et tables SQL
-   **Transactions** : Gestion des transactions avec rollback automatique

**Utilisation dans le projet** :

```python
# Exemple d'utilisation dans le code
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://user:pass@host/db')
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM commandes_volets"))
```

### 2. PyMySQL 1.1.0

**Rôle** : Connecteur MySQL pur Python

**Caractéristiques** :

-   **Pure Python** : Pas de dépendances C, installation simplifiée
-   **Compatibilité** : Support complet du protocole MySQL
-   **Performance** : Optimisé pour les applications Python
-   **Sécurité** : Support SSL/TLS intégré

**Utilisation dans le projet** :

```python
# Connexion à MySQL
import mysql.connector
conn = mysql.connector.connect(
    host='mysql_db',
    user='fenetre_user',
    password='password',
    database='db_commandes'
)
```

### 3. psycopg2 2.9.9

**Rôle** : Connecteur PostgreSQL pour Python

**Avantages** :

-   **Performance** : Implémentation C optimisée
-   **Fonctionnalités avancées** : Support des types PostgreSQL complexes
-   **Fiabilité** : Connecteur le plus utilisé pour PostgreSQL
-   **Support complet** : Toutes les fonctionnalités PostgreSQL

**Utilisation dans le projet** :

```python
# Connexion à PostgreSQL
import psycopg2
conn = psycopg2.connect(
    host='db',
    database='postgres',
    user='postgres',
    password='password'
)
```

### 4. pandas 2.1.3

**Rôle** : Manipulation et analyse de données

**Fonctionnalités utilisées** :

-   **DataFrames** : Structure de données tabulaires
-   **Traitement de données** : Filtrage, groupement, agrégation
-   **Lecture/écriture** : Support de multiples formats (CSV, JSON, etc.)
-   **Analyse temporelle** : Gestion des dates et heures

**Utilisation dans le projet** :

```python
# Traitement des données de logs
import pandas as pd
df = pd.DataFrame(log_data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df_grouped = df.groupby('machine_id').agg({
    'production_time': 'sum',
    'pieces_count': 'count'
})
```

### 5. APScheduler 3.10.4

**Rôle** : Planification de tâches avancée

**Fonctionnalités** :

-   **Planification flexible** : Cron, intervalle, date spécifique
-   **Persistance** : Sauvegarde des tâches en base de données
-   **Gestion d'erreurs** : Retry automatique et gestion des exceptions
-   **Monitoring** : Logs détaillés des exécutions

**Utilisation dans le projet** :

```python
# Planification des tâches de synchronisation
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(sync_mysql_data, 'interval', minutes=15)
scheduler.add_job(process_ftp_logs, 'interval', minutes=5)
scheduler.start()
```

### 6. python-dotenv 1.0.0

**Rôle** : Gestion des variables d'environnement

**Fonctionnalités** :

-   **Fichier .env** : Chargement automatique depuis un fichier .env
-   **Variables d'environnement** : Accès aux variables système
-   **Sécurité** : Séparation de la configuration du code
-   **Flexibilité** : Support de différents environnements

**Utilisation dans le projet** :

```python
# Chargement des variables d'environnement
from dotenv import load_dotenv
import os

load_dotenv()
ftp_host = os.getenv('FTP_HOST')
db_password = os.getenv('POSTGRES_PASSWORD')
```

### 7. psycopg2-binary 2.9.9

**Rôle** : Version binaire de psycopg2

**Avantages** :

-   **Installation simplifiée** : Pas de compilation requise
-   **Compatibilité** : Fonctionne sur tous les systèmes
-   **Performance** : Même performance que psycopg2
-   **Déploiement** : Facilite le déploiement en conteneur

### 8. pysftp 0.2.9

**Rôle** : Client SFTP pour Python

**Fonctionnalités** :

-   **Transfert de fichiers** : Upload/download sécurisé
-   **Authentification** : Clés SSH et mots de passe
-   **Gestion des erreurs** : Retry automatique et gestion des timeouts
-   **Compression** : Support de la compression des données

**Utilisation dans le projet** :

```python
# Connexion SFTP (alternative à FTP)
import pysftp
with pysftp.Connection('host', username='user', password='pass') as sftp:
    sftp.get('remote_file.log', 'local_file.log')
```

### 9. mysql-connector-python 8.2.0

**Rôle** : Connecteur MySQL officiel Oracle

**Avantages** :

-   **Support officiel** : Maintenu par Oracle
-   **Performance** : Optimisé pour les applications Python
-   **Fonctionnalités complètes** : Support de toutes les fonctionnalités MySQL
-   **Sécurité** : Support SSL/TLS et authentification avancée

## Gestion des Versions

### Stratégie de Versioning :

-   **Versions fixes** : Évite les incompatibilités
-   **Mise à jour contrôlée** : Tests avant déploiement
-   **Sécurité** : Corrections de vulnérabilités
-   **Stabilité** : Versions LTS quand possible

### Compatibilité :

-   **Python 3.9** : Toutes les dépendances compatibles
-   **Docker** : Optimisé pour les conteneurs
-   **Cross-platform** : Fonctionne sur Linux, Windows, macOS

## Sécurité

### Vulnérabilités Potentielles :

-   **psycopg2** : Mise à jour régulière recommandée
-   **pandas** : Attention aux injections SQL via les données
-   **pysftp** : Utilisation de connexions sécurisées

### Bonnes Pratiques :

-   **Variables d'environnement** : Pas de secrets en dur
-   **Connexions sécurisées** : SSL/TLS activé
-   **Permissions minimales** : Principe du moindre privilège

## Performance

### Optimisations :

-   **psycopg2-binary** : Installation plus rapide
-   **pandas** : Utilisation de NumPy en arrière-plan
-   **APScheduler** : Exécution asynchrone des tâches
-   **Pool de connexions** : Réutilisation des connexions DB

### Monitoring :

-   **Logs détaillés** : Traçabilité des opérations
-   **Métriques** : Temps d'exécution et taux d'erreur
-   **Alertes** : Notification en cas de problème

## Maintenance

### Mise à Jour :

-   **Vérification mensuelle** : Nouvelles versions disponibles
-   **Tests de régression** : Validation avant déploiement
-   **Documentation** : Changelog des modifications

### Support :

-   **Communauté active** : Toutes les bibliothèques bien maintenues
-   **Documentation** : Guides et exemples disponibles
-   **Stack Overflow** : Nombreuses ressources disponibles

## Intégration avec l'Architecture

### Rôle dans le Système :

1. **Collecte de données** : FTP et MySQL
2. **Traitement** : Pandas pour l'analyse
3. **Stockage** : PostgreSQL via psycopg2
4. **Planification** : APScheduler pour l'automatisation
5. **Configuration** : python-dotenv pour la flexibilité

Cette configuration de dépendances permet de créer un système de data engineering robuste, sécurisé et performant, capable de gérer des flux de données complexes entre différents systèmes.
