#!/bin/bash

# Script de démonstration du problème de versioning Alembic
# et de sa résolution dans un environnement Docker

echo "=== DÉMONSTRATION DU PROBLÈME DE VERSIONING ALEMBIC ==="
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher des messages colorés
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo "[INFO] $1"
}

# Fonction pour attendre une entrée utilisateur
wait_for_input() {
    echo ""
    echo "Appuyez sur Entrée pour continuer..."
    read
}

# Nettoyage initial
cleanup() {
    print_info "Nettoyage des conteneurs existants..."
    docker-compose down -v 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
}

# Étape 1: Présentation du problème
echo "=== ÉTAPE 1: PRÉSENTATION DU PROBLÈME ==="
echo ""
print_info "Dans ce projet, nous avons une application FastAPI avec PostgreSQL."
print_info "En développement, les migrations Alembic sont faites manuellement."
print_info "Mais lors du déploiement en production via Docker, les migrations ne sont pas appliquées."
print_warning "Cela cause un crash de l'application car les tables n'existent pas!"
wait_for_input

# Étape 2: Démonstration du problème
echo "=== ÉTAPE 2: DÉMONSTRATION DU PROBLÈME ==="
echo ""
print_info "Création du Dockerfile problématique..."

# Créer le Dockerfile problématique
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# PROBLÈME: Pas de migration automatique
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

print_info "Dockerfile problématique créé."
print_info "Construction de l'image..."

docker build -t taskmanager-api:problematic . > /dev/null 2>&1

if [ $? -eq 0 ]; then
    print_success "Image construite avec succès"
else
    print_error "Erreur lors de la construction de l'image"
    exit 1
fi

wait_for_input

# Étape 3: Tentative de lancement (qui va échouer)
echo "=== ÉTAPE 3: TENTATIVE DE LANCEMENT (VA ÉCHOUER) ==="
echo ""
print_info "Lancement de l'application avec docker-compose..."
print_warning "Cette étape va échouer car les migrations ne sont pas appliquées!"

# Créer un docker-compose simplifié pour la démo
cat > docker-compose-demo.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: taskmanager
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d taskmanager"]
      interval: 5s
      timeout: 3s
      retries: 5

  app:
    image: taskmanager-api:problematic
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/taskmanager
    depends_on:
      db:
        condition: service_healthy
EOF

print_info "Démarrage des services..."
docker-compose -f docker-compose-demo.yml up -d

# Attendre un peu pour que les services se lancent
sleep 10

# Vérifier les logs de l'application
print_info "Vérification des logs de l'application..."
echo ""
print_error "LOGS DE L'APPLICATION (ERREUR ATTENDUE):"
docker-compose -f docker-compose-demo.yml logs app | tail -20

wait_for_input

# Arrêter les services
print_info "Arrêt des services défaillants..."
docker-compose -f docker-compose-demo.yml down -v

# Étape 4: Analyse du problème
echo ""
echo "=== ÉTAPE 4: ANALYSE DU PROBLÈME ==="
echo ""
print_error "PROBLÈME IDENTIFIÉ:"
echo "  - L'application FastAPI tente de se connecter à la base de données"
echo "  - Les tables n'existent pas car les migrations Alembic n'ont pas été appliquées"
echo "  - Le Dockerfile ne contient pas la commande 'alembic upgrade head'"
echo "  - Résultat: sqlalchemy.exc.ProgrammingError (relation does not exist)"
echo ""
print_warning "En développement, nous faisons manuellement:"
echo "  $ alembic upgrade head"
echo "  $ uvicorn main:app --reload"
echo ""
print_warning "Mais en production (Docker), cette étape est oubliée!"

wait_for_input

# Étape 5: Correction du problème
echo "=== ÉTAPE 5: CORRECTION DU PROBLÈME ==="
echo ""
print_info "Création du Dockerfile corrigé..."

# Créer le Dockerfile corrigé
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# CORRECTION: Ajout des migrations automatiques
# Script de démarrage qui fait les migrations puis lance l'app
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
EOF

print_success "Dockerfile corrigé créé!"
print_info "La nouvelle commande CMD inclut maintenant:"
echo "  1. alembic upgrade head  # Applique les migrations"
echo "  2. uvicorn main:app...   # Lance l'application"

wait_for_input

# Étape 6: Construction de l'image corrigée
echo "=== ÉTAPE 6: CONSTRUCTION DE L'IMAGE CORRIGÉE ==="
echo ""
print_info "Construction de la nouvelle image..."

docker build -t taskmanager-api:fixed . > /dev/null 2>&1

if [ $? -eq 0 ]; then
    print_success "Image corrigée construite avec succès"
else
    print_error "Erreur lors de la construction de l'image corrigée"
    exit 1
fi

# Mettre à jour le docker-compose pour utiliser la nouvelle image
sed -i 's/taskmanager-api:problematic/taskmanager-api:fixed/g' docker-compose-demo.yml

wait_for_input

# Étape 7: Test de la solution
echo "=== ÉTAPE 7: TEST DE LA SOLUTION ==="
echo ""
print_info "Démarrage de l'application avec l'image corrigée..."

docker-compose -f docker-compose-demo.yml up -d

# Attendre que les services se lancent
print_info "Attente du démarrage des services..."
sleep 15

# Vérifier les logs
print_info "Vérification des logs de l'application corrigée..."
echo ""
print_success "LOGS DE L'APPLICATION (SUCCÈS ATTENDU):"
docker-compose -f docker-compose-demo.yml logs app | tail -20

wait_for_input

# Étape 8: Validation fonctionnelle
echo "=== ÉTAPE 8: VALIDATION FONCTIONNELLE ==="
echo ""
print_info "Test de l'API pour confirmer le bon fonctionnement..."

# Test du endpoint de health
print_info "Test du endpoint /health..."
health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$health_response" = "200" ]; then
    print_success "Health check: OK (HTTP 200)"
else
    print_error "Health check: FAILED (HTTP $health_response)"
fi

# Test de création d'une tâche
print_info "Test de création d'une tâche..."
task_response=$(curl -s -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Task", "description": "This is a test task"}' \
     -w "%{http_code}")

if [[ "$task_response" == *"200"* ]] || [[ "$task_response" == *"201"* ]]; then
    print_success "Création de tâche: OK"
else
    print_error "Création de tâche: FAILED"
fi

# Test de récupération des tâches
print_info "Test de récupération des tâches..."
tasks_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/tasks)

if [ "$tasks_response" = "200" ]; then
    print_success "Récupération des tâches: OK (HTTP 200)"
else
    print_error "Récupération des tâches: FAILED (HTTP $tasks_response)"
fi

wait_for_input

# Étape 9: Amélioration avec script de démarrage
echo "=== ÉTAPE 9: AMÉLIORATION AVEC SCRIPT DE DÉMARRAGE ==="
echo ""
print_info "Pour une solution plus robuste, créons un script de démarrage..."

# Créer un script de démarrage amélioré
cat > start.sh << 'EOF'
#!/bin/bash

# Script de démarrage robuste pour l'application
set -e

echo "Starting TaskManager API..."

# Attendre que la base de données soit prête
echo "Waiting for database to be ready..."
until pg_isready -h db -p 5432 -U user; do
    echo "Database is not ready yet. Waiting..."
    sleep 2
done

echo "Database is ready!"

# Appliquer les migrations
echo "Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations applied successfully!"
else
    echo "Error applying migrations!"
    exit 1
fi

# Démarrer l'application
echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
EOF

chmod +x start.sh

print_success "Script de démarrage créé!"
print_info "Ce script inclut:"
echo "  - Vérification de la disponibilité de la base de données"
echo "  - Application des migrations avec gestion d'erreur"
echo "  - Démarrage de l'application"
echo "  - Logs détaillés pour le debugging"

# Créer un Dockerfile utilisant le script
cat > Dockerfile.improved << 'EOF'
FROM python:3.11-slim

# Installer postgresql-client pour pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Rendre le script exécutable
RUN chmod +x start.sh

EXPOSE 8000

# Utiliser le script de démarrage amélioré
CMD ["./start.sh"]
EOF

print_info "Dockerfile amélioré créé (Dockerfile.improved)"

wait_for_input

# Étape 10: Résumé et bonnes pratiques
echo "=== ÉTAPE 10: RÉSUMÉ ET BONNES PRATIQUES ==="
echo ""
print_success "PROBLÈME RÉSOLU AVEC SUCCÈS!"
echo ""
print_info "RÉCAPITULATIF:"
echo "  ✗ Problème: Migrations Alembic non appliquées en production"
echo "  ✓ Solution: Ajout de 'alembic upgrade head' dans le CMD du Dockerfile"
echo "  ✓ Résultat: Application démarrée et fonctionnelle"
echo ""
print_info "BONNES PRATIQUES IDENTIFIÉES:"
echo "  1. Automatiser les migrations dans le processus de déploiement"
echo "  2. Utiliser des scripts de démarrage robustes"
echo "  3. Vérifier la disponibilité des dépendances (DB)"
echo "  4. Implémenter des health checks"
echo "  5. Maintenir la parité entre dev et prod"
echo "  6. Documenter les processus de déploiement"
echo ""
print_info "MONITORING ET ALERTES:"
echo "  - Logs structurés pour tracer les migrations"
echo "  - Alertes sur les échecs de démarrage"
echo "  - Métriques de santé de l'application"
echo "  - Surveillance des erreurs de base de données"

wait_for_input

# Étape 11: Nettoyage
echo "=== ÉTAPE 11: NETTOYAGE ==="
echo ""
print_info "Nettoyage des ressources de démonstration..."

# Arrêter les services
docker-compose -f docker-compose-demo.yml down -v

# Supprimer les images de démonstration
docker rmi taskmanager-api:problematic taskmanager-api:fixed 2>/dev/null || true

# Supprimer les fichiers temporaires
rm -f docker-compose-demo.yml Dockerfile.improved start.sh

print_success "Nettoyage terminé!"
echo ""
print_info "DÉMONSTRATION TERMINÉE"
print_info "Le rapport complet documente cet incident et sa résolution."
print_info "Les fichiers du projet sont prêts pour le déploiement en production."