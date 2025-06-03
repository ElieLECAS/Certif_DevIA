from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# Schémas de base pour CentreUsinage
class CentreUsinageBase(BaseModel):
    nom: str
    type_cu: str
    description: Optional[str] = None
    actif: bool = True

class CentreUsinageCreate(CentreUsinageBase):
    pass

class CentreUsinageUpdate(BaseModel):
    nom: Optional[str] = None
    type_cu: Optional[str] = None
    description: Optional[str] = None
    actif: Optional[bool] = None

class CentreUsinage(CentreUsinageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: datetime

# Schémas de base pour SessionProduction
class SessionProductionBase(BaseModel):
    centre_usinage_id: int
    date_production: date
    heure_premiere_piece: Optional[datetime] = None
    heure_derniere_piece: Optional[datetime] = None
    heure_premier_machine_start: Optional[datetime] = None
    heure_dernier_machine_stop: Optional[datetime] = None
    total_pieces: int = 0
    duree_production_totale: Optional[Decimal] = None
    temps_attente: Optional[Decimal] = None
    temps_arret_volontaire: Optional[Decimal] = None
    temps_production_effectif: Optional[Decimal] = None
    taux_occupation: Optional[Decimal] = None
    taux_attente: Optional[Decimal] = None
    taux_arret_volontaire: Optional[Decimal] = None
    fichier_log_source: Optional[str] = None

class SessionProductionCreate(SessionProductionBase):
    pass

class SessionProductionUpdate(BaseModel):
    centre_usinage_id: Optional[int] = None
    date_production: Optional[date] = None
    heure_premiere_piece: Optional[datetime] = None
    heure_derniere_piece: Optional[datetime] = None
    heure_premier_machine_start: Optional[datetime] = None
    heure_dernier_machine_stop: Optional[datetime] = None
    total_pieces: Optional[int] = None
    duree_production_totale: Optional[Decimal] = None
    temps_attente: Optional[Decimal] = None
    temps_arret_volontaire: Optional[Decimal] = None
    temps_production_effectif: Optional[Decimal] = None
    taux_occupation: Optional[Decimal] = None
    taux_attente: Optional[Decimal] = None
    taux_arret_volontaire: Optional[Decimal] = None
    fichier_log_source: Optional[str] = None

class SessionProduction(SessionProductionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: datetime
    centre_usinage: Optional[CentreUsinage] = None

# Schémas de base pour JobProfil
class JobProfilBase(BaseModel):
    session_id: int
    reference: str
    longueur: Optional[Decimal] = None
    couleur: Optional[str] = None
    timestamp_debut: Optional[datetime] = None

class JobProfilCreate(JobProfilBase):
    pass

class JobProfilUpdate(BaseModel):
    session_id: Optional[int] = None
    reference: Optional[str] = None
    longueur: Optional[Decimal] = None
    couleur: Optional[str] = None
    timestamp_debut: Optional[datetime] = None

class JobProfil(JobProfilBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: datetime

# Schémas de base pour PeriodeAttente
class PeriodeAttenteBase(BaseModel):
    session_id: int
    timestamp_debut: datetime
    timestamp_fin: datetime
    duree_secondes: int

class PeriodeAttenteCreate(PeriodeAttenteBase):
    pass

class PeriodeAttenteUpdate(BaseModel):
    session_id: Optional[int] = None
    timestamp_debut: Optional[datetime] = None
    timestamp_fin: Optional[datetime] = None
    duree_secondes: Optional[int] = None

class PeriodeAttente(PeriodeAttenteBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: datetime

# Schémas de base pour PeriodeArret
class PeriodeArretBase(BaseModel):
    session_id: int
    timestamp_debut: datetime
    timestamp_fin: datetime
    duree_secondes: int

class PeriodeArretCreate(PeriodeArretBase):
    pass

class PeriodeArretUpdate(BaseModel):
    session_id: Optional[int] = None
    timestamp_debut: Optional[datetime] = None
    timestamp_fin: Optional[datetime] = None
    duree_secondes: Optional[int] = None

class PeriodeArret(PeriodeArretBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: datetime

# Schémas de base pour PieceProduction
class PieceProductionBase(BaseModel):
    session_id: int
    numero_piece: int
    timestamp_production: datetime
    details: Optional[str] = None

class PieceProductionCreate(PieceProductionBase):
    pass

class PieceProductionUpdate(BaseModel):
    session_id: Optional[int] = None
    numero_piece: Optional[int] = None
    timestamp_production: Optional[datetime] = None
    details: Optional[str] = None

class PieceProduction(PieceProductionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: datetime

# Schémas avec relations complètes
class SessionProductionWithDetails(SessionProduction):
    job_profils: List[JobProfil] = []
    periodes_attente: List[PeriodeAttente] = []
    periodes_arret: List[PeriodeArret] = []
    pieces_production: List[PieceProduction] = []

class CentreUsinageWithSessions(CentreUsinage):
    sessions_production: List[SessionProduction] = [] 