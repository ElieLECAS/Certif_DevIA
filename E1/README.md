# E1 – Gestion des données industrielles

## I. Présentation du Projet

Ce projet a pour objectif d’extraire, transformer et exposer des données de production issues de machines industrielles et du système de commande existant.

Les traitements s’appuient sur plusieurs sources :

-   **Logs de machines** : fichiers `*.LOG` déposés via SFTP dans des dossiers dédiés aux différents centres d’usinage.
-   **Base MySQL métier** : tables simulant le référentiel des commandes de volets roulants.
-   **Base PostgreSQL** : stockage centralisé des données consolidées et exposées à l’API.

**Enjeux techniques :**

-   Automatisation : planification via cron et conteneurs Docker.
-   Conformité RGPD : stockage minimal des données personnelles (identifiants chiffrés, historisation limitée).
-   Performances : nettoyage et normalisation des données avant insertion.
-   API REST : consultation sécurisée des résultats.

---

## II. Extraction et Agrégation des Données (C1, C3)

### Scripts d’extraction

-   `script/ftp_log_service.py`

    -   Parcourt les dossiers de logs (`/app/logs/DEM12`, `DEMALU`, `SU12`).
    -   Analyse chaque fichier pour extraire pièces produites, temps d’attente/arrêt, profils de job.
    -   Écrit les résultats dans PostgreSQL (`psycopg2`).
    -   Journalisation détaillée (`/app/sync_logs/ftp_log_service.log`) et gestion d’exceptions (connexion BD, lecture de fichiers, parsing).

-   `script/mysql_sync_service.py`
    -   Récupère les commandes de volets roulants depuis MySQL à l’aide d’une requête SQL complexe (jointures, filtres, groupement).
    -   Nettoyage via pandas : suppression des doublons, tri par priorité (`gestion_en_stock`).
    -   Insère les données consolidées dans `commandes_volets_roulants` (PostgreSQL).
    -   Logs : `/app/sync_logs/mysql_sync.log`.

### Règles d’agrégation

-   Nettoyage : suppression des caractères nuls, filtrage des lignes invalides, gestion des encodages.
-   Normalisation : conversion des dates/heures au format ISO, calcul des durées en heures.
-   Formatage : regroupement par machine, session de production ou numéro de commande.

### Format final

Les données sont stockées dans PostgreSQL, principalement dans les tables :

-   `centre_usinage`
-   `session_production`
-   `job_profil`
-   `periode_attente`
-   `periode_arret`
-   `piece_production`
-   `commandes_volets_roulants`

---

## III. Requêtes SQL et Préparation des Données (C2)

### Requêtes principales :

-   Création des tables de production et de synchronisation dans PostgreSQL (`CREATE TABLE IF NOT EXISTS …`).
-   Sélection des commandes MySQL :

```sql
SELECT Cde.AuNummer AS numero_commande,
       Cde.AuAlpha AS extension,
       Cde.AufStatus AS status,
       DATE(Logb.Datum) AS date_modification,
       a.ZCode AS coffre,
       CASE WHEN Vorgang.Nummer LIKE '%VR%' THEN 1 ELSE 0 END AS gestion_en_stock
FROM A_Kopf AS Cde
LEFT JOIN A_Logbuch AS Logb ON Cde.ID = Logb.ID_A_Kopf
LEFT JOIN P_Zubeh AS a ON Cde.ID = a.ID_A_Kopf
...
WHERE Logb.Notiz LIKE '%cde Planifiee%'
  AND (Cde.AufStatus LIKE '%Planifiee%' OR ... )
GROUP BY ...
```

-   Optimisation : `GROUP BY`, suppression des doublons (pandas), `TRUNCATE TABLE` avant insertion.

### Outils/langages :

-   `psycopg2` pour PostgreSQL
-   `mysql-connector-python` pour MySQL
-   `pandas` pour l’agrégation
-   `SQLModel` pour l’API

---

## IV. Base de Données (C4)

### Modélisation

-   Conceptuel / Logique / Physique : le schéma PostgreSQL repose sur des entités métiers telles que :
    -   `centre_usinage` → `session_production` → `job_profil` / `periode_attente` / `periode_arret` / `piece_production`
    -   `commandes_volets_roulants`
-   Modèles définis dans `api/models.py`.

### Respect du RGPD

-   Données personnelles minimales (email, nom d’utilisateur pour l’authentification).
-   Hashage des mots de passe (`passlib`).
-   Possibilité de purger ou d’anonymiser les données à la source (les scripts d’extraction ne conservent que les champs nécessaires).

### Import des données

-   Scripts :
    -   `ftp_log_service.py` et `mysql_sync_service.py`.
    -   Planification via `start.sh` :
        -   `ftp_log_service.py` quotidien à 11 h
        -   `mysql_sync_service.py` quotidien à 9 h et 14 h
-   Dépendances : listées dans `script/requirements.txt`.
-   Exécution manuelle :

```bash
python script/ftp_log_service.py     # Traitement des logs
python script/mysql_sync_service.py  # Synchronisation MySQL -> PostgreSQL
```

---

## V. API REST (C5)

### Architecture

-   Application FastAPI contenue dans `api/main.py`.
-   Connexion à PostgreSQL via `api/database.py`.
-   Modèles et schémas définis dans `api/models.py` et `api/schemas.py`.

### Endpoints principaux

| Méthode & Route               | Description                               |
| ----------------------------- | ----------------------------------------- |
| POST /token                   | Authentification OAuth2, retour d’un JWT  |
| POST /users/                  | Création d’un utilisateur                 |
| GET /centres/, POST /centres/ | Gestion des centres d’usinage             |
| GET /sessions/                | Liste des sessions de production          |
| POST /commandes-volets/       | Insertion d’une commande de volet roulant |
| GET /commandes-volets/        | Consultation des commandes synchronisées  |

#### Exemples :

```bash
# Obtenir un token
curl -X POST -d "username=demo&password=demo" http://localhost:8000/token

# Lister les centres d'usinage
curl -H "Authorization: Bearer <JWT>" http://localhost:8000/centres/
```

### Authentification

-   OAuth2 Password Flow avec JWT (`jose`, `passlib`).
-   Utilisateurs stockés dans la table `user`.
-   Configuration de la clé secrète dans `.env` (`SECRET_KEY`).

### Démarrage rapide

1. Cloner le dépôt puis copier et adapter `.env_exemple` → `.env`.
2. Lancer l’environnement (PostgreSQL, MySQL, SFTP, services, API) :

```bash
docker-compose up --build
```

3. Accéder à l’API : [http://localhost:8000/docs](http://localhost:8000/docs)

### Liens utiles

-   `docker-compose.yaml` – orchestration complète
-   `init.sql` – création et jeu de données MySQL
-   `queries.ipynb` – exemples de requêtes SQL
-   `api/README.md` – documentation dédiée à l’API

---

## Licence

Projet à usage pédagogique. Adapter la licence selon votre organisation.
