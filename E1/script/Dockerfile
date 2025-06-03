FROM python:3.11-slim

WORKDIR /app

# Copier d'abord requirements.txt pour optimiser le cache Docker
COPY requirements.txt /app/requirements.txt

# Installer cron et dépendances Python
RUN apt-get update && \
    apt-get install -y cron && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copier les fichiers du service
COPY ftp_log_service.py /app/ftp_log_service.py
COPY script.py /app/script.py

# Rendre le script exécutable
RUN chmod +x /app/script.py

# Créer la tâche cron directement et l'installer
RUN echo "PATH=/usr/local/bin:/usr/bin:/bin" > /etc/cron.d/log-parser && \
    echo "* 8 * * * /usr/local/bin/python3 /app/test_service.py >> /app/cron.log 2>&1" >> /etc/cron.d/log-parser && \
    echo "" >> /etc/cron.d/log-parser && \
    chmod 0644 /etc/cron.d/log-parser && \
    crontab /etc/cron.d/log-parser

# Créer le fichier de log
RUN touch /app/cron.log

CMD ["cron", "-f"]
