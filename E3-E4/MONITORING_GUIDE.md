# 📊 Guide de Monitoring - FastAPI Chatbot SAV

## 🎯 Vue d'ensemble

Ce guide détaille la mise en place d'un système de monitoring complet pour l'application FastAPI Chatbot SAV avec Prometheus et Grafana.

## 🏗️ Architecture du Monitoring

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │───▶│  Prometheus  │───▶│   Grafana   │───▶│   Alerts    │
│  Application│    │   (Collect)  │    │ (Visualize) │    │ (Notify)    │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
```

## 📋 Métriques Collectées

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

### 🗄️ Métriques Base de Données
- **Database Connections** : Connexions actives à la DB

## 🚀 Installation et Configuration

### 1. Démarrage des Services

```bash
# Cloner le projet
git clone <repository>
cd E3-E4

# Démarrer tous les services
docker-compose up -d

# Vérifier les services
docker-compose ps
```

### 2. Accès aux Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI App** | http://localhost:8001 | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin/admin |

### 3. Configuration Initiale Grafana

1. **Connexion** : http://localhost:3000 (admin/admin)
2. **Source de données** : Prometheus est configuré automatiquement
3. **Dashboard** : Le dashboard FastAPI est chargé automatiquement

## 📊 Dashboard Grafana

### 🎛️ Panels Disponibles

#### **1. Métriques HTTP**
- **Requêtes par minute** : Graphique des requêtes HTTP
- **Temps de réponse** : Latence moyenne par endpoint
- **Codes de statut** : Distribution des codes HTTP

#### **2. Métriques Système**
- **CPU Usage** : Utilisation CPU en temps réel
- **Memory Usage** : Utilisation mémoire en MB
- **Requêtes actives** : Nombre de requêtes simultanées

#### **3. Métriques Métier**
- **Chat Requests** : Requêtes de chat par type d'utilisateur
- **Chat Response Time** : Temps de réponse du chatbot
- **AI Model Calls** : Appels aux modèles IA

### 🔧 Personnalisation du Dashboard

```json
// Exemple d'ajout d'un nouveau panel
{
  "id": 10,
  "title": "Nouveau Panel",
  "type": "graph",
  "targets": [
    {
      "expr": "votre_requête_promql",
      "legendFormat": "{{label}}"
    }
  ]
}
```

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

## 🚨 Alertes (Configuration Recommandée)

### 📋 Règles d'Alerte

```yaml
# Exemple de règles d'alerte (à ajouter dans prometheus.yml)
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
          
      - alert: HighMemoryUsage
        expr: memory_usage_bytes / 1024 / 1024 > 500
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Utilisation mémoire élevée"
```

## 🔧 Intégration dans le Code

### 📝 Exemple d'Utilisation

```python
from monitoring import record_chat_request, record_chat_response_time

# Dans votre route de chat
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    start_time = time.time()
    
    try:
        # Logique du chatbot
        response = await process_chat_request(request)
        
        # Enregistrer les métriques
        record_chat_request("user", "success")
        record_chat_response_time("user", time.time() - start_time)
        
        return response
    except Exception as e:
        record_chat_request("user", "error")
        raise e
```

## 📊 Métriques Avancées

### 🔍 Métriques Personnalisées

```python
# Exemple de métrique personnalisée
from prometheus_client import Counter, Histogram

CUSTOM_METRIC = Counter(
    'custom_metric_total',
    'Description de la métrique',
    ['label1', 'label2']
)

# Utilisation
CUSTOM_METRIC.labels(label1="value1", label2="value2").inc()
```

### 📈 Métriques de Performance

```python
# Métriques de cache
CACHE_HITS = Counter('cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('cache_misses_total', 'Cache misses')

# Métriques de base de données
DB_QUERY_DURATION = Histogram('db_query_duration_seconds', 'DB query duration')
```

## 🛠️ Maintenance et Dépannage

### 🔍 Vérification des Services

```bash
# Vérifier les logs
docker-compose logs prometheus
docker-compose logs grafana
docker-compose logs web

# Vérifier les métriques
curl http://localhost:8001/metrics
curl http://localhost:9090/api/v1/targets
```

### 🔧 Problèmes Courants

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

## 📈 Optimisation des Performances

### 🎯 Recommandations

1. **Scrape Interval** : 10-15s pour les métriques critiques
2. **Retention** : 15-30 jours pour Prometheus
3. **Dashboard Refresh** : 10-30s selon les besoins
4. **Alerting** : Seuils adaptés à votre charge

### 🔧 Configuration Optimisée

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

## 📚 Ressources Utiles

### 🔗 Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Monitoring](https://fastapi.tiangolo.com/advanced/middleware/)

### 📊 Dashboards Prêts à l'Emploi
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Prometheus Exporters](https://prometheus.io/docs/instrumenting/exporters/)

### 🛠️ Outils Complémentaires
- **AlertManager** : Gestion des alertes
- **Node Exporter** : Métriques système
- **cAdvisor** : Métriques conteneurs

---

## 🎯 Résumé

Ce système de monitoring offre :

✅ **Visibilité complète** sur les performances de l'application  
✅ **Métriques métier** spécifiques au chatbot  
✅ **Alertes proactives** pour détecter les problèmes  
✅ **Interface intuitive** avec Grafana  
✅ **Scalabilité** pour les environnements de production  

Le monitoring est maintenant intégré et opérationnel pour votre application FastAPI Chatbot SAV !