"""Application FastAPI principale du chatbot SAV."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import uvicorn
import os
import time

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


# FastAPI app avec lifespan
app = FastAPI(
    title="Chatbot SAV", 
    description="Application de chatbot pour le service après-vente",
    lifespan=lifespan
)

# Configuration CORS
# Récupérer les origines autorisées depuis les variables d'environnement
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

# Endpoint pour les métriques Prometheus
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Static files et templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Importer et inclure les routes
from routes import router
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 
