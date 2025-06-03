from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional
from datetime import date, datetime
import models
import schemas

# CRUD pour CentreUsinage
def get_centre_usinage(db: Session, centre_id: int):
    return db.query(models.CentreUsinage).filter(models.CentreUsinage.id == centre_id).first()

def get_centre_usinage_by_nom(db: Session, nom: str):
    return db.query(models.CentreUsinage).filter(models.CentreUsinage.nom == nom).first()

def get_centres_usinage(db: Session, skip: int = 0, limit: int = 100, actif_only: bool = True):
    query = db.query(models.CentreUsinage)
    if actif_only:
        query = query.filter(models.CentreUsinage.actif == True)
    return query.offset(skip).limit(limit).all()

def create_centre_usinage(db: Session, centre: schemas.CentreUsinageCreate):
    db_centre = models.CentreUsinage(**centre.model_dump())
    db.add(db_centre)
    db.commit()
    db.refresh(db_centre)
    return db_centre

def update_centre_usinage(db: Session, centre_id: int, centre: schemas.CentreUsinageUpdate):
    db_centre = db.query(models.CentreUsinage).filter(models.CentreUsinage.id == centre_id).first()
    if db_centre:
        update_data = centre.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_centre, field, value)
        db.commit()
        db.refresh(db_centre)
    return db_centre

def delete_centre_usinage(db: Session, centre_id: int):
    db_centre = db.query(models.CentreUsinage).filter(models.CentreUsinage.id == centre_id).first()
    if db_centre:
        db.delete(db_centre)
        db.commit()
    return db_centre

# CRUD pour SessionProduction
def get_session_production(db: Session, session_id: int):
    return db.query(models.SessionProduction).filter(models.SessionProduction.id == session_id).first()

def get_sessions_production(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    centre_usinage_id: Optional[int] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None
):
    query = db.query(models.SessionProduction)
    
    if centre_usinage_id:
        query = query.filter(models.SessionProduction.centre_usinage_id == centre_usinage_id)
    
    if date_debut:
        query = query.filter(models.SessionProduction.date_production >= date_debut)
    
    if date_fin:
        query = query.filter(models.SessionProduction.date_production <= date_fin)
    
    return query.order_by(desc(models.SessionProduction.date_production)).offset(skip).limit(limit).all()

def get_session_production_with_details(db: Session, session_id: int):
    return db.query(models.SessionProduction).filter(
        models.SessionProduction.id == session_id
    ).first()

def create_session_production(db: Session, session: schemas.SessionProductionCreate):
    db_session = models.SessionProduction(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_session_production(db: Session, session_id: int, session: schemas.SessionProductionUpdate):
    db_session = db.query(models.SessionProduction).filter(models.SessionProduction.id == session_id).first()
    if db_session:
        update_data = session.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_session, field, value)
        db.commit()
        db.refresh(db_session)
    return db_session

def delete_session_production(db: Session, session_id: int):
    db_session = db.query(models.SessionProduction).filter(models.SessionProduction.id == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return db_session

# CRUD pour JobProfil
def get_job_profil(db: Session, job_id: int):
    return db.query(models.JobProfil).filter(models.JobProfil.id == job_id).first()

def get_job_profils(db: Session, skip: int = 0, limit: int = 100, session_id: Optional[int] = None):
    query = db.query(models.JobProfil)
    if session_id:
        query = query.filter(models.JobProfil.session_id == session_id)
    return query.offset(skip).limit(limit).all()

def create_job_profil(db: Session, job: schemas.JobProfilCreate):
    db_job = models.JobProfil(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job_profil(db: Session, job_id: int, job: schemas.JobProfilUpdate):
    db_job = db.query(models.JobProfil).filter(models.JobProfil.id == job_id).first()
    if db_job:
        update_data = job.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_job, field, value)
        db.commit()
        db.refresh(db_job)
    return db_job

def delete_job_profil(db: Session, job_id: int):
    db_job = db.query(models.JobProfil).filter(models.JobProfil.id == job_id).first()
    if db_job:
        db.delete(db_job)
        db.commit()
    return db_job

# CRUD pour PeriodeAttente
def get_periode_attente(db: Session, periode_id: int):
    return db.query(models.PeriodeAttente).filter(models.PeriodeAttente.id == periode_id).first()

def get_periodes_attente(db: Session, skip: int = 0, limit: int = 100, session_id: Optional[int] = None):
    query = db.query(models.PeriodeAttente)
    if session_id:
        query = query.filter(models.PeriodeAttente.session_id == session_id)
    return query.offset(skip).limit(limit).all()

def create_periode_attente(db: Session, periode: schemas.PeriodeAttenteCreate):
    db_periode = models.PeriodeAttente(**periode.model_dump())
    db.add(db_periode)
    db.commit()
    db.refresh(db_periode)
    return db_periode

def update_periode_attente(db: Session, periode_id: int, periode: schemas.PeriodeAttenteUpdate):
    db_periode = db.query(models.PeriodeAttente).filter(models.PeriodeAttente.id == periode_id).first()
    if db_periode:
        update_data = periode.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_periode, field, value)
        db.commit()
        db.refresh(db_periode)
    return db_periode

def delete_periode_attente(db: Session, periode_id: int):
    db_periode = db.query(models.PeriodeAttente).filter(models.PeriodeAttente.id == periode_id).first()
    if db_periode:
        db.delete(db_periode)
        db.commit()
    return db_periode

# CRUD pour PeriodeArret
def get_periode_arret(db: Session, periode_id: int):
    return db.query(models.PeriodeArret).filter(models.PeriodeArret.id == periode_id).first()

def get_periodes_arret(db: Session, skip: int = 0, limit: int = 100, session_id: Optional[int] = None):
    query = db.query(models.PeriodeArret)
    if session_id:
        query = query.filter(models.PeriodeArret.session_id == session_id)
    return query.offset(skip).limit(limit).all()

def create_periode_arret(db: Session, periode: schemas.PeriodeArretCreate):
    db_periode = models.PeriodeArret(**periode.model_dump())
    db.add(db_periode)
    db.commit()
    db.refresh(db_periode)
    return db_periode

def update_periode_arret(db: Session, periode_id: int, periode: schemas.PeriodeArretUpdate):
    db_periode = db.query(models.PeriodeArret).filter(models.PeriodeArret.id == periode_id).first()
    if db_periode:
        update_data = periode.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_periode, field, value)
        db.commit()
        db.refresh(db_periode)
    return db_periode

def delete_periode_arret(db: Session, periode_id: int):
    db_periode = db.query(models.PeriodeArret).filter(models.PeriodeArret.id == periode_id).first()
    if db_periode:
        db.delete(db_periode)
        db.commit()
    return db_periode

# CRUD pour PieceProduction
def get_piece_production(db: Session, piece_id: int):
    return db.query(models.PieceProduction).filter(models.PieceProduction.id == piece_id).first()

def get_pieces_production(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    session_id: Optional[int] = None,
    date_debut: Optional[datetime] = None,
    date_fin: Optional[datetime] = None
):
    query = db.query(models.PieceProduction)
    
    if session_id:
        query = query.filter(models.PieceProduction.session_id == session_id)
    
    if date_debut:
        query = query.filter(models.PieceProduction.timestamp_production >= date_debut)
    
    if date_fin:
        query = query.filter(models.PieceProduction.timestamp_production <= date_fin)
    
    return query.order_by(desc(models.PieceProduction.timestamp_production)).offset(skip).limit(limit).all()

def create_piece_production(db: Session, piece: schemas.PieceProductionCreate):
    db_piece = models.PieceProduction(**piece.model_dump())
    db.add(db_piece)
    db.commit()
    db.refresh(db_piece)
    return db_piece

def update_piece_production(db: Session, piece_id: int, piece: schemas.PieceProductionUpdate):
    db_piece = db.query(models.PieceProduction).filter(models.PieceProduction.id == piece_id).first()
    if db_piece:
        update_data = piece.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_piece, field, value)
        db.commit()
        db.refresh(db_piece)
    return db_piece

def delete_piece_production(db: Session, piece_id: int):
    db_piece = db.query(models.PieceProduction).filter(models.PieceProduction.id == piece_id).first()
    if db_piece:
        db.delete(db_piece)
        db.commit()
    return db_piece

# Fonctions de statistiques et d'analyse
def get_production_stats_by_centre(db: Session, centre_usinage_id: int, date_debut: Optional[date] = None, date_fin: Optional[date] = None):
    """Obtenir les statistiques de production pour un centre d'usinage"""
    query = db.query(models.SessionProduction).filter(models.SessionProduction.centre_usinage_id == centre_usinage_id)
    
    if date_debut:
        query = query.filter(models.SessionProduction.date_production >= date_debut)
    
    if date_fin:
        query = query.filter(models.SessionProduction.date_production <= date_fin)
    
    return query.all()

def get_production_summary(db: Session):
    """Obtenir un résumé global de la production"""
    return db.query(
        models.CentreUsinage.nom,
        models.CentreUsinage.type_cu,
        db.func.count(models.SessionProduction.id).label('total_sessions'),
        db.func.sum(models.SessionProduction.total_pieces).label('total_pieces'),
        db.func.avg(models.SessionProduction.taux_occupation).label('taux_occupation_moyen')
    ).join(
        models.SessionProduction, models.CentreUsinage.id == models.SessionProduction.centre_usinage_id
    ).group_by(
        models.CentreUsinage.id, models.CentreUsinage.nom, models.CentreUsinage.type_cu
    ).all() 