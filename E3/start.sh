#!/bin/bash

# Attendre que la base de données soit prête
echo "Attente de la base de données PostgreSQL..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if nc -z db 5432; then
        echo "✅ Base de données PostgreSQL prête !"
        break
    fi
    echo "⏳ Tentative $((attempt + 1))/$max_attempts - Attente de PostgreSQL..."
    sleep 3
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Impossible de se connecter à PostgreSQL après $max_attempts tentatives"
    exit 1
fi

# Attendre plus longtemps pour que PostgreSQL soit complètement initialisé
echo "⏳ Attente de l'initialisation complète de PostgreSQL..."
sleep 10

# Tester la connexion avec psql
echo "🔍 Test de connexion à PostgreSQL..."
max_db_attempts=20
db_attempt=0

while [ $db_attempt -lt $max_db_attempts ]; do
    if PGPASSWORD=password psql -h db -U postgres -d chatbot_sav -c "SELECT 1;" > /dev/null 2>&1; then
        echo "✅ Connexion PostgreSQL réussie !"
        break
    fi
    echo "⏳ Tentative $((db_attempt + 1))/$max_db_attempts - Test de connexion DB..."
    sleep 2
    db_attempt=$((db_attempt + 1))
done

if [ $db_attempt -eq $max_db_attempts ]; then
    echo "❌ Impossible de se connecter à la base de données après $max_db_attempts tentatives"
    echo "⚠️  Démarrage de l'application malgré l'erreur..."
fi

# Démarrer l'application FastAPI
echo "🚀 Démarrage de l'application FastAPI..."
uvicorn app:app --host 0.0.0.0 --port 8000 --reload 