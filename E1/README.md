# Système de Traitement des Logs FTP vers PostgreSQL

Ce projet implémente un système automatisé pour récupérer des fichiers LOG depuis un serveur FTP, les parser et stocker les données analysées dans une base de données PostgreSQL.

## Architecture

Le système est composé de 3 services Docker :

1. **FTP Server** (`ftp`) - Serveur FTP pour recevoir les fichiers LOG
2. **PostgreSQL** (`db`) - Base de données pour stocker les données analysées
3. **Parser** (`parser`) - Service qui traite les fichiers LOG

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SERVEUR FTP   │    │     PARSER      │    │   POSTGRESQL    │
│                 │    │                 │    │                 │
│ Reçoit les      │───▶│ Traite les      │───▶│ Stocke les      │
│ fichiers LOG    │    │ logs et calcule │    │ résultats       │
│ des machines    │    │ les métriques   │    │ d'analyse       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Structure des Dossiers FTP

Le système explore automatiquement les sous-dossiers du FTP pour traiter les fichiers LOG par type de centre d'usinage :

```
/home/vsftpd/
├── DEM12 (PVC)/          # Fichiers LOG pour centres PVC
│   ├── 20250528.LOG
│   ├── 20250527.LOG
│   └── ...
├── DEMALU (ALU)/         # Fichiers LOG pour centres ALU
│   ├── 20250528.LOG
│   ├── 20250527.LOG
│   └── ...
└── SU12 (HYBRIDE)/       # Fichiers LOG pour centres HYBRIDE
    ├── 20250528.LOG
    ├── 20250527.LOG
    └── ...
```

## Fichiers Principaux

-   `ftp_log_service.py` - Service principal qui gère la récupération FTP, le parsing et le stockage
-   `script.py` - Script d'entrée exécuté par cron
-   `service.py` - Service Django original (pour référence)
-   `parser.py` - Parser original (pour référence)
-   `test_service.py` - Script de test pour vérifier le fonctionnement

## Configuration

### Variables d'Environnement

Le système utilise les variables d'environnement suivantes :

```bash
# Configuration FTP
FTP_HOST=ftp
FTP_USER=monuser
FTP_PASS=motdepasse

# Configuration PostgreSQL
DB_HOST=db
DB_NAME=logsdb
DB_USER=user
DB_PASS=password
```

### Mapping des Dossiers CU

Le service est configuré pour reconnaître automatiquement les types de centres d'usinage :

```python
cu_directories = {
    'DEM12 (PVC)': 'PVC',
    'DEMALU (ALU)': 'ALU',
    'SU12 (HYBRIDE)': 'HYBRIDE'
}
```

### Structure de la Base de Données

Le système crée automatiquement les tables suivantes :

-   `centre_usinage` - Informations sur les centres d'usinage
-   `session_production` - Sessions de production avec métriques
-   `job_profil` - Profils des jobs traités
-   `periode_attente` - Périodes d'attente machine
-   `periode_arret` - Périodes d'arrêt volontaire
-   `piece_production` - Pièces produites

## Utilisation

### Démarrage avec Docker Compose

```bash
# Construire et démarrer tous les services
docker-compose up -d

# Voir les logs du parser
docker-compose logs -f parser

# Arrêter les services
docker-compose down
```

### Test Manuel

```bash
# Tester la connexion et le fonctionnement
docker-compose exec parser python3 /app/script/test_service.py

# Exécuter le traitement manuellement
docker-compose exec parser python3 /app/script/script.py
```

### Planification Automatique

Le script est configuré pour s'exécuter automatiquement tous les jours à 8h00 via cron.
La tâche cron est définie directement dans le Dockerfile.

## Format des Fichiers LOG

Le système attend des fichiers avec l'extension `.LOG` contenant des lignes au format :

```
YYYYMMDD HH:MM:SS|@EventType: Details
```

Exemples d'événements supportés :

-   `StukUitgevoerd` - Pièce produite
-   `MachineWait` - Attente machine
-   `MachineStop` / `MachineStart` - Arrêt/Démarrage machine
-   `JobProfiel` - Profil de job (R:ref L:longueur C:couleur)

## Traitement par Type de Centre d'Usinage

Le système traite automatiquement chaque dossier selon son type :

-   **DEM12 (PVC)** → Type `PVC`
-   **DEMALU (ALU)** → Type `ALU`
-   **SU12 (HYBRIDE)** → Type `HYBRIDE`

Chaque fichier LOG est traité avec le contexte de son type de centre d'usinage, permettant une analyse spécialisée.

## Métriques Calculées

Pour chaque session de production, le système calcule :

-   **Temps de production** - Durée entre première et dernière pièce
-   **Temps d'attente** - Temps cumulé des attentes machine
-   **Temps d'arrêt volontaire** - Temps entre MachineStop et MachineStart
-   **Taux d'occupation** - Pourcentage de temps productif
-   **Taux d'attente** - Pourcentage de temps en attente
-   **Taux d'arrêt** - Pourcentage de temps d'arrêt volontaire

## Logs et Monitoring

-   Les logs du cron sont stockés dans `/app/cron.log`
-   Les logs du service sont affichés sur stdout/stderr
-   Utiliser `docker-compose logs parser` pour voir les logs en temps réel

### Exemple de Logs de Traitement

```
=== Traitement du dossier DEM12 (PVC) (Type: PVC) ===
Trouvé 45 fichiers LOG dans DEM12 (PVC)
Traitement de DEM12 (PVC)/20250528.LOG...
✅ DEM12 (PVC)/20250528.LOG traité avec succès
...
Dossier DEM12 (PVC) terminé: 45 fichiers traités, 0 erreurs

=== Traitement du dossier DEMALU (ALU) (Type: ALU) ===
Trouvé 38 fichiers LOG dans DEMALU (ALU)
...

=== TRAITEMENT GLOBAL TERMINÉ ===
Total: 125 fichiers traités, 2 erreurs
```

## Dépannage

### Problèmes de Connexion FTP

```bash
# Vérifier que le serveur FTP est accessible
docker-compose exec parser ping ftp

# Lister les dossiers disponibles
docker-compose exec parser python3 -c "
import ftplib
ftp = ftplib.FTP('ftp')
ftp.login('monuser', 'motdepasse')
print('Dossiers:', ftp.nlst())
ftp.quit()
"
```

### Problèmes de Base de Données

```bash
# Vérifier la connexion PostgreSQL
docker-compose exec parser python3 -c "from ftp_log_service import FTPLogService; s=FTPLogService(); s.connect_db(); print('OK')"
```

### Fichiers LOG Non Traités

-   Vérifier que les dossiers sont nommés exactement : `DEM12 (PVC)`, `DEMALU (ALU)`, `SU12 (HYBRIDE)`
-   Vérifier le format des fichiers LOG
-   Vérifier les permissions FTP
-   Consulter les logs pour les erreurs de parsing

### Ajouter un Nouveau Type de Centre d'Usinage

1. Modifier le dictionnaire `cu_directories` dans `ftp_log_service.py`
2. Créer le dossier correspondant sur le serveur FTP
3. Reconstruire l'image Docker

## Développement

### Tests Complets

Le script de test vérifie maintenant :

```bash
python3 test_service.py
```

-   Connexion base de données
-   Connexion FTP
-   Exploration des dossiers CU
-   Traitement d'un fichier unique
-   Processus complet

### Ajouter de Nouveaux Types d'Événements

Modifier la méthode `analyze_machine_performance` dans `ftp_log_service.py` pour supporter de nouveaux types d'événements.

### Modifier la Planification

La tâche cron est définie directement dans le Dockerfile :

```dockerfile
RUN echo "0 8 * * * root python3 /app/script.py >> /app/cron.log 2>&1" > /etc/cron.d/log-parser
```

Pour modifier l'horaire, éditer cette ligne et reconstruire l'image.

