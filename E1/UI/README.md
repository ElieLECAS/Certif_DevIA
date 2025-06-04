# Dashboard Production Industrielle - Interface Streamlit

## Description

Cette application Streamlit fournit une interface web moderne pour visualiser et analyser les données de production des centres d'usinage. Elle se connecte à l'API FastAPI pour récupérer les données en temps réel.

## Fonctionnalités

### 📊 Vue d'ensemble des centres d'usinage

-   Affichage du nombre total de centres d'usinage
-   Liste détaillée des centres avec leurs caractéristiques
-   Filtrage par statut (actif/inactif)

### 🔄 Sessions de production

-   Visualisation des sessions de production avec filtres par date et centre
-   Métriques clés : nombre de sessions, total de pièces, taux d'occupation, taux d'attente
-   Graphiques interactifs :
    -   Barres : Pièces produites par centre d'usinage
    -   Ligne temporelle : Évolution du nombre de sessions par jour
-   Tableau détaillé des sessions avec tri et filtrage

### 📈 Statistiques globales

-   Résumé de production avec indicateurs de performance
-   Métriques agrégées sur l'ensemble des centres

## Interface utilisateur

### Sidebar (Barre latérale)

-   **Filtres par centre d'usinage** : Sélection d'un centre spécifique ou vue globale
-   **Filtres temporels** : Sélection de plages de dates pour l'analyse

### Dashboard principal

-   **Layout responsive** : Adaptation automatique à la taille de l'écran
-   **Mise à jour automatique** : Cache des données pendant 1 minute
-   **Graphiques interactifs** : Zoom, survol, export des visualisations

## Configuration

### Variables d'environnement

-   `API_BASE_URL` : URL de base de l'API FastAPI (par défaut : `http://api:8000`)

### Configuration Streamlit

Le fichier `.streamlit/config.toml` contient :

-   Thème personnalisé avec couleurs de l'entreprise
-   Configuration serveur pour Docker
-   Désactivation des statistiques d'usage

## Déploiement avec Docker

### Construction de l'image

```bash
docker build -t streamlit-ui ./UI
```

### Lancement avec docker-compose

```bash
docker-compose up ui
```

L'application sera accessible sur `http://localhost:8501`

## Dépendances

-   **streamlit** : Framework web pour applications de données
-   **requests** : Client HTTP pour communiquer avec l'API
-   **pandas** : Manipulation et analyse de données
-   **plotly** : Graphiques interactifs
-   **numpy** : Calculs numériques

## Structure des fichiers

```
UI/
├── app.py                 # Application Streamlit principale
├── requirements.txt       # Dépendances Python
├── Dockerfile            # Configuration Docker
├── .streamlit/
│   └── config.toml       # Configuration Streamlit
└── README.md             # Documentation
```

## Utilisation

1. **Démarrage** : L'application se lance automatiquement avec docker-compose
2. **Navigation** : Utilisez la sidebar pour filtrer les données
3. **Visualisation** : Explorez les différentes sections du dashboard
4. **Interaction** : Cliquez sur les graphiques pour plus de détails

## Troubleshooting

### Erreurs de connexion API

-   Vérifiez que le service API est démarré
-   Contrôlez la configuration réseau Docker
-   Consultez les logs : `docker logs streamlit_ui`

### Performance

-   Les données sont mises en cache pendant 1 minute
-   Pour forcer le rafraîchissement : utilisez Ctrl+R dans le navigateur
-   Pour vider le cache : redémarrez le conteneur

## Développement

### Mode développement local

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Ajout de nouvelles fonctionnalités

1. Modifiez `app.py`
2. Ajoutez les dépendances dans `requirements.txt`
3. Testez localement
4. Reconstruisez l'image Docker
