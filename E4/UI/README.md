# GMAO Mobile - Application Flask

Application mobile optimisée pour la gestion de stock avec scanner QR code, basée sur Flask et l'API FastAPI.

## Fonctionnalités

### 🔍 Scanner QR Code

-   Scanner en temps réel avec la caméra
-   Support multi-caméras (avant/arrière)
-   Saisie manuelle en fallback
-   Historique des scans récents
-   Interface optimisée mobile

### 📦 Gestion de Stock

-   Consultation de l'inventaire
-   Recherche avancée
-   Filtres par niveau de stock
-   Mouvements de stock (entrées/sorties)
-   Alertes de stock faible

### 📱 Interface Mobile

-   Design responsive et mobile-first
-   Navigation par onglets en bas
-   Actions rapides accessibles
-   Mode hors ligne partiel
-   PWA ready

### 🎯 Actions Rapides

-   Scanner QR code
-   Mouvement de stock direct
-   Création de demandes
-   Génération de QR codes
-   Partage et téléchargement

## Installation et Déploiement

### Avec Docker (Recommandé)

1. **Construire l'image**

```bash
docker build -t gmao-flask-mobile ./UI
```

2. **Lancer avec docker-compose**

```bash
# Depuis la racine du projet
docker-compose up flask-mobile
```

L'application sera accessible sur `http://localhost:8080`

### Installation locale

1. **Installer les dépendances**

```bash
cd UI
pip install -r requirements.txt
```

2. **Configurer les variables d'environnement**

```bash
export API_BASE_URL=http://localhost:8010
export SECRET_KEY=your-secret-key
```

3. **Lancer l'application**

```bash
python app.py
```

## Configuration

### Variables d'environnement

-   `API_BASE_URL`: URL de l'API FastAPI (défaut: http://localhost:8010)
-   `SECRET_KEY`: Clé secrète Flask pour les sessions
-   `FLASK_ENV`: Environnement Flask (production/development)

### Dépendances

-   **Flask 2.3.3**: Framework web
-   **requests 2.31.0**: Client HTTP pour l'API
-   **qrcode[pil] 7.4.2**: Génération de QR codes
-   **Pillow 10.0.1**: Traitement d'images
-   **gunicorn 21.2.0**: Serveur WSGI pour production

## Structure du Projet

```
UI/
├── app.py                 # Application Flask principale
├── requirements.txt       # Dépendances Python
├── Dockerfile            # Configuration Docker
├── templates/            # Templates Jinja2
│   ├── base.html         # Template de base
│   ├── index.html        # Page d'accueil
│   ├── scanner.html      # Scanner QR code
│   ├── inventaire.html   # Liste des produits
│   └── produit_detail.html # Détail produit
└── static/              # Fichiers statiques (si nécessaire)
```

## API Endpoints Utilisés

L'application communique avec l'API FastAPI via les endpoints suivants :

-   `GET /inventaire/` - Liste des produits
-   `GET /inventaire/search/` - Recherche de produits
-   `GET /inventaire/reference/{reference}` - Produit par référence
-   `GET /inventaire/stock-faible/` - Produits en stock faible
-   `POST /mouvements-stock/` - Enregistrer un mouvement
-   `GET /demandes/` - Liste des demandes
-   `POST /demandes/` - Créer une demande

## Fonctionnalités Mobiles

### Scanner QR Code

-   Utilise la librairie `html5-qrcode` pour l'accès caméra
-   Support des appareils iOS et Android
-   Gestion des permissions caméra
-   Fallback en saisie manuelle

### Interface Responsive

-   Bootstrap 5 pour le design
-   Navigation bottom tabs
-   Boutons d'action flottants
-   Optimisé pour les écrans tactiles

### PWA Features

-   Meta tags pour l'installation
-   Mode hors ligne partiel
-   Notifications push (à implémenter)
-   Cache des données critiques

## Développement

### Lancer en mode développement

```bash
export FLASK_ENV=development
python app.py
```

### Structure des templates

Les templates utilisent Jinja2 avec un système de blocs :

-   `{% block title %}` - Titre de la page
-   `{% block content %}` - Contenu principal
-   `{% block extra_css %}` - CSS spécifique
-   `{% block extra_js %}` - JavaScript spécifique

### Ajout de nouvelles fonctionnalités

1. Créer la route dans `app.py`
2. Créer le template correspondant
3. Ajouter les appels API nécessaires
4. Tester sur mobile

## Production

### Configuration Docker

Le Dockerfile utilise :

-   Python 3.11-slim comme base
-   Gunicorn avec 4 workers
-   Port 5000 exposé
-   Variables d'environnement configurables

### Sécurité

-   Changez `SECRET_KEY` en production
-   Configurez CORS correctement
-   Utilisez HTTPS en production
-   Validez toutes les entrées utilisateur

### Performance

-   Cache des requêtes API fréquentes
-   Compression des assets
-   CDN pour les librairies externes
-   Monitoring des performances

## Troubleshooting

### Problèmes courants

1. **Scanner ne fonctionne pas**

    - Vérifiez les permissions caméra
    - Testez sur HTTPS (requis pour la caméra)
    - Utilisez la saisie manuelle en fallback

2. **Erreurs API**

    - Vérifiez que l'API FastAPI est démarrée
    - Contrôlez l'URL dans `API_BASE_URL`
    - Vérifiez les logs de l'API

3. **Problèmes d'affichage mobile**
    - Testez sur différents navigateurs
    - Vérifiez la viewport meta tag
    - Utilisez les outils de développement mobile

### Logs

```bash
# Logs Docker
docker logs gmao-flask-mobile

# Logs locaux
tail -f app.log
```

## Roadmap

### Fonctionnalités à venir

-   [ ] Mode hors ligne complet
-   [ ] Notifications push
-   [ ] Synchronisation en arrière-plan
-   [ ] Export de données
-   [ ] Rapports mobiles
-   [ ] Authentification utilisateur
-   [ ] Multi-langues

### Améliorations techniques

-   [ ] Tests automatisés
-   [ ] CI/CD pipeline
-   [ ] Monitoring avancé
-   [ ] Cache Redis
-   [ ] WebSockets pour temps réel
