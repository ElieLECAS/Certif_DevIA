# Rapport de Projet – Certification Développeur IA orienté Data Ingénierie

**Projet E1 – Gestion et synchronisation de données industrielles**

---

## Présentation du projet et contexte (C1)

Le projet E1 vise à automatiser la collecte, l’agrégation, la synchronisation et l’exploitation de données de commandes industrielles (volets roulants, fenêtres, etc.) issues de plusieurs sources hétérogènes :

-   **Fichiers de logs machines** déposés sur un serveur FTP par des centres d’usinage,
-   **Base de données MySQL** legacy contenant l’historique métier,
-   **Stockage cible PostgreSQL** pour l’analyse et l’exploitation moderne des données.

L’architecture s’appuie sur des microservices conteneurisés (Docker Compose) orchestrant :

-   Un serveur FTP (collecte des logs),
-   Une base MySQL (données legacy),
-   Une base PostgreSQL (stockage cible),
-   Un service de synchronisation (Python) pour l’ETL,
-   Une API (FastAPI) pour l’exposition des données (structure présente, mais non détaillée ici).

Le projet est versionné sur Git, chaque composant est documenté, et la configuration est externalisée via des variables d’environnement.

---

## C1. Automatiser l’extraction de données

### Spécifications techniques

-   **Technologies** : Python 3.9, Docker, Docker Compose, PostgreSQL, MySQL, FTP, SQLAlchemy, pandas, APScheduler.
-   **Services externes** : FTP (fauria/vsftpd), MySQL, PostgreSQL.
-   **Scripts** : Extraction des logs FTP (`ftp_log_service.py`), synchronisation MySQL (`mysql_sync_service.py`).
-   **Orchestration** : Docker Compose, cron pour la planification.

### Extraction automatisée

-   **Script d’extraction FTP** :
    -   Se connecte au serveur FTP, télécharge les fichiers de logs, les analyse, extrait les métriques de production, et stocke les résultats dans PostgreSQL.
    -   Gestion des erreurs, logs détaillés, suppression des fichiers traités si configuré.
-   **Script de synchronisation MySQL** :
    -   Se connecte à la base MySQL, extrait les commandes planifiées avec volets roulants, les transforme et les insère dans PostgreSQL.
    -   Gestion des encodages, logs détaillés, upsert pour éviter les doublons.

### Dépôt Git

-   Tous les scripts, Dockerfile, fichiers de configuration et documentation sont versionnés dans le dépôt Git du projet.

---

## C2. Développer des requêtes SQL d’extraction

-   **Requêtes SQL** :
    -   Les scripts Python utilisent des requêtes SQL complexes pour extraire les données pertinentes de MySQL (jointures entre `a_kopf`, `a_logbuch`, `p_zubeh`, `a_vorgang`).
    -   Les requêtes filtrent les commandes planifiées, les accessoires de type volets roulants, et gèrent les problèmes d’encodage.
-   **Documentation** :
    -   Les requêtes sont commentées dans le code, avec explication des critères de sélection et des jointures.
-   **Optimisations** :
    -   Utilisation d’index sur les colonnes de filtrage (`aufstatus`, `zcode`, etc.) dans le script d’initialisation MySQL (`init.sql`).

---

## C3. Développer des règles d’agrégation et d’homogénéisation

-   **Agrégation** :
    -   Le script FTP agrège les métriques de production par session (nombre de pièces, temps de production, taux d’occupation, etc.).
    -   Le script MySQL agrège et normalise les données issues de plusieurs tables pour un stockage homogène dans PostgreSQL.
-   **Homogénéisation** :
    -   Les formats de données sont harmonisés lors de l’insertion dans PostgreSQL (types, encodages, structure).
-   **Documentation** :
    -   Les scripts sont documentés, les dépendances et enchaînements logiques sont explicités dans les rapports markdown.

---

## C4. Créer une base de données conforme (RGPD, modèles, import)

-   **Modélisation** :
    -   La structure de la base MySQL est détaillée dans `init.sql` (tables, clés étrangères, index).
    -   La base PostgreSQL cible est créée dynamiquement par les scripts Python (tables de production, commandes, etc.).
-   **Import** :
    -   Le script MySQL permet l’import automatisé des données legacy dans PostgreSQL.
-   **Documentation** :
    -   Les scripts d’installation et d’import sont versionnés et documentés.
-   **RGPD** :
    -   Les procédures de tri et de gestion des données personnelles ne sont pas explicitement présentes dans le code, mais la structure permet leur ajout (pas de traitement automatisé RGPD dans le code actuel).

---

## C5. Développer une API REST pour l’exploitation des données

-   **API FastAPI** :
    -   Présente dans la structure du projet (`/api`), mais la documentation et l’implémentation détaillée ne sont pas incluses dans les fichiers analysés.
    -   L’architecture prévoit l’exposition des données via une API REST, conforme aux standards modernes (OpenAPI).
-   **Sécurité** :
    -   Les règles d’authentification/autorisation ne sont pas détaillées dans le code fourni.
-   **Documentation** :
    -   La documentation technique de l’API n’est pas incluse dans le projet actuel.

---

## Synthèse par compétence du référentiel

| Compétence | Réalisation dans le projet                                                                            |
| ---------- | ----------------------------------------------------------------------------------------------------- |
| **C1**     | Extraction automatisée depuis FTP et MySQL, orchestration Docker, scripts versionnés, logs détaillés. |
| **C2**     | Requêtes SQL complexes, documentation dans le code, index pour optimisation.                          |
| **C3**     | Agrégation et homogénéisation des données, scripts documentés, gestion des formats.                   |
| **C4**     | Modélisation des bases, import automatisé, documentation, structure extensible pour conformité RGPD.  |
| **C5**     | Structure API REST présente, mais non détaillée dans le code fourni.                                  |

---

## Conclusion

Le projet E1 répond à l’essentiel des exigences du référentiel pour un projet de data engineering :

-   **Automatisation** de la collecte et de la synchronisation des données,
-   **Traitement** et **agrégation** multi-sources,
-   **Stockage** structuré et optimisé,
-   **Orchestration** moderne (Docker, cron),
-   **Documentation** technique exhaustive (rapports markdown, scripts commentés).

Les points d’amélioration concernent principalement la documentation et l’implémentation détaillée de l’API REST, ainsi que la formalisation des procédures RGPD.

---

**Annexes**

-   Voir les rapports techniques détaillés pour chaque composant dans le dossier du projet (`RAPPORT_*.md`).
-   Voir le script d’initialisation SQL pour la structure complète de la base de données legacy.
-   Voir le docker-compose pour l’architecture d’orchestration.

---

Ce rapport est strictement basé sur les éléments présents dans le projet E1 et respecte le référentiel de la certification.
