FROM python:3.11-slim

WORKDIR /app

# Installer cron et dépendances Python
RUN apt-get update && \
    apt-get install -y cron && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean

# Copier les fichiers du parser
COPY main.py /app/main.py
COPY crontab.txt /etc/cron.d/my-cron
COPY requirements.txt /app/requirements.txt

# Appliquer la crontab
RUN chmod 0644 /etc/cron.d/my-cron && \
    crontab /etc/cron.d/my-cron

CMD ["cron", "-f"]
