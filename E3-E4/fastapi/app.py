from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime

# Fonction de lifespan pour remplacer @app.on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    import asyncio
    import time
    
    # Attendre que la base de données soit prête avec retry
    max_retries = 10
    for attempt in range(max_retries):
        try:
            from models import Base, User
            from database import SessionLocal, engine
            from auth import get_password_hash
            
            # Tester la connexion en créant les tables
            Base.metadata.create_all(bind=engine)
            print("✅ Tables créées avec succès")
            
            # Créer l'utilisateur admin par défaut
            db = SessionLocal()
            try:
                
                # Créer l'utilisateur admin
                admin_user = db.query(User).filter(User.username == "admin").first()
                if not admin_user:
                    admin_user = User(
                        username="admin",
                        email="admin@chatbot-sav.com",
                        hashed_password=get_password_hash("admin123"),
                        is_active=True,
                        is_staff=True,
                        is_superuser=True
                    )
                    db.add(admin_user)
                    db.commit()
                    print("✅ Utilisateur admin créé avec succès")
                    print("   👤 Username: admin")
                    print("   🔑 Password: admin123")
                    print("   📧 Email: admin@chatbot-sav.com")
                else:
                    print("ℹ️  Utilisateur admin existe déjà")
                

                
                break  # Sortir de la boucle si tout va bien
            except Exception as e:
                print(f"⚠️  Erreur lors de la création des utilisateurs: {e}")
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️  Tentative {attempt + 1}/{max_retries} - Erreur de connexion DB: {e}")
            if attempt < max_retries - 1:
                print("⏳ Nouvelle tentative dans 3 secondes...")
                await asyncio.sleep(3)
            else:
                print("❌ Impossible de se connecter à la base de données après plusieurs tentatives")
                print("Les tables seront créées lors de la première requête")
    
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