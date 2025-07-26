FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    netcat-openbsd \
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

# Rendre le script de démarrage exécutable
RUN chmod +x start.sh

# Exposer le port
EXPOSE 8000

# Commande par défaut
CMD ["./start.sh"] 