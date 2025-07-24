from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from decimal import Decimal

class CentreUsinageBase(SQLModel):
    nom: str = Field(unique=True, index=True, max_length=100)
    type_cu: str = Field(max_length=50)
    description: Optional[str] = None
    actif: bool = Field(default=True)

class CentreUsinage(CentreUsinageBase, table=True):
    __tablename__ = "centre_usinage"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    sessions_production: List["SessionProduction"] = Relationship(back_populates="centre_usinage")

class SessionProductionBase(SQLModel):
    centre_usinage_id: int = Field(foreign_key="centre_usinage.id")
    date_production: date
    heure_premiere_piece: Optional[datetime] = None
    heure_derniere_piece: Optional[datetime] = None
    heure_premier_machine_start: Optional[datetime] = None
    heure_dernier_machine_stop: Optional[datetime] = None
    total_pieces: int = Field(default=0)
    duree_production_totale: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=10)
    temps_attente: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=10)
    temps_arret_volontaire: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=10)
    temps_production_effectif: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=10)
    taux_occupation: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)
    taux_attente: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)
    taux_arret_volontaire: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)
    fichier_log_source: Optional[str] = Field(default=None, max_length=255)

class SessionProduction(SessionProductionBase, table=True):
    __tablename__ = "session_production"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    centre_usinage: CentreUsinage = Relationship(back_populates="sessions_production")
    job_profils: List["JobProfil"] = Relationship(back_populates="session")
    periodes_attente: List["PeriodeAttente"] = Relationship(back_populates="session")
    periodes_arret: List["PeriodeArret"] = Relationship(back_populates="session")
    pieces_production: List["PieceProduction"] = Relationship(back_populates="session")

class JobProfilBase(SQLModel):
    session_id: int = Field(foreign_key="session_production.id")
    reference: str = Field(max_length=50)
    longueur: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    couleur: Optional[str] = Field(default=None, max_length=50)
    timestamp_debut: Optional[datetime] = None

class JobProfil(JobProfilBase, table=True):
    __tablename__ = "job_profil"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    session: SessionProduction = Relationship(back_populates="job_profils")

class PeriodeAttenteBase(SQLModel):
    session_id: int = Field(foreign_key="session_production.id")
    timestamp_debut: datetime
    timestamp_fin: datetime
    duree_secondes: int

class PeriodeAttente(PeriodeAttenteBase, table=True):
    __tablename__ = "periode_attente"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    session: SessionProduction = Relationship(back_populates="periodes_attente")

class PeriodeArretBase(SQLModel):
    session_id: int = Field(foreign_key="session_production.id")
    timestamp_debut: datetime
    timestamp_fin: datetime
    duree_secondes: int

class PeriodeArret(PeriodeArretBase, table=True):
    __tablename__ = "periode_arret"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    session: SessionProduction = Relationship(back_populates="periodes_arret")

class PieceProductionBase(SQLModel):
    session_id: int = Field(foreign_key="session_production.id")
    numero_piece: int
    timestamp_production: datetime
    details: Optional[str] = None

class PieceProduction(PieceProductionBase, table=True):
    __tablename__ = "piece_production"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    session: SessionProduction = Relationship(back_populates="pieces_production")

# Modèles pour la création et la lecture
class CentreUsinageCreate(CentreUsinageBase):
    pass

class CentreUsinageRead(CentreUsinageBase):
    id: int
    date_creation: datetime

class SessionProductionCreate(SessionProductionBase):
    pass

class SessionProductionRead(SessionProductionBase):
    id: int
    date_creation: datetime

class JobProfilCreate(JobProfilBase):
    pass

class JobProfilRead(JobProfilBase):
    id: int
    date_creation: datetime

class PeriodeAttenteCreate(PeriodeAttenteBase):
    pass

class PeriodeAttenteRead(PeriodeAttenteBase):
    id: int
    date_creation: datetime

class PeriodeArretCreate(PeriodeArretBase):
    pass

class PeriodeArretRead(PeriodeArretBase):
    id: int
    date_creation: datetime

class PieceProductionCreate(PieceProductionBase):
    pass

class PieceProductionRead(PieceProductionBase):
    id: int
    date_creation: datetime 