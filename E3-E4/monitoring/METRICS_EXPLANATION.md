# 📊 Explication des Métriques Prometheus et Grafana

Ce document explique en détail toutes les métriques collectées par Prometheus et affichées dans les dashboards Grafana pour le projet FastAPI.

## 🔍 Métriques de Base HTTP

### 1. **Request Rate (Taux de Requêtes)**
- **Métrique Prometheus**: `rate(http_requests_total[5m])`
- **Description**: Nombre de requêtes HTTP par seconde
- **Unité**: Requêtes/seconde
- **Interprétation**:
  - **Normal**: 0.1 - 10 req/s (dépend de l'usage)
  - **Élevé**: > 10 req/s (charge importante)
  - **Très élevé**: > 100 req/s (pic de charge)

### 2. **Response Time (Temps de Réponse)**
- **Métrique Prometheus**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Description**: Temps de réponse des requêtes HTTP
- **Unité**: Secondes
- **Interprétation**:
  - **Excellent**: < 0.1s
  - **Bon**: 0.1s - 0.5s
  - **Acceptable**: 0.5s - 2s
  - **Problématique**: > 2s

### 3. **Error Rate (Taux d'Erreurs)**
- **Métrique Prometheus**: `rate(http_errors_total[5m])`
- **Description**: Nombre d'erreurs HTTP par seconde
- **Unité**: Erreurs/seconde
- **Interprétation**:
  - **Normal**: 0 - 0.01 erreurs/s
  - **Problématique**: > 0.01 erreurs/s
  - **Critique**: > 0.1 erreurs/s

### 4. **Active Connections (Connexions Actives)**
- **Métrique Prometheus**: `http_requests_in_flight`
- **Description**: Nombre de requêtes en cours de traitement
- **Unité**: Nombre de connexions
- **Interprétation**:
  - **Normal**: 1 - 10 connexions
  - **Élevé**: 10 - 50 connexions
  - **Très élevé**: > 50 connexions

## 📈 Métriques Détaillées par Endpoint

### 5. **Requests by HTTP Method (Requêtes par Méthode HTTP)**
- **Métrique Prometheus**: `sum(rate(http_requests_total[5m])) by (method)`
- **Description**: Répartition des requêtes par méthode HTTP (GET, POST, etc.)
- **Interprétation**:
  - **GET**: Pages et données de lecture
  - **POST**: Soumissions de formulaires et API
  - **PUT/PATCH**: Modifications de données
  - **DELETE**: Suppressions

### 6. **Requests by Endpoint (Requêtes par Endpoint)**
- **Métrique Prometheus**: `sum(rate(http_requests_total[5m])) by (endpoint)`
- **Description**: Répartition des requêtes par endpoint
- **Endpoints principaux**:
  - `/login`: Authentification
  - `/api/chat`: API de chat RAG
  - `/conversations`: Gestion des conversations
  - `/register`: Inscription

## 🎯 Métriques Spécifiques au Chat RAG

### 7. **Chat API Response Time**
- **Métrique Prometheus**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{endpoint="/api/chat"}[5m]))`
- **Description**: Temps de réponse spécifique à l'API de chat
- **Interprétation**:
  - **Normal**: < 5s (temps de traitement RAG)
  - **Lent**: 5s - 15s
  - **Problématique**: > 15s

### 8. **Chat API Request Rate**
- **Métrique Prometheus**: `rate(http_requests_total{endpoint="/api/chat"}[5m])`
- **Description**: Taux de requêtes vers l'API de chat
- **Interprétation**:
  - **Normal**: 0.01 - 0.1 req/s
  - **Élevé**: 0.1 - 1 req/s
  - **Très élevé**: > 1 req/s

### 9. **Chat API Error Rate**
- **Métrique Prometheus**: `rate(http_errors_total{endpoint="/api/chat"}[5m]) / rate(http_requests_total{endpoint="/api/chat"}[5m])`
- **Description**: Pourcentage d'erreurs pour l'API de chat
- **Interprétation**:
  - **Normal**: < 1%
  - **Problématique**: 1% - 5%
  - **Critique**: > 5%

## 🚨 Types d'Erreurs

### 10. **Error Types Breakdown (Répartition des Types d'Erreurs)**
- **Client Errors (4xx)**: Erreurs côté client
  - 400: Bad Request
  - 401: Unauthorized
  - 404: Not Found
- **Server Errors (5xx)**: Erreurs côté serveur
  - 500: Internal Server Error
  - 502: Bad Gateway
  - 503: Service Unavailable
- **Exceptions**: Erreurs non gérées

## 📊 Métriques de Performance

### 11. **Response Time Percentiles**
- **50th percentile (médiane)**: Temps de réponse typique
- **95th percentile**: Temps de réponse pour 95% des requêtes
- **99th percentile**: Temps de réponse pour les cas extrêmes

### 12. **Error Rate Percentage**
- **Métrique Prometheus**: `rate(http_requests_total{status=~"4..|5.."}[5m]) / rate(http_requests_total[5m])`
- **Description**: Pourcentage global d'erreurs
- **Interprétation**:
  - **Excellent**: < 0.1%
  - **Bon**: 0.1% - 1%
  - **Problématique**: > 1%

## 🔧 Configuration des Métriques

### Métriques Collectées dans `app.py`

```python
# Compteur de requêtes totales
http_requests_total = Counter(
    'http_requests_total',
    'Total des requêtes HTTP',
    ['method', 'endpoint', 'status']
)

# Histogramme des temps de réponse
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Durée des requêtes HTTP',
    ['method', 'endpoint']
)

# Gauge des requêtes en cours
http_requests_in_flight = Gauge(
    'http_requests_in_flight',
    'Requêtes HTTP en cours',
    ['method', 'endpoint']
)

# Compteur d'erreurs détaillées
http_errors_total = Counter(
    'http_errors_total',
    'Total des erreurs HTTP',
    ['method', 'endpoint', 'status', 'error_type']
)
```

## 📈 Seuils d'Alerte Recommandés

### Seuils de Performance
- **Response Time 95th percentile**: > 2s
- **Error Rate**: > 1%
- **Active Connections**: > 50
- **Chat API Response Time**: > 10s

### Seuils de Charge
- **Request Rate**: > 100 req/s
- **Chat API Request Rate**: > 5 req/s
- **Error Rate Percentage**: > 5%

## 🎯 Utilisation des Dashboards

### Dashboard Standard
- **4 panneaux principaux**: Request Rate, Response Time, Error Rate, Active Connections
- **Vue d'ensemble rapide** de l'état de l'application
- **Rafraîchissement**: 5s - 1h

### Dashboard Amélioré
- **13 panneaux détaillés** avec métriques avancées
- **Analyse par endpoint** et par méthode HTTP
- **Métriques spécifiques RAG** pour le chat
- **Seuils colorés** pour une détection visuelle rapide

## 🔍 Interprétation des Graphiques

### Patterns Normaux
- **Request Rate**: Stable avec des pics pendant les heures d'usage
- **Response Time**: Relativement constant avec quelques pics
- **Error Rate**: Proche de zéro avec quelques erreurs occasionnelles
- **Active Connections**: Faible en temps normal, plus élevé pendant les pics

### Patterns Problématiques
- **Request Rate**: Pics soudains et prolongés
- **Response Time**: Augmentation progressive ou soudaine
- **Error Rate**: Augmentation soudaine ou progressive
- **Active Connections**: Augmentation sans retour à la normale

## 🛠️ Dépannage

### Problèmes Courants

1. **Temps de réponse élevés**
   - Vérifier la base de données
   - Contrôler les appels API externes
   - Analyser les requêtes RAG

2. **Taux d'erreurs élevés**
   - Vérifier les logs d'application
   - Contrôler la connectivité base de données
   - Analyser les erreurs 5xx

3. **Connexions actives élevées**
   - Vérifier les fuites de connexions
   - Contrôler les timeouts
   - Analyser les requêtes bloquantes

## 📚 Ressources Additionnelles

- [Documentation Prometheus](https://prometheus.io/docs/)
- [Documentation Grafana](https://grafana.com/docs/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/)
- [Grafana Dashboard Templates](https://grafana.com/grafana/dashboards/)

---

*Ce document est mis à jour régulièrement avec les nouvelles métriques et améliorations du système de monitoring.*