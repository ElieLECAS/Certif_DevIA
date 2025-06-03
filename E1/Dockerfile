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
RUN echo "0 8 * * * root python3 /app/script.py >> /app/cron.log 2>&1" > /etc/cron.d/log-parser && \
    chmod 0644 /etc/cron.d/log-parser && \
    crontab /etc/cron.d/log-parser


CMD ["cron", "-f"]
