# 📊 Monitoring FastAPI Chatbot SAV

## 🎯 Vue d'ensemble

Ce projet inclut un système de monitoring complet pour l'application FastAPI Chatbot SAV avec **Prometheus** et **Grafana**.

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   FastAPI   │───▶│  Prometheus  │───▶│   Grafana   │
│  Application│    │   (Collect)  │    │ (Visualize) │
└─────────────┘    └──────────────┘    └─────────────┘
```

## 🚀 Démarrage Rapide

### 1. Démarrer les services

```bash
cd E3-E4
docker-compose up -d
```

### 2. Vérifier les services

```bash
# Vérifier que tous les services sont démarrés
docker-compose ps

# Vérifier les logs
docker-compose logs -f
```

### 3. Accès aux interfaces

| Service | URL | Description |
|---------|-----|-------------|
| **FastAPI App** | http://localhost:8001 | Application principale |
| **Prometheus** | http://localhost:9090 | Collecte de métriques |
| **Grafana** | http://localhost:3000 | Visualisation (admin/admin) |

## 📊 Métriques Disponibles

### 🔍 Métriques Système
- **CPU Usage** : Utilisation CPU de l'application
- **Memory Usage** : Utilisation mémoire (RSS)
- **Active Requests** : Nombre de requêtes simultanées

### 🌐 Métriques HTTP
- **Request Count** : Nombre total de requêtes par endpoint
- **Request Duration** : Temps de réponse par endpoint
- **Status Codes** : Distribution des codes de statut HTTP

### 🤖 Métriques Métier (Chatbot)
- **Chat Requests** : Requêtes de chat par type d'utilisateur
- **Chat Response Time** : Temps de réponse du chatbot
- **AI Model Calls** : Appels aux modèles IA

## 📈 Dashboard Grafana

Le dashboard inclut :

### 🎛️ Panels Principaux
1. **Requêtes HTTP par minute** - Graphique des requêtes
2. **Temps de réponse moyen** - Latence par endpoint
3. **Requêtes actives** - Nombre de requêtes simultanées
4. **Utilisation mémoire** - Mémoire en MB
5. **Utilisation CPU** - CPU en pourcentage
6. **Requêtes de chat** - Par type d'utilisateur
7. **Temps de réponse du chatbot** - Latence du chatbot
8. **Appels au modèle IA** - Par type de modèle
9. **Codes de statut HTTP** - Distribution des codes

### 🔧 Personnalisation

Pour ajouter un nouveau panel :

1. Aller sur Grafana (http://localhost:3000)
2. Ouvrir le dashboard "FastAPI Chatbot SAV - Monitoring"
3. Cliquer sur "Add panel"
4. Configurer la requête PromQL

## 🔍 Requêtes Prometheus Utiles

### 📈 Requêtes de Base

```promql
# Requêtes HTTP par seconde
rate(http_requests_total[1m])

# Temps de réponse moyen
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Utilisation mémoire en MB
memory_usage_bytes / 1024 / 1024

# Requêtes actives
http_requests_active
```

### 🎯 Requêtes Métier

```promql
# Requêtes de chat par type d'utilisateur
rate(chat_requests_total[5m])

# Temps de réponse du chatbot
rate(chat_response_time_seconds_sum[5m]) / rate(chat_response_time_seconds_count[5m])

# Appels au modèle IA
rate(ai_model_calls_total[5m])
```

## 🧪 Tests

### Test Automatique

```bash
# Lancer le script de test
python test_monitoring.py
```

### Tests Manuels

```bash
# Test de l'endpoint de santé
curl http://localhost:8001/health

# Test des métriques
curl http://localhost:8001/metrics

# Test de Prometheus
curl http://localhost:9090/api/v1/targets
```

## 🔧 Configuration

### Prometheus (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi-app'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Grafana

- **Source de données** : Prometheus (http://prometheus:9090)
- **Dashboard** : Chargé automatiquement
- **Credentials** : admin/admin

## 🚨 Alertes (Configuration Recommandée)

Ajouter dans `prometheus.yml` :

```yaml
rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

Créer `alerts.yml` :

```yaml
groups:
  - name: fastapi_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Taux d'erreur élevé"
          
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Temps de réponse élevé"
```

## 🛠️ Dépannage

### Problèmes Courants

#### **Prometheus ne collecte pas les métriques**
```bash
# Vérifier la configuration
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# Vérifier les cibles
curl http://localhost:9090/api/v1/targets
```

#### **Grafana ne se connecte pas à Prometheus**
```bash
# Vérifier la source de données
# Grafana UI → Configuration → Data Sources → Prometheus
# URL: http://prometheus:9090
```

#### **Métriques manquantes**
```bash
# Vérifier l'endpoint /metrics
curl http://localhost:8001/metrics

# Vérifier les logs de l'application
docker-compose logs web
```

### Logs Utiles

```bash
# Logs de tous les services
docker-compose logs

# Logs d'un service spécifique
docker-compose logs prometheus
docker-compose logs grafana
docker-compose logs web
```

## 📊 Métriques Avancées

### Métriques Personnalisées

Le code inclut des métriques spécifiques au chatbot :

```python
# Exemple d'utilisation dans le code
from monitoring import record_chat_request, record_chat_response_time

# Dans une route
record_chat_request("client", "success")
record_chat_response_time("client", duration)
```

### Métriques Disponibles

| Métrique | Description | Labels |
|----------|-------------|--------|
| `http_requests_total` | Total des requêtes HTTP | method, endpoint, status |
| `http_request_duration_seconds` | Durée des requêtes | method, endpoint |
| `http_requests_active` | Requêtes actives | - |
| `memory_usage_bytes` | Utilisation mémoire | - |
| `cpu_usage_percent` | Utilisation CPU | - |
| `chat_requests_total` | Requêtes de chat | user_type, response_status |
| `chat_response_time_seconds` | Temps de réponse chat | user_type |
| `ai_model_calls_total` | Appels IA | model_type, status |

## 📈 Optimisation

### Recommandations de Performance

1. **Scrape Interval** : 10-15s pour les métriques critiques
2. **Retention** : 15-30 jours pour Prometheus
3. **Dashboard Refresh** : 10-30s selon les besoins
4. **Alerting** : Seuils adaptés à votre charge

### Configuration Optimisée

```yaml
# prometheus.yml optimisé
global:
  scrape_interval: 10s
  evaluation_interval: 10s

scrape_configs:
  - job_name: 'fastapi-app'
    scrape_interval: 10s
    scrape_timeout: 5s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['web:8000']
```

## 📚 Ressources

### Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Monitoring](https://fastapi.tiangolo.com/advanced/middleware/)

### Outils Complémentaires
- **AlertManager** : Gestion des alertes
- **Node Exporter** : Métriques système
- **cAdvisor** : Métriques conteneurs

---

## 🎯 Résumé

Ce système de monitoring offre :

✅ **Visibilité complète** sur les performances  
✅ **Métriques métier** spécifiques au chatbot  
✅ **Interface intuitive** avec Grafana  
✅ **Scalabilité** pour la production  
✅ **Alertes proactives** (configurables)  

Le monitoring est maintenant opérationnel pour votre application FastAPI Chatbot SAV !