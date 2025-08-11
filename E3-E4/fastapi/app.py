"""Application FastAPI principale du chatbot SAV."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler as fastapi_http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, RedirectResponse, JSONResponse
import uvicorn
import os
import time
import logging
from urllib.parse import quote

# Fonction de lifespan pour remplacer @app.on_event
def create_default_admin(db):
    """Créer l'utilisateur administrateur par défaut si nécessaire."""
    from models import User
    from auth import get_password_hash

    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        # Vérifier et définir les valeurs par défaut si les variables d'environnement ne sont pas définies
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        admin = User(
            username=admin_username,
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        db.add(admin)
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise la base et crée l'administrateur."""
    import asyncio

    from database import SessionLocal, engine
    from models import Base

    max_retries = 5
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            with SessionLocal() as db:
                create_default_admin(db)
            break
        except OperationalError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
            else:
                raise e
    
    yield


# Lecture des variables d'environnement pour DEBUG/ENVIRONMENT
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
DEBUG = os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"} or ENVIRONMENT in {"dev", "development"}

# Config niveau de logs
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

# FastAPI app avec lifespan
app = FastAPI(
    title="Chatbot SAV", 
    description="Application de chatbot pour le service après-vente",
    lifespan=lifespan
)

# Configuration CORS
# En dev (DEBUG=True), autoriser toutes les origines; en prod, restreindre
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
cors_allow_origins = ["*"] if DEBUG else ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Métriques Prometheus
http_requests_total = Counter(
    'http_requests_total',
    'Total des requêtes HTTP',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Durée des requêtes HTTP',
    ['method', 'endpoint']
)

http_requests_in_flight = Gauge(
    'http_requests_in_flight',
    'Requêtes HTTP en cours',
    ['method', 'endpoint']
)

# Métriques personnalisées pour OpenAI et FAISS
openai_requests_total = Counter(
    'openai_requests_total',
    'Total des requêtes OpenAI',
    ['model', 'endpoint', 'status']
)

openai_request_duration_seconds = Histogram(
    'openai_request_duration_seconds',
    'Durée des requêtes OpenAI',
    ['model', 'endpoint']
)

openai_response_tokens = Counter(
    'openai_response_tokens',
    'Nombre total de tokens dans les réponses OpenAI',
    ['model', 'endpoint']
)

openai_request_tokens = Counter(
    'openai_request_tokens',
    'Nombre total de tokens dans les requêtes OpenAI',
    ['model', 'endpoint']
)

faiss_search_duration_seconds = Histogram(
    'faiss_search_duration_seconds',
    'Durée des recherches FAISS',
    ['operation']
)

faiss_search_results_count = Counter(
    'faiss_search_results_count',
    'Nombre de résultats de recherche FAISS',
    ['operation']
)

chatbot_conversations_total = Counter(
    'chatbot_conversations_total',
    'Total des conversations du chatbot',
    ['status']
)

chatbot_messages_total = Counter(
    'chatbot_messages_total',
    'Total des messages du chatbot',
    ['type']
)

# Métriques d'erreurs détaillées
http_errors_total = Counter(
    'http_errors_total',
    'Total des erreurs HTTP',
    ['method', 'endpoint', 'status', 'error_type']
)

# Middleware pour collecter les métriques
@app.middleware("http")
async def collect_metrics(request, call_next):
    start_time = time.time()
    
    # Incrémenter les requêtes en cours
    http_requests_in_flight.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Enregistrer les métriques
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Enregistrer les erreurs
        if response.status_code >= 400:
            error_type = "client_error" if response.status_code < 500 else "server_error"
            http_errors_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
                error_type=error_type
            ).inc()
        
        return response
        
    except Exception as e:
        # Enregistrer les exceptions
        http_errors_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500,
            error_type="exception"
        ).inc()
        raise
    finally:
        # Décrémenter les requêtes en cours
        http_requests_in_flight.labels(
            method=request.method,
            endpoint=request.url.path
        ).dec()

# Gestionnaire global pour rediriger les 401 vers /login pour les pages HTML
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Redirection uniquement pour les 401 côté pages HTML
    if exc.status_code == 401:
        accept_header = request.headers.get("accept", "")
        is_api = request.url.path.startswith("/api")
        expects_json = "application/json" in accept_header

        # Pour l'API ou les requêtes JSON, conserver la réponse 401 JSON
        if is_api or expects_json:
            headers = getattr(exc, "headers", None) or {}
            return JSONResponse({"detail": exc.detail}, status_code=401, headers=headers)

        # Pour les pages, rediriger vers /login avec le paramètre next
        next_path = request.url.path or "/"
        query = request.url.query
        if query:
            next_path = f"{next_path}?{query}"
        response = RedirectResponse(url=f"/login?next={quote(next_path)}", status_code=302)
        # Supprimer un éventuel cookie expiré pour éviter des boucles
        response.delete_cookie(key="access_token")
        return response

    # Pour les autres codes, utiliser le gestionnaire par défaut de FastAPI
    return await fastapi_http_exception_handler(request, exc)

# Gestion dédiée des 404 (pages HTML vs API)
@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        is_api = request.url.path.startswith("/api")

        # Pour l'API, garder JSON; pour les pages, afficher un template HTML, 
        # même si l'entête Accept inclut application/json (navigation navigateur)
        if is_api:
            return JSONResponse({"detail": exc.detail or "Not Found"}, status_code=404)

        # Page HTML 404 simple
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "status_code": 404, "message": "Page non trouvée"},
            status_code=404,
        )

    # Laisser le gestionnaire par défaut pour les autres codes
    return await fastapi_http_exception_handler(request, exc)

# Endpoint pour les métriques Prometheus
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Static files et templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# En dev, activer l'auto-reload des templates
templates.env.auto_reload = DEBUG

# Importer et inclure les routes
from routes import router
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=DEBUG, log_level=("debug" if DEBUG else "info")) 
