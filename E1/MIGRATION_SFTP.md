# Migration de FTP vers SFTP

## Changements effectués

### Services Docker

-   **Service FTP** : Remplacé `fauria/vsftpd` par `atmoz/sftp`
-   **Nom du service** : Changé de `ftp` vers `sftp`
-   **Port** : Changé du port 21 (FTP) vers le port 22 (SFTP/SSH)

### Configuration

-   **Image** : `atmoz/sftp` au lieu de `fauria/vsftpd`
-   **Port** : `22:22` au lieu de `21:21` et `21000-21010:21000-21010`
-   **Variables d'environnement** : Suppression des variables PASV (PASV_ADDRESS, PASV_MIN_PORT, PASV_MAX_PORT)
-   **Configuration utilisateur** : Utilise maintenant le format `command: "${FTP_USER}:${FTP_PASS}:1001:1001:logs"`

### Partage de dossier avec Python

-   **Volume** : `./logs:/home/${FTP_USER}/logs`
-   **Accès** : Le dossier `logs` est maintenant accessible à l'utilisateur SFTP dans `/home/${FTP_USER}/logs`
-   **Permissions** : L'utilisateur SFTP a l'UID/GID 1001:1001 pour la gestion des permissions

### Services dépendants

-   **sync_service** : Mis à jour pour utiliser `FTP_HOST=sftp` au lieu de `FTP_HOST=ftp`

## Utilisation

### Connexion SFTP

```bash
sftp -P 22 sftp_user@localhost
```

### Variables d'environnement nécessaires

```env
SFTP_USER=sftp_user:password123
SFTP_PORT=22
```

### Structure des fichiers

```
./logs/                          # Dossier partagé entre Python et SFTP
├── DEM12/                      # Dossier pour machines DEM12
│   └── *.LOG                   # Fichiers LOG
├── DEMALU/                     # Dossier pour machines DEMALU
│   └── *.LOG
└── SU12/                       # Dossier pour machines SU12
    └── *.LOG
```

## Avantages de SFTP par rapport à FTP

-   **Sécurité** : Chiffrement des données et des authentifications
-   **Simplicité** : Un seul port (22) au lieu de multiples ports
-   **Compatibilité** : Protocole SSH standard
-   **Pas de mode passif** : Plus simple à configurer avec Docker

## Notes techniques

-   L'utilisateur SFTP est créé avec l'UID/GID 1001:1001
-   Le répertoire `logs` est créé automatiquement dans le home de l'utilisateur
-   L'utilisateur est chrooté dans son répertoire home pour la sécurité
-   La structure de dossiers est initialisée automatiquement par le service Python
-   Toutes les fonctionnalités sont centralisées dans `ftp_log_service.py`

## Utilisation du service Python

```bash
# Traitement normal des logs
python ftp_log_service.py

# Initialisation de la structure de dossiers seulement
python ftp_log_service.py init
```
