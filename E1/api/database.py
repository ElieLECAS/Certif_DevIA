from sqlmodel import SQLModel, Session, create_engine
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de la base de données PostgreSQL
DB_HOST = os.getenv('POSTGRES_HOST', 'db')
DB_NAME = os.getenv('POSTGRES_DB', 'production')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'example')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """
    Les tables de production sont créées par le script d'extraction des logs (ftp_log_service.py).
    Cette fonction crée uniquement la table user nécessaire pour l'authentification de l'API.
    """
    # Importer seulement le modèle User pour créer sa table
    from auth.models import User
    
    # Créer uniquement la table user
    User.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session 