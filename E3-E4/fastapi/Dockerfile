FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer le dossier pour les uploads
RUN mkdir -p uploads static templates

# Exposer le port
EXPOSE 8000

# Commande pour démarrer l'application
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# Commande par défaut: appliquer les migrations puis démarrer l'app
CMD ["/bin/sh", "-c", "alembic upgrade head && uvicorn app:app --host 0.0.0.0 --port 8000"]