"""
Module de monitoring pour l'application FastAPI avec Prometheus.
"""

import time
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import psutil
import os

# Métriques Prometheus
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total des requêtes HTTP',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Durée des requêtes HTTP',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Nombre de requêtes actives'
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Utilisation mémoire de l\'application'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'Utilisation CPU de l\'application'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Nombre de connexions actives à la base de données'
)

# Métriques spécifiques au chatbot
CHAT_REQUESTS = Counter(
    'chat_requests_total',
    'Total des requêtes de chat',
    ['user_type', 'response_status']
)

CHAT_RESPONSE_TIME = Histogram(
    'chat_response_time_seconds',
    'Temps de réponse du chatbot',
    ['user_type']
)

AI_MODEL_CALLS = Counter(
    'ai_model_calls_total',
    'Total des appels au modèle IA',
    ['model_type', 'status']
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour collecter les métriques Prometheus.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Incrémenter le compteur de requêtes actives
        ACTIVE_REQUESTS.inc()
        
        try:
            response = await call_next(request)
            
            # Enregistrer les métriques
            duration = time.time() - start_time
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Enregistrer les erreurs
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            raise e
        finally:
            # Décrémenter le compteur de requêtes actives
            ACTIVE_REQUESTS.dec()

def update_system_metrics():
    """
    Met à jour les métriques système.
    """
    try:
        # Métriques mémoire
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        MEMORY_USAGE.set(memory_info.rss)
        
        # Métriques CPU
        cpu_percent = process.cpu_percent()
        CPU_USAGE.set(cpu_percent)
    except Exception as e:
        # En cas d'erreur, on ne fait rien pour éviter de casser l'application
        pass

def get_metrics():
    """
    Retourne les métriques Prometheus au format texte.
    """
    # Mettre à jour les métriques système
    update_system_metrics()
    
    return generate_latest()

def create_metrics_response():
    """
    Crée une réponse HTTP avec les métriques Prometheus.
    """
    return StarletteResponse(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )

# Fonctions utilitaires pour les métriques métier
def record_chat_request(user_type: str, response_status: str):
    """
    Enregistre une requête de chat.
    """
    CHAT_REQUESTS.labels(
        user_type=user_type,
        response_status=response_status
    ).inc()

def record_chat_response_time(user_type: str, duration: float):
    """
    Enregistre le temps de réponse du chat.
    """
    CHAT_RESPONSE_TIME.labels(user_type=user_type).observe(duration)

def record_ai_model_call(model_type: str, status: str):
    """
    Enregistre un appel au modèle IA.
    """
    AI_MODEL_CALLS.labels(
        model_type=model_type,
        status=status
    ).inc()

def record_database_connection_count(count: int):
    """
    Enregistre le nombre de connexions à la base de données.
    """
    DATABASE_CONNECTIONS.set(count)