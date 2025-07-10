FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip et installation des outils de base
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Vérification de l'installation
CMD ["python", "vanna_ai.py"]
