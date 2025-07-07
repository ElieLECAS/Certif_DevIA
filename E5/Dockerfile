FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'app et migrations
COPY app/ .
COPY alembic.ini .
COPY alembic/ ./alembic/

EXPOSE 8000

# Ancienne commande avant correction :
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000"] 

# Commande corrigée pour la production :
# CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"] 