# Rapport Technique - Service de Synchronisation MySQL (mysql_sync_service.py)

## Vue d'ensemble

Le service `mysql_sync_service.py` est un composant ETL (Extract, Transform, Load) qui synchronise les données métier des commandes de volets roulants depuis une base de données MySQL legacy vers PostgreSQL. Ce service extrait les commandes planifiées avec des volets roulants et les transforme en données structurées pour l'analyse.

## Architecture du Service

### 1. Classe MySQLSyncService

**Rôle principal** : Orchestrateur de la synchronisation de données entre systèmes

**Responsabilités** :

-   Connexion aux bases de données (MySQL source, PostgreSQL destination)
-   Extraction des données métier
-   Transformation et validation des données
-   Chargement en base de données cible

### 2. Configuration et Initialisation

```python
def __init__(self):
    # Configuration MySQL
    self.mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'mysql_db'),
        'user': os.getenv('MYSQL_USER'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'database': os.getenv('MYSQL_DB'),
        'port': int(os.getenv('MYSQL_PORT', '3306'))
    }

    # Configuration PostgreSQL
    self.pg_config = {
        'dbname': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST')
    }
```

**Avantages** :

-   **Configuration externalisée** : Variables d'environnement
-   **Valeurs par défaut** : Configuration robuste
-   **Séparation des responsabilités** : MySQL source, PostgreSQL destination

## Gestion des Connexions

### 1. Connexion MySQL

```python
def connect_mysql(self):
    try:
        return mysql.connector.connect(**self.mysql_config)
    except mysql.connector.Error as e:
        logger.error(f"Erreur de connexion MySQL: {e}")
        raise
```

**Caractéristiques** :

-   **Connecteur officiel** : mysql-connector-python d'Oracle
-   **Gestion d'erreurs** : Exceptions spécifiques MySQL
-   **Performance** : Optimisé pour les applications Python

### 2. Connexion PostgreSQL

```python
def connect_postgres(self):
    try:
        return psycopg2.connect(**self.pg_config)
    except psycopg2.Error as e:
        logger.error(f"Erreur de connexion PostgreSQL: {e}")
        raise
```

**Caractéristiques** :

-   **Connecteur psycopg2** : Performant et fiable
-   **Gestion d'erreurs** : Exceptions spécifiques PostgreSQL
-   **Transactions** : Support complet des transactions

## Structure de la Base de Données

### 1. Table PostgreSQL de Destination

```sql
CREATE TABLE IF NOT EXISTS commandes_volets (
    id_commande VARCHAR(32) PRIMARY KEY,
    numero_commande INTEGER NOT NULL,
    extension VARCHAR(5),
    statut VARCHAR(50),
    affaire VARCHAR(100),
    date_modification TIMESTAMP,
    code_accessoire VARCHAR(20),
    description_accessoire TEXT,
    numero_operation VARCHAR(20),
    description_operation TEXT,
    date_synchronisation TIMESTAMP
);
```

**Structure optimisée** :

-   **Clé primaire** : ID unique de la commande
-   **Données métier** : Informations essentielles des commandes
-   **Traçabilité** : Date de synchronisation
-   **Flexibilité** : Champs optionnels pour l'évolution

### 2. Tables MySQL Sources

**Tables utilisées** :

-   `a_kopf` : Informations principales des commandes
-   `a_logbuch` : Logs et historique des commandes
-   `p_zubeh` : Accessoires et composants
-   `a_vorgang` : Événements et opérations

## Extraction des Données

### 1. Requête Complexe d'Extraction

```python
def get_commandes_with_volets(self):
    query = """
    SELECT DISTINCT
        k.id,
        k.aunummer as numero_commande,
        k.aualpha as extension,
        k.aufstatus as statut,
        k.kommission as affaire,
        l.datum as date_modification,
        z.zcode as code_accessoire,
        z.text as description_accessoire,
        v.nummer as numero_operation,
        v.bezeichnung as description_operation,
        l.notiz as notiz
    FROM a_kopf k
    JOIN a_logbuch l ON l.id_a_kopf = k.id
    JOIN p_zubeh z ON z.id_a_kopf = k.id
    LEFT JOIN a_vorgang v ON v.id_a_kopf = k.id
    WHERE (z.zcode LIKE 'VR%' OR z.zcode LIKE 'SOP%' OR z.zcode LIKE 'S P%')
    AND (l.notiz LIKE '%cde Planifiée%' OR l.notiz LIKE '%cde PlanifiÃ©e%')
    ORDER BY k.aunummer;
    """
```

**Fonctionnalités de la requête** :

-   **Jointures multiples** : 4 tables liées
-   **Filtrage intelligent** : Volets roulants et commandes planifiées
-   **Gestion d'encodage** : Support des caractères spéciaux
-   **Tri optimisé** : Par numéro de commande

### 2. Filtrage des Données

**Critères de sélection** :

-   **Codes d'accessoires** : `VR%` (volets roulants), `SOP%` (coffres standard), `S P%` (coffres sur mesure)
-   **Statut des commandes** : "Planifiée" (avec gestion d'encodage)
-   **Données complètes** : Jointure avec tous les détails

### 3. Gestion des Encodages

```python
# Gestion des problèmes d'encodage dans les notes
AND (l.notiz LIKE '%cde Planifiée%' OR l.notiz LIKE '%cde PlanifiÃ©e%')
```

**Problèmes résolus** :

-   **Encodage UTF-8** : Caractères spéciaux mal encodés
-   **Compatibilité** : Support de différents encodages
-   **Robustesse** : Requête fonctionne malgré les problèmes d'encodage

## Transformation des Données

### 1. Mapping des Champs

```python
def insert_into_postgres(self, commandes):
    insert_query = """
    INSERT INTO commandes_volets (
        id_commande,
        numero_commande,
        extension,
        statut,
        affaire,
        date_modification,
        code_accessoire,
        description_accessoire,
        numero_operation,
        description_operation,
        date_synchronisation
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id_commande) DO UPDATE SET
        numero_commande = EXCLUDED.numero_commande,
        extension = EXCLUDED.extension,
        statut = EXCLUDED.statut,
        affaire = EXCLUDED.affaire,
        date_modification = EXCLUDED.date_modification,
        code_accessoire = EXCLUDED.code_accessoire,
        description_accessoire = EXCLUDED.description_accessoire,
        numero_operation = EXCLUDED.numero_operation,
        description_operation = EXCLUDED.description_operation,
        date_synchronisation = CURRENT_TIMESTAMP
    """
```

**Fonctionnalités** :

-   **Upsert** : Insert ou Update selon l'existence
-   **Timestamp automatique** : Date de synchronisation
-   **Gestion des conflits** : Évite les doublons

### 2. Validation des Données

**Contrôles appliqués** :

-   **Types de données** : Conversion automatique
-   **Valeurs nulles** : Gestion des champs optionnels
-   **Intégrité** : Vérification des contraintes

## Debugging et Monitoring

### 1. Fonction de Debug

```python
def debug_tables(self):
    # Vérification du contenu des tables
    # Test des jointures
    # Validation des données
    # Logs détaillés pour le debugging
```

**Fonctionnalités de debug** :

-   **Inspection des tables** : Contenu et structure
-   **Test des jointures** : Validation des relations
-   **Logs détaillés** : Traçabilité complète

### 2. Logging Avancé

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mysql_sync.log'),
        logging.StreamHandler()
    ]
)
```

**Avantages** :

-   **Logs fichier** : Persistance pour l'analyse
-   **Logs console** : Debugging en temps réel
-   **Format structuré** : Timestamp et niveaux

## Orchestration du Processus

### 1. Méthode Principale de Synchronisation

```python
def sync(self):
    try:
        # 1. Récupération des données depuis MySQL
        commandes = self.get_commandes_with_volets()

        # 2. Insertion en PostgreSQL
        self.insert_into_postgres(commandes)

        # 3. Logs de succès
        logger.info(f"Synchronisation terminée: {len(commandes)} commandes traitées")

    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation: {e}")
        raise
```

### 2. Gestion du Cycle de Vie

**Étapes du processus** :

1. **Connexion** : Établissement des connexions
2. **Extraction** : Récupération des données MySQL
3. **Transformation** : Mapping et validation
4. **Chargement** : Insertion en PostgreSQL
5. **Validation** : Vérification des résultats
6. **Fermeture** : Libération des ressources

## Gestion des Erreurs

### 1. Mécanismes de Récupération

-   **Reconnexion automatique** : En cas de perte de connexion
-   **Retry intelligent** : Tentatives multiples
-   **Rollback automatique** : En cas d'erreur de transaction

### 2. Types d'Erreurs Gérées

-   **Erreurs de connexion** : MySQL et PostgreSQL
-   **Erreurs de requête** : SQL malformé ou données invalides
-   **Erreurs de contrainte** : Violations d'intégrité
-   **Erreurs d'encodage** : Caractères spéciaux

## Performance et Optimisations

### 1. Optimisations Appliquées

-   **Requête optimisée** : Index et jointures efficaces
-   **Batch processing** : Traitement par lots
-   **Connexions persistantes** : Réutilisation des connexions
-   **Transactions** : Atomicité des opérations

### 2. Métriques de Performance

-   **Temps de synchronisation** : Mesurable par exécution
-   **Nombre de commandes** : Volume traité
-   **Taux de succès** : Pourcentage de réussite
-   **Utilisation mémoire** : Optimisée

## Sécurité

### 1. Bonnes Pratiques

-   **Variables d'environnement** : Pas de secrets en dur
-   **Connexions sécurisées** : SSL/TLS si disponible
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

-   **Exécution périodique** : Toutes les 15 minutes
-   **Décalage temporel** : Évite la concurrence avec FTP
-   **Gestion des erreurs** : Retry automatique

## Cas d'Usage Métier

### 1. Migration de Données

-   **Système legacy** : MySQL vers PostgreSQL
-   **Données métier** : Commandes de volets roulants
-   **Traçabilité** : Historique des synchronisations

### 2. Intégration de Systèmes

-   **ETL** : Extraction, Transformation, Loading
-   **Data Warehouse** : Stockage structuré
-   **Analytics** : Analyse des commandes

### 3. Monitoring Opérationnel

-   **Suivi des commandes** : État et progression
-   **Métriques de production** : Volumes et tendances
-   **Alertes** : Détection des anomalies

## Avantages de cette Architecture

1. **Robustesse** : Gestion d'erreurs complète
2. **Performance** : Optimisations multiples
3. **Observabilité** : Logs détaillés et monitoring
4. **Maintenabilité** : Code modulaire et bien structuré
5. **Sécurité** : Bonnes pratiques appliquées
6. **Scalabilité** : Peut traiter de gros volumes

## Évolutions Possibles

### 1. Améliorations Techniques

-   **Incremental sync** : Synchronisation différentielle
-   **Real-time sync** : Synchronisation en temps réel
-   **Data validation** : Validation avancée des données
-   **Performance monitoring** : Métriques détaillées

### 2. Fonctionnalités Métier

-   **Filtres avancés** : Critères de sélection complexes
-   **Transformations** : Calculs métier supplémentaires
-   **Notifications** : Alertes en cas de problème
-   **Reporting** : Rapports de synchronisation

Ce service représente une solution ETL complète et robuste pour la synchronisation de données entre systèmes hétérogènes, combinant performance, sécurité et observabilité pour un système de production fiable.
