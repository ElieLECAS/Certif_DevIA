# Rapport Technique - Script de Démarrage (start.sh)

## Vue d'ensemble

Le script `start.sh` est le point d'entrée principal du conteneur de synchronisation. Il configure l'environnement, initialise les tâches cron et démarre les services de traitement des données. Ce script orchestre l'exécution des deux services Python : le traitement des logs FTP et la synchronisation MySQL vers PostgreSQL.

## Analyse Détaillée du Script

### 1. Configuration de l'Environnement

```bash
#!/bin/sh
printenv | grep -v "no_proxy" > /etc/environment
```

**Fonctionnalités** :

-   **Shebang** : Utilise le shell par défaut du système
-   **Export des variables** : Toutes les variables d'environnement sont disponibles pour cron
-   **Filtrage** : Exclusion de `no_proxy` pour éviter les conflits

**Avantages** :

-   **Flexibilité** : Variables d'environnement dynamiques
-   **Sécurité** : Pas de secrets en dur dans le script
-   **Maintenabilité** : Configuration externalisée

### 2. Configuration des Tâches Cron FTP

```bash
echo "POSTGRES_HOST=${POSTGRES_HOST}" > /etc/cron.d/ftp_log_cron
echo "POSTGRES_DB=${POSTGRES_DB}" >> /etc/cron.d/ftp_log_cron
echo "POSTGRES_USER=${POSTGRES_USER}" >> /etc/cron.d/ftp_log_cron
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> /etc/cron.d/ftp_log_cron
echo "FTP_HOST=${FTP_HOST}" >> /etc/cron.d/ftp_log_cron
echo "FTP_USER=${FTP_USER}" >> /etc/cron.d/ftp_log_cron
echo "FTP_PASS=${FTP_PASS}" >> /etc/cron.d/ftp_log_cron
echo "DELETE_AFTER_SYNC=${DELETE_AFTER_SYNC}" >> /etc/cron.d/ftp_log_cron
```

**Configuration** :

-   **Variables PostgreSQL** : Connexion à la base de données cible
-   **Variables FTP** : Connexion au serveur FTP source
-   **Paramètres de synchronisation** : Contrôle du comportement

**Sécurité** :

-   **Variables d'environnement** : Pas de secrets en dur
-   **Isolation** : Chaque tâche a ses propres variables

### 3. Configuration des Tâches Cron MySQL

```bash
echo "POSTGRES_HOST=${POSTGRES_HOST}" > /etc/cron.d/mysql_sync_cron
echo "POSTGRES_DB=${POSTGRES_DB}" >> /etc/cron.d/mysql_sync_cron
echo "POSTGRES_USER=${POSTGRES_USER}" >> /etc/cron.d/mysql_sync_cron
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_HOST=${MYSQL_HOST}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_DB=${MYSQL_DB}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_USER=${MYSQL_USER}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_PASSWORD=${MYSQL_PASSWORD}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_PORT=${MYSQL_PORT:-3306}" >> /etc/cron.d/mysql_sync_cron
```

**Configuration** :

-   **Variables PostgreSQL** : Base de données de destination
-   **Variables MySQL** : Base de données source legacy
-   **Port par défaut** : 3306 si non spécifié

### 4. Planification des Tâches

#### Service FTP (Toutes les 5 minutes)

```bash
echo "*/5 * * * * root cd /app && /usr/local/bin/python /app/ftp_log_service.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/ftp_log_cron
```

**Détails** :

-   **Fréquence** : `*/5` = toutes les 5 minutes
-   **Utilisateur** : `root` (nécessaire pour les permissions)
-   **Répertoire** : `cd /app` pour le contexte d'exécution
-   **Logs** : Redirection vers `/var/log/cron.log`
-   **Erreurs** : `2>&1` capture les erreurs et les sorties

#### Service MySQL (Toutes les 15 minutes avec décalage)

```bash
echo "2,17,32,47 * * * * root cd /app && /usr/local/bin/python /app/mysql_sync_service.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/mysql_sync_cron
```

**Détails** :

-   **Fréquence** : `2,17,32,47` = minutes 2, 17, 32, 47 de chaque heure
-   **Décalage** : Évite la concurrence avec le service FTP
-   **Périodicité** : Toutes les 15 minutes avec un décalage de 2 minutes

### 5. Gestion des Permissions

```bash
chmod 0644 /etc/cron.d/ftp_log_cron
chmod 0644 /etc/cron.d/mysql_sync_cron
```

**Permissions** :

-   **0644** : Lecture/écriture pour root, lecture pour groupe et autres
-   **Sécurité** : Permissions minimales nécessaires
-   **Fonctionnalité** : Cron peut lire les fichiers de configuration

### 6. Démarrage du Service Cron

```bash
cron
```

**Fonctionnalités** :

-   **Démarrage** : Service cron en arrière-plan
-   **Persistance** : Continue à fonctionner jusqu'à l'arrêt du conteneur
-   **Monitoring** : Logs disponibles pour le debugging

### 7. Affichage des Logs

```bash
tail -f /var/log/cron.log
```

**Fonctionnalités** :

-   **Temps réel** : `tail -f` suit les nouveaux logs
-   **Debugging** : Visibilité immédiate des exécutions
-   **Monitoring** : Permet de voir les erreurs en temps réel

## Architecture de Planification

### Stratégie de Synchronisation :

#### Service FTP (Haute Fréquence)

-   **Fréquence** : Toutes les 5 minutes
-   **Priorité** : Données en temps réel des machines
-   **Criticité** : Élevée (données de production)

#### Service MySQL (Basse Fréquence)

-   **Fréquence** : Toutes les 15 minutes
-   **Priorité** : Données métier legacy
-   **Criticité** : Moyenne (données de référence)

### Éviter les Conflits :

-   **Décalage temporel** : 2 minutes entre les services
-   **Ressources** : Pas de concurrence sur les bases de données
-   **Logs** : Séparation claire des exécutions

## Gestion des Erreurs

### Mécanismes de Récupération :

-   **Logs détaillés** : Capture de toutes les sorties
-   **Redémarrage automatique** : Cron continue malgré les erreurs
-   **Isolation** : Une erreur n'affecte pas l'autre service

### Monitoring :

-   **Fichier de log** : `/var/log/cron.log`
-   **Temps réel** : `tail -f` pour le debugging
-   **Historique** : Logs persistants pour l'analyse

## Sécurité

### Bonnes Pratiques :

-   **Variables d'environnement** : Pas de secrets en dur
-   **Permissions minimales** : Seules les permissions nécessaires
-   **Isolation** : Chaque tâche dans son propre contexte
-   **Logs sécurisés** : Pas de mots de passe dans les logs

### Risques Atténués :

-   **Injection de commandes** : Variables d'environnement contrôlées
-   **Élévation de privilèges** : Utilisation minimale de root
-   **Fuites d'informations** : Logs filtrés

## Performance

### Optimisations :

-   **Décalage des tâches** : Évite la concurrence
-   **Logs optimisés** : Redirection efficace
-   **Contexte d'exécution** : Répertoire de travail défini

### Monitoring :

-   **Temps d'exécution** : Mesurable via les logs
-   **Fréquence d'erreurs** : Traçable
-   **Utilisation des ressources** : Contrôlable

## Maintenance

### Debugging :

-   **Logs en temps réel** : `tail -f /var/log/cron.log`
-   **Variables d'environnement** : Vérifiables via `/etc/environment`
-   **Configuration cron** : Fichiers dans `/etc/cron.d/`

### Mise à Jour :

-   **Variables d'environnement** : Modification sans redéploiement
-   **Fréquences** : Ajustables via les patterns cron
-   **Services** : Ajout/suppression de tâches possible

## Intégration avec Docker

### Variables d'Environnement :

-   **Docker Compose** : Définies dans `docker-compose.yaml`
-   **Héritage** : Transmises au conteneur
-   **Flexibilité** : Configuration par environnement

### Volumes :

-   **Logs** : Partagés avec l'hôte via `./logs:/app/logs`
-   **Code** : Montage en développement pour les modifications

## Avantages de cette Approche

1. **Robustesse** : Gestion d'erreurs et redémarrage automatique
2. **Observabilité** : Logs détaillés et monitoring en temps réel
3. **Flexibilité** : Configuration via variables d'environnement
4. **Maintenabilité** : Script simple et bien documenté
5. **Sécurité** : Bonnes pratiques de sécurité appliquées
6. **Performance** : Optimisation des ressources et évitement des conflits

Ce script représente une approche mature de l'orchestration de services de data engineering, combinant simplicité, robustesse et observabilité pour un système de production fiable.
