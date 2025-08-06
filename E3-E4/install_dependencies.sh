#!/bin/bash

# Script d'installation des dépendances pour le projet FastAPI
# Ce script gère les conflits de dépendances et installe les packages de manière robuste

set -e  # Arrêter en cas d'erreur

echo "🔧 Installation des dépendances FastAPI..."

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Mettre à jour pip
echo "📦 Mise à jour de pip..."
python3 -m pip install --upgrade pip

# Installer les dépendances de base d'abord
echo "📦 Installation des dépendances de base..."
pip install --no-cache-dir -r fastapi/requirements.txt

# Installer les dépendances de développement si demandé
if [ "$1" = "--dev" ]; then
    echo "📦 Installation des dépendances de développement..."
    pip install --no-cache-dir -r fastapi/requirements-dev.txt
fi

echo "✅ Installation terminée avec succès!"

# Vérifier l'installation
echo "🔍 Vérification de l'installation..."
python3 -c "import fastapi; print('✅ FastAPI installé')"
python3 -c "import prometheus_client; print('✅ Prometheus client installé')"
python3 -c "import psutil; print('✅ psutil installé')"

echo "🎉 Toutes les dépendances sont installées et fonctionnelles!"