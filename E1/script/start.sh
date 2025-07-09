#!/bin/sh

# Exporter les variables d'environnement pour cron
printenv | grep -v "no_proxy" > /etc/environment

# Créer le fichier crontab avec les variables d'environnement
echo "POSTGRES_HOST=${POSTGRES_HOST}" > /etc/cron.d/ftp_log_cron
echo "POSTGRES_DB=${POSTGRES_DB}" >> /etc/cron.d/ftp_log_cron
echo "POSTGRES_USER=${POSTGRES_USER}" >> /etc/cron.d/ftp_log_cron
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> /etc/cron.d/ftp_log_cron
echo "FTP_HOST=${FTP_HOST}" >> /etc/cron.d/ftp_log_cron
echo "FTP_USER=${FTP_USER}" >> /etc/cron.d/ftp_log_cron
echo "FTP_PASS=${FTP_PASS}" >> /etc/cron.d/ftp_log_cron
echo "DELETE_AFTER_SYNC=${DELETE_AFTER_SYNC}" >> /etc/cron.d/ftp_log_cron

# Ajouter la tâche cron
echo "*/15 * * * * root cd /app && /usr/local/bin/python /app/ftp_log_service.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/ftp_log_cron

# Donner les bonnes permissions
chmod 0644 /etc/cron.d/ftp_log_cron

# Démarrer le service cron
cron

# Afficher les logs en temps réel
tail -f /var/log/cron.log 