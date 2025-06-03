from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class CentreUsinage(Base):
    __tablename__ = "centre_usinage"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False, index=True)
    type_cu = Column(String(50), nullable=False)
    description = Column(Text)
    actif = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    sessions_production = relationship("SessionProduction", back_populates="centre_usinage")

class SessionProduction(Base):
    __tablename__ = "session_production"
    
    id = Column(Integer, primary_key=True, index=True)
    centre_usinage_id = Column(Integer, ForeignKey("centre_usinage.id"))
    date_production = Column(Date, nullable=False, index=True)
    heure_premiere_piece = Column(DateTime)
    heure_derniere_piece = Column(DateTime)
    heure_premier_machine_start = Column(DateTime)
    heure_dernier_machine_stop = Column(DateTime)
    total_pieces = Column(Integer, default=0)
    duree_production_totale = Column(Numeric(10, 4))
    temps_attente = Column(Numeric(10, 4))
    temps_arret_volontaire = Column(Numeric(10, 4))
    temps_production_effectif = Column(Numeric(10, 4))
    taux_occupation = Column(Numeric(5, 2))
    taux_attente = Column(Numeric(5, 2))
    taux_arret_volontaire = Column(Numeric(5, 2))
    fichier_log_source = Column(String(255))
    date_creation = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    centre_usinage = relationship("CentreUsinage", back_populates="sessions_production")
    job_profils = relationship("JobProfil", back_populates="session")
    periodes_attente = relationship("PeriodeAttente", back_populates="session")
    periodes_arret = relationship("PeriodeArret", back_populates="session")
    pieces_production = relationship("PieceProduction", back_populates="session")

class JobProfil(Base):
    __tablename__ = "job_profil"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("session_production.id"))
    reference = Column(String(50), nullable=False)
    longueur = Column(Numeric(10, 2))
    couleur = Column(String(50))
    timestamp_debut = Column(DateTime)
    date_creation = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    session = relationship("SessionProduction", back_populates="job_profils")

class PeriodeAttente(Base):
    __tablename__ = "periode_attente"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("session_production.id"))
    timestamp_debut = Column(DateTime, nullable=False)
    timestamp_fin = Column(DateTime, nullable=False)
    duree_secondes = Column(Integer, nullable=False)
    date_creation = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    session = relationship("SessionProduction", back_populates="periodes_attente")

class PeriodeArret(Base):
    __tablename__ = "periode_arret"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("session_production.id"))
    timestamp_debut = Column(DateTime, nullable=False)
    timestamp_fin = Column(DateTime, nullable=False)
    duree_secondes = Column(Integer, nullable=False)
    date_creation = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    session = relationship("SessionProduction", back_populates="periodes_arret")

class PieceProduction(Base):
    __tablename__ = "piece_production"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("session_production.id"))
    numero_piece = Column(Integer, nullable=False)
    timestamp_production = Column(DateTime, nullable=False)
    details = Column(Text)
    date_creation = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    session = relationship("SessionProduction", back_populates="pieces_production") 