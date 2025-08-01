"""Application FastAPI principale du chatbot SAV."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
import uvicorn
import os

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
    
    # Shutdown (optionnel)
    print("🔄 Arrêt de l'application...")

# FastAPI app avec lifespan
app = FastAPI(
    title="Chatbot SAV", 
    description="Application de chatbot pour le service après-vente",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files et templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Importer et inclure les routes
from routes import router
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 
