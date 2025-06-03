from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

import crud
import models
import schemas
from database import SessionLocal, engine, get_db

# Créer les tables si elles n'existent pas
models.Base.metadata.create_all(bind=engine)

# Créer l'application FastAPI
app = FastAPI(
    title="API Production Industrielle",
    description="API CRUD pour la gestion des données de production des centres d'usinage",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes pour CentreUsinage
@app.get("/centres-usinage/", response_model=List[schemas.CentreUsinage])
def read_centres_usinage(
    skip: int = 0, 
    limit: int = 100, 
    actif_only: bool = True,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des centres d'usinage"""
    centres = crud.get_centres_usinage(db, skip=skip, limit=limit, actif_only=actif_only)
    return centres

@app.get("/centres-usinage/{centre_id}", response_model=schemas.CentreUsinageWithSessions)
def read_centre_usinage(centre_id: int, db: Session = Depends(get_db)):
    """Récupérer un centre d'usinage par son ID avec ses sessions"""
    db_centre = crud.get_centre_usinage(db, centre_id=centre_id)
    if db_centre is None:
        raise HTTPException(status_code=404, detail="Centre d'usinage non trouvé")
    return db_centre

@app.post("/centres-usinage/", response_model=schemas.CentreUsinage)
def create_centre_usinage(centre: schemas.CentreUsinageCreate, db: Session = Depends(get_db)):
    """Créer un nouveau centre d'usinage"""
    db_centre = crud.get_centre_usinage_by_nom(db, nom=centre.nom)
    if db_centre:
        raise HTTPException(status_code=400, detail="Un centre d'usinage avec ce nom existe déjà")
    return crud.create_centre_usinage(db=db, centre=centre)

@app.put("/centres-usinage/{centre_id}", response_model=schemas.CentreUsinage)
def update_centre_usinage(
    centre_id: int, 
    centre: schemas.CentreUsinageUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour un centre d'usinage"""
    db_centre = crud.update_centre_usinage(db, centre_id=centre_id, centre=centre)
    if db_centre is None:
        raise HTTPException(status_code=404, detail="Centre d'usinage non trouvé")
    return db_centre

@app.delete("/centres-usinage/{centre_id}")
def delete_centre_usinage(centre_id: int, db: Session = Depends(get_db)):
    """Supprimer un centre d'usinage"""
    db_centre = crud.delete_centre_usinage(db, centre_id=centre_id)
    if db_centre is None:
        raise HTTPException(status_code=404, detail="Centre d'usinage non trouvé")
    return {"message": "Centre d'usinage supprimé avec succès"}

# Routes pour SessionProduction
@app.get("/sessions-production/", response_model=List[schemas.SessionProduction])
def read_sessions_production(
    skip: int = 0,
    limit: int = 100,
    centre_usinage_id: Optional[int] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des sessions de production avec filtres optionnels"""
    sessions = crud.get_sessions_production(
        db, 
        skip=skip, 
        limit=limit, 
        centre_usinage_id=centre_usinage_id,
        date_debut=date_debut,
        date_fin=date_fin
    )
    return sessions

@app.get("/sessions-production/{session_id}", response_model=schemas.SessionProductionWithDetails)
def read_session_production(session_id: int, db: Session = Depends(get_db)):
    """Récupérer une session de production avec tous ses détails"""
    db_session = crud.get_session_production_with_details(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session de production non trouvée")
    return db_session

@app.post("/sessions-production/", response_model=schemas.SessionProduction)
def create_session_production(session: schemas.SessionProductionCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle session de production"""
    return crud.create_session_production(db=db, session=session)

@app.put("/sessions-production/{session_id}", response_model=schemas.SessionProduction)
def update_session_production(
    session_id: int, 
    session: schemas.SessionProductionUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour une session de production"""
    db_session = crud.update_session_production(db, session_id=session_id, session=session)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session de production non trouvée")
    return db_session

@app.delete("/sessions-production/{session_id}")
def delete_session_production(session_id: int, db: Session = Depends(get_db)):
    """Supprimer une session de production"""
    db_session = crud.delete_session_production(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session de production non trouvée")
    return {"message": "Session de production supprimée avec succès"}

# Routes pour JobProfil
@app.get("/job-profils/", response_model=List[schemas.JobProfil])
def read_job_profils(
    skip: int = 0,
    limit: int = 100,
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des profils de jobs"""
    jobs = crud.get_job_profils(db, skip=skip, limit=limit, session_id=session_id)
    return jobs

@app.get("/job-profils/{job_id}", response_model=schemas.JobProfil)
def read_job_profil(job_id: int, db: Session = Depends(get_db)):
    """Récupérer un profil de job par son ID"""
    db_job = crud.get_job_profil(db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Profil de job non trouvé")
    return db_job

@app.post("/job-profils/", response_model=schemas.JobProfil)
def create_job_profil(job: schemas.JobProfilCreate, db: Session = Depends(get_db)):
    """Créer un nouveau profil de job"""
    return crud.create_job_profil(db=db, job=job)

@app.put("/job-profils/{job_id}", response_model=schemas.JobProfil)
def update_job_profil(job_id: int, job: schemas.JobProfilUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un profil de job"""
    db_job = crud.update_job_profil(db, job_id=job_id, job=job)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Profil de job non trouvé")
    return db_job

@app.delete("/job-profils/{job_id}")
def delete_job_profil(job_id: int, db: Session = Depends(get_db)):
    """Supprimer un profil de job"""
    db_job = crud.delete_job_profil(db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Profil de job non trouvé")
    return {"message": "Profil de job supprimé avec succès"}

# Routes pour PeriodeAttente
@app.get("/periodes-attente/", response_model=List[schemas.PeriodeAttente])
def read_periodes_attente(
    skip: int = 0,
    limit: int = 100,
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des périodes d'attente"""
    periodes = crud.get_periodes_attente(db, skip=skip, limit=limit, session_id=session_id)
    return periodes

@app.get("/periodes-attente/{periode_id}", response_model=schemas.PeriodeAttente)
def read_periode_attente(periode_id: int, db: Session = Depends(get_db)):
    """Récupérer une période d'attente par son ID"""
    db_periode = crud.get_periode_attente(db, periode_id=periode_id)
    if db_periode is None:
        raise HTTPException(status_code=404, detail="Période d'attente non trouvée")
    return db_periode

@app.post("/periodes-attente/", response_model=schemas.PeriodeAttente)
def create_periode_attente(periode: schemas.PeriodeAttenteCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle période d'attente"""
    return crud.create_periode_attente(db=db, periode=periode)

@app.put("/periodes-attente/{periode_id}", response_model=schemas.PeriodeAttente)
def update_periode_attente(
    periode_id: int, 
    periode: schemas.PeriodeAttenteUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour une période d'attente"""
    db_periode = crud.update_periode_attente(db, periode_id=periode_id, periode=periode)
    if db_periode is None:
        raise HTTPException(status_code=404, detail="Période d'attente non trouvée")
    return db_periode

@app.delete("/periodes-attente/{periode_id}")
def delete_periode_attente(periode_id: int, db: Session = Depends(get_db)):
    """Supprimer une période d'attente"""
    db_periode = crud.delete_periode_attente(db, periode_id=periode_id)
    if db_periode is None:
        raise HTTPException(status_code=404, detail="Période d'attente non trouvée")
    return {"message": "Période d'attente supprimée avec succès"}

# Routes pour PeriodeArret
@app.get("/periodes-arret/", response_model=List[schemas.PeriodeArret])
def read_periodes_arret(
    skip: int = 0,
    limit: int = 100,
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des périodes d'arrêt"""
    periodes = crud.get_periodes_arret(db, skip=skip, limit=limit, session_id=session_id)
    return periodes

@app.get("/periodes-arret/{periode_id}", response_model=schemas.PeriodeArret)
def read_periode_arret(periode_id: int, db: Session = Depends(get_db)):
    """Récupérer une période d'arrêt par son ID"""
    db_periode = crud.get_periode_arret(db, periode_id=periode_id)
    if db_periode is None:
        raise HTTPException(status_code=404, detail="Période d'arrêt non trouvée")
    return db_periode

@app.post("/periodes-arret/", response_model=schemas.PeriodeArret)
def create_periode_arret(periode: schemas.PeriodeArretCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle période d'arrêt"""
    return crud.create_periode_arret(db=db, periode=periode)

@app.put("/periodes-arret/{periode_id}", response_model=schemas.PeriodeArret)
def update_periode_arret(
    periode_id: int, 
    periode: schemas.PeriodeArretUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour une période d'arrêt"""
    db_periode = crud.update_periode_arret(db, periode_id=periode_id, periode=periode)
    if db_periode is None:
        raise HTTPException(status_code=404, detail="Période d'arrêt non trouvée")
    return db_periode

@app.delete("/periodes-arret/{periode_id}")
def delete_periode_arret(periode_id: int, db: Session = Depends(get_db)):
    """Supprimer une période d'arrêt"""
    db_periode = crud.delete_periode_arret(db, periode_id=periode_id)
    if db_periode is None:
        raise HTTPException(status_code=404, detail="Période d'arrêt non trouvée")
    return {"message": "Période d'arrêt supprimée avec succès"}

# Routes pour PieceProduction
@app.get("/pieces-production/", response_model=List[schemas.PieceProduction])
def read_pieces_production(
    skip: int = 0,
    limit: int = 100,
    session_id: Optional[int] = None,
    date_debut: Optional[datetime] = None,
    date_fin: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des pièces produites avec filtres optionnels"""
    pieces = crud.get_pieces_production(
        db, 
        skip=skip, 
        limit=limit, 
        session_id=session_id,
        date_debut=date_debut,
        date_fin=date_fin
    )
    return pieces

@app.get("/pieces-production/{piece_id}", response_model=schemas.PieceProduction)
def read_piece_production(piece_id: int, db: Session = Depends(get_db)):
    """Récupérer une pièce produite par son ID"""
    db_piece = crud.get_piece_production(db, piece_id=piece_id)
    if db_piece is None:
        raise HTTPException(status_code=404, detail="Pièce produite non trouvée")
    return db_piece

@app.post("/pieces-production/", response_model=schemas.PieceProduction)
def create_piece_production(piece: schemas.PieceProductionCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle pièce produite"""
    return crud.create_piece_production(db=db, piece=piece)

@app.put("/pieces-production/{piece_id}", response_model=schemas.PieceProduction)
def update_piece_production(
    piece_id: int, 
    piece: schemas.PieceProductionUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour une pièce produite"""
    db_piece = crud.update_piece_production(db, piece_id=piece_id, piece=piece)
    if db_piece is None:
        raise HTTPException(status_code=404, detail="Pièce produite non trouvée")
    return db_piece

@app.delete("/pieces-production/{piece_id}")
def delete_piece_production(piece_id: int, db: Session = Depends(get_db)):
    """Supprimer une pièce produite"""
    db_piece = crud.delete_piece_production(db, piece_id=piece_id)
    if db_piece is None:
        raise HTTPException(status_code=404, detail="Pièce produite non trouvée")
    return {"message": "Pièce produite supprimée avec succès"}

# Routes de statistiques et d'analyse
@app.get("/stats/production-summary")
def get_production_summary(db: Session = Depends(get_db)):
    """Obtenir un résumé global de la production"""
    summary = crud.get_production_summary(db)
    return [
        {
            "nom_centre": row.nom,
            "type_cu": row.type_cu,
            "total_sessions": row.total_sessions,
            "total_pieces": row.total_pieces,
            "taux_occupation_moyen": float(row.taux_occupation_moyen) if row.taux_occupation_moyen else None
        }
        for row in summary
    ]

@app.get("/stats/production-by-centre/{centre_usinage_id}")
def get_production_stats_by_centre(
    centre_usinage_id: int,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Obtenir les statistiques de production pour un centre d'usinage spécifique"""
    stats = crud.get_production_stats_by_centre(
        db, 
        centre_usinage_id=centre_usinage_id,
        date_debut=date_debut,
        date_fin=date_fin
    )
    if not stats:
        raise HTTPException(status_code=404, detail="Aucune donnée trouvée pour ce centre d'usinage")
    return stats

# Route de santé de l'API
@app.get("/health")
def health_check():
    """Vérifier l'état de santé de l'API"""
    return {"status": "healthy", "message": "API Production Industrielle opérationnelle"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 