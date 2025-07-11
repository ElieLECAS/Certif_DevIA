from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from decimal import Decimal

class CentreUsinageBase(SQLModel):
    nom: str = Field(unique=True, index=True)
    type_cu: str
    description: Optional[str] = None
    actif: bool = Field(default=True)

class CentreUsinage(CentreUsinageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    sessions_production: List["SessionProduction"] = Relationship(back_populates="centre_usinage")

class SessionProductionBase(SQLModel):
    centre_usinage_id: int = Field(foreign_key="centreusinage.id")
    date_production: date
    heure_premiere_piece: Optional[datetime] = None
    heure_derniere_piece: Optional[datetime] = None
    heure_premier_machine_start: Optional[datetime] = None
    heure_dernier_machine_stop: Optional[datetime] = None
    total_pieces: int = Field(default=0)
    duree_production_totale: float = Field(default=0)
    temps_attente: float = Field(default=0)
    temps_arret_volontaire: float = Field(default=0)
    temps_production_effectif: float = Field(default=0)
    taux_occupation: float = Field(default=0)
    taux_attente: float = Field(default=0)
    taux_arret_volontaire: float = Field(default=0)
    fichier_log_source: Optional[str] = None

class SessionProduction(SessionProductionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    centre_usinage: CentreUsinage = Relationship(back_populates="sessions_production")
    job_profils: List["JobProfil"] = Relationship(back_populates="session")
    periodes_attente: List["PeriodeAttente"] = Relationship(back_populates="session")
    periodes_arret: List["PeriodeArret"] = Relationship(back_populates="session")
    pieces_production: List["PieceProduction"] = Relationship(back_populates="session")

class JobProfilBase(SQLModel):
    session_id: int = Field(foreign_key="sessionproduction.id")
    reference: str
    longueur: Optional[float] = None
    couleur: Optional[str] = None
    timestamp_debut: Optional[datetime] = None

class JobProfil(JobProfilBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    session: SessionProduction = Relationship(back_populates="job_profils")

class PeriodeAttenteBase(SQLModel):
    session_id: int = Field(foreign_key="sessionproduction.id")
    timestamp_debut: datetime
    timestamp_fin: datetime
    duree_secondes: int

class PeriodeAttente(PeriodeAttenteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    session: SessionProduction = Relationship(back_populates="periodes_attente")

class PeriodeArretBase(SQLModel):
    session_id: int = Field(foreign_key="sessionproduction.id")
    timestamp_debut: datetime
    timestamp_fin: datetime
    duree_secondes: int

class PeriodeArret(PeriodeArretBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    session: SessionProduction = Relationship(back_populates="periodes_arret")

class PieceProductionBase(SQLModel):
    session_id: int = Field(foreign_key="sessionproduction.id")
    numero_piece: int
    timestamp_production: datetime
    details: Optional[str] = None

class PieceProduction(PieceProductionBase, table=True):
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