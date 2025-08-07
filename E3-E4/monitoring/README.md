# Monitoring avec Prometheus et Grafana

Ce dossier contient la configuration pour le monitoring de l'application FastAPI avec Prometheus et Grafana.

## Structure

```
monitoring/
├── prometheus/
│   └── prometheus.yml          # Configuration Prometheus
├── grafana/
│   ├── dashboards/
│   │   └── fastapi-dashboard.json  # Dashboard FastAPI
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml      # Configuration source de données
│       └── dashboards/
│           └── dashboard.yml        # Configuration provisionnement
└── README.md
```

## Services

### Prometheus

-   **Port**: 9090
-   **URL**: http://localhost:9090
-   **Fonction**: Collecte et stocke les métriques

### Grafana

-   **Port**: 3000
-   **URL**: http://localhost:3000
-   **Identifiants par défaut**: admin/admin
-   **Fonction**: Visualisation des métriques

### PostgreSQL Exporter

-   **Port**: 9187
-   **URL**: http://localhost:9187
-   **Fonction**: Expose les métriques PostgreSQL pour Prometheus

## Métriques surveillées

-   Taux de requêtes HTTP
-   Temps de réponse
-   Taux d'erreurs
-   Connexions actives
-   Métriques PostgreSQL

## Utilisation

1. Démarrer les services : `docker-compose up -d`
2. Accéder à Grafana : http://localhost:3000
3. Se connecter avec admin/admin
4. Le dashboard FastAPI sera automatiquement disponible

## Configuration

Les métriques sont collectées automatiquement depuis :

-   L'application FastAPI (port 8000)
-   L'exporter PostgreSQL (port 9187)
-   Prometheus lui-même (port 9090)
