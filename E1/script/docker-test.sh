#!/bin/bash
"""
Script pour exécuter les tests pytest dans Docker.

Ce script facilite l'exécution des tests dans un environnement Docker.

Utilisation:
    ./docker-test.sh                    # Tous les tests
    ./docker-test.sh --coverage         # Tests avec couverture
    ./docker-test.sh --unit             # Tests unitaires seulement
    ./docker-test.sh --build            # Rebuild l'image avant les tests
"""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
IMAGE_NAME="ftp-log-service-test"
CONTAINER_NAME="ftp-log-test-container"

# Fonction pour afficher les messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Fonction pour nettoyer les conteneurs existants
cleanup() {
    print_info "Nettoyage des conteneurs existants..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
}

# Fonction pour construire l'image Docker
build_image() {
    print_info "Construction de l'image Docker..."
    if docker build -t $IMAGE_NAME .; then
        print_success "Image Docker construite avec succès"
    else
        print_error "Échec de la construction de l'image Docker"
        exit 1
    fi
}

# Fonction pour exécuter les tests
run_tests() {
    local test_args="$1"
    
    print_info "Démarrage du conteneur de test..."
    
    # Nettoyer d'abord
    cleanup
    
    # Exécuter le conteneur avec les tests
    if docker run --name $CONTAINER_NAME --rm $IMAGE_NAME python3 run_tests.py $test_args; then
        print_success "Tests exécutés avec succès"
        return 0
    else
        print_error "Échec des tests"
        return 1
    fi
}

# Fonction pour exécuter les tests en mode interactif
run_interactive() {
    print_info "Démarrage du conteneur en mode interactif..."
    cleanup
    docker run -it --name $CONTAINER_NAME --rm $IMAGE_NAME bash
}

# Fonction pour afficher l'aide
show_help() {
    echo "Script pour exécuter les tests pytest dans Docker"
    echo ""
    echo "Utilisation: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help              Afficher cette aide"
    echo "  --build             Reconstruire l'image Docker avant les tests"
    echo "  --interactive       Lancer un shell interactif dans le conteneur"
    echo "  --coverage          Exécuter les tests avec couverture de code"
    echo "  --unit              Exécuter seulement les tests unitaires"
    echo "  --integration       Exécuter seulement les tests d'intégration"
    echo "  --verbose           Mode verbeux"
    echo "  --fast              Tests rapides seulement"
    echo "  --specific TEST     Exécuter un test spécifique"
    echo ""
    echo "Exemples:"
    echo "  $0                           # Tous les tests"
    echo "  $0 --build --coverage        # Rebuild + tests avec couverture"
    echo "  $0 --unit --verbose          # Tests unitaires en mode verbeux"
    echo "  $0 --interactive             # Shell interactif"
}

# Parsing des arguments
BUILD_IMAGE=false
INTERACTIVE=false
TEST_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        --build)
            BUILD_IMAGE=true
            shift
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        --coverage|--unit|--integration|--verbose|--fast)
            TEST_ARGS="$TEST_ARGS $1"
            shift
            ;;
        --specific)
            TEST_ARGS="$TEST_ARGS $1 $2"
            shift 2
            ;;
        *)
            print_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Affichage de l'en-tête
echo "🐳 TESTS DOCKER POUR FTP LOG SERVICE"
echo "===================================="

# Vérifier que Docker est disponible
if ! command -v docker &> /dev/null; then
    print_error "Docker n'est pas installé ou n'est pas dans le PATH"
    exit 1
fi

# Construire l'image si demandé
if [ "$BUILD_IMAGE" = true ]; then
    build_image
fi

# Vérifier que l'image existe
if ! docker image inspect $IMAGE_NAME &> /dev/null; then
    print_warning "L'image $IMAGE_NAME n'existe pas, construction automatique..."
    build_image
fi

# Exécuter selon le mode demandé
if [ "$INTERACTIVE" = true ]; then
    run_interactive
else
    print_info "Exécution des tests avec les arguments: $TEST_ARGS"
    if run_tests "$TEST_ARGS"; then
        print_success "Tous les tests sont terminés avec succès!"
        exit 0
    else
        print_error "Certains tests ont échoué!"
        exit 1
    fi
fi 