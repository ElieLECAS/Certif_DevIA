FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY app.py .
COPY templates/ ./templates/

# Exposer le port
EXPOSE 5000

# Variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Commande pour démarrer l'application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"] 