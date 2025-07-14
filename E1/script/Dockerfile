FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    cron \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Créer le fichier de log pour cron
RUN touch /var/log/cron.log

# Donner les permissions d'exécution au script de démarrage
COPY start.sh /start.sh
# Convertir les fins de ligne Windows vers Unix
RUN dos2unix /start.sh
RUN chmod +x /start.sh

# Créer le dossier pour les fichiers cron
RUN mkdir -p /etc/cron.d

CMD ["/start.sh"]
# CMD ["python", "mysql_sync_service.py"]
