"""
Utilitaires de monitoring pour instrumenter OpenAI et FAISS
"""

import time
import functools
from typing import Any, Callable, Dict, List
import logging
from prometheus_client import Counter, Histogram
from app import (
    openai_requests_total,
    openai_request_duration_seconds,
    openai_response_tokens,
    openai_request_tokens,
    faiss_search_duration_seconds,
    faiss_search_results_count,
    chatbot_conversations_total,
    chatbot_messages_total
)

logger = logging.getLogger(__name__)


def monitor_openai_call(model: str = "gpt-4o-mini", endpoint: str = "chat/completions"):
    """
    Décorateur pour monitorer les appels OpenAI
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # Exécuter la fonction
                result = await func(*args, **kwargs)
                
                # Mesurer la durée
                duration = time.time() - start_time
                
                # Incrémenter les métriques de succès
                openai_requests_total.labels(
                    model=model,
                    endpoint=endpoint,
                    status="success"
                ).inc()
                
                # Enregistrer la durée
                openai_request_duration_seconds.labels(
                    model=model,
                    endpoint=endpoint
                ).observe(duration)
                
                # Compter les tokens si disponibles
                if hasattr(result, 'usage'):
                    if hasattr(result.usage, 'prompt_tokens'):
                        openai_request_tokens.labels(
                            model=model,
                            endpoint=endpoint
                        ).inc(result.usage.prompt_tokens)
                    
                    if hasattr(result.usage, 'completion_tokens'):
                        openai_response_tokens.labels(
                            model=model,
                            endpoint=endpoint
                        ).inc(result.usage.completion_tokens)
                
                logger.info(f"OpenAI call successful - Model: {model}, Duration: {duration:.3f}s")
                return result
                
            except Exception as e:
                # Incrémenter les métriques d'erreur
                openai_requests_total.labels(
                    model=model,
                    endpoint=endpoint,
                    status="error"
                ).inc()
                
                duration = time.time() - start_time
                logger.error(f"OpenAI call failed - Model: {model}, Duration: {duration:.3f}s, Error: {str(e)}")
                raise
                
        return wrapper
    return decorator


def monitor_faiss_search(operation: str = "similarity_search"):
    """
    Décorateur pour monitorer les recherches FAISS
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # Exécuter la fonction
                result = func(*args, **kwargs)
                
                # Mesurer la durée
                duration = time.time() - start_time
                
                # Enregistrer la durée
                faiss_search_duration_seconds.labels(
                    operation=operation
                ).observe(duration)
                
                # Compter le nombre de résultats
                if isinstance(result, list):
                    faiss_search_results_count.labels(
                        operation=operation
                    ).inc(len(result))
                
                logger.info(f"FAISS search successful - Operation: {operation}, Duration: {duration:.3f}s, Results: {len(result) if isinstance(result, list) else 'N/A'}")
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"FAISS search failed - Operation: {operation}, Duration: {duration:.3f}s, Error: {str(e)}")
                raise
                
        return wrapper
    return decorator


def track_conversation_status(status: str):
    """
    Fonction pour tracker le statut des conversations
    """
    chatbot_conversations_total.labels(status=status).inc()
    logger.info(f"Conversation status updated: {status}")


def track_message_type(message_type: str):
    """
    Fonction pour tracker le type de message
    """
    chatbot_messages_total.labels(type=message_type).inc()
    logger.info(f"Message tracked: {message_type}")


class OpenAIMonitor:
    """
    Classe pour monitorer les appels OpenAI avec plus de détails
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            if exc_type is None:
                # Succès
                openai_requests_total.labels(
                    model=self.model,
                    endpoint="chat/completions",
                    status="success"
                ).inc()
                
                openai_request_duration_seconds.labels(
                    model=self.model,
                    endpoint="chat/completions"
                ).observe(duration)
                
                logger.info(f"OpenAI call completed - Model: {self.model}, Duration: {duration:.3f}s")
            else:
                # Erreur
                openai_requests_total.labels(
                    model=self.model,
                    endpoint="chat/completions",
                    status="error"
                ).inc()
                
                logger.error(f"OpenAI call failed - Model: {self.model}, Duration: {duration:.3f}s, Error: {str(exc_val)}")


class FAISSMonitor:
    """
    Classe pour monitorer les recherches FAISS
    """
    
    def __init__(self, operation: str = "similarity_search"):
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            if exc_type is None:
                faiss_search_duration_seconds.labels(
                    operation=self.operation
                ).observe(duration)
                
                logger.info(f"FAISS search completed - Operation: {self.operation}, Duration: {duration:.3f}s")
            else:
                logger.error(f"FAISS search failed - Operation: {self.operation}, Duration: {duration:.3f}s, Error: {str(exc_val)}")


def get_monitoring_stats() -> Dict[str, Any]:
    """
    Récupérer les statistiques de monitoring
    """
    return {
        "openai_requests_total": openai_requests_total._value.sum(),
        "faiss_searches_total": faiss_search_results_count._value.sum(),
        "chatbot_conversations_total": chatbot_conversations_total._value.sum(),
        "chatbot_messages_total": chatbot_messages_total._value.sum()
    }
