#!/bin/sh

# Exporter les variables d'environnement pour cron
printenv | grep -v "no_proxy" > /etc/environment

# Créer le fichier crontab avec les variables d'environnement pour le traitement des logs
echo "POSTGRES_HOST=${POSTGRES_HOST}" > /etc/cron.d/log_processing_cron
echo "POSTGRES_DB=${POSTGRES_DB}" >> /etc/cron.d/log_processing_cron
echo "POSTGRES_USER=${POSTGRES_USER}" >> /etc/cron.d/log_processing_cron
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> /etc/cron.d/log_processing_cron
echo "LOGS_DIRECTORY=${LOGS_DIRECTORY}" >> /etc/cron.d/log_processing_cron
echo "DELETE_AFTER_SYNC=${DELETE_AFTER_SYNC}" >> /etc/cron.d/log_processing_cron

# Créer le fichier crontab avec les variables d'environnement pour MySQL
echo "POSTGRES_HOST=${POSTGRES_HOST}" > /etc/cron.d/mysql_sync_cron
echo "POSTGRES_DB=${POSTGRES_DB}" >> /etc/cron.d/mysql_sync_cron
echo "POSTGRES_USER=${POSTGRES_USER}" >> /etc/cron.d/mysql_sync_cron
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_HOST=${MYSQL_HOST}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_DB=${MYSQL_DB}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_USER=${MYSQL_USER}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_PASSWORD=${MYSQL_PASSWORD}" >> /etc/cron.d/mysql_sync_cron
echo "MYSQL_PORT=${MYSQL_PORT:-3306}" >> /etc/cron.d/mysql_sync_cron

# Ajouter les tâches cron
# Service de traitement des logs : toutes les 15 minutes
echo "*/15 * * * * root cd /app && /usr/local/bin/python /app/ftp_log_service.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/log_processing_cron

# Service MySQL : tous les jours à 9h et 14h
echo "0 9,14 * * * root cd /app && /usr/local/bin/python /app/mysql_sync_service.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/mysql_sync_cron

# Donner les bonnes permissions
chmod 0644 /etc/cron.d/log_processing_cron
chmod 0644 /etc/cron.d/mysql_sync_cron

# Démarrer le service cron
cron

# Exécuter les deux services immédiatement au démarrage, avec un délai entre eux
(cd /app && /usr/local/bin/python /app/ftp_log_service.py >> /var/log/cron.log 2>&1) &
sleep 90
(cd /app && /usr/local/bin/python /app/mysql_sync_service.py >> /var/log/cron.log 2>&1) &

# Afficher les logs en temps réel
tail -f /var/log/cron.log 