import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de la base de données depuis les variables d'environnement
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gmao_user:gmao_password@localhost:5432/gmao_db")

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL)

# Session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

# Dépendance pour obtenir la session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 