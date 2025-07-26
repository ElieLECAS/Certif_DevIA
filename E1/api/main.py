from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta
from typing import List

from database import get_session, create_db_and_tables
from models import (
    CentreUsinage, CentreUsinageCreate, CentreUsinageRead,
    SessionProduction, SessionProductionCreate, SessionProductionRead,
    JobProfil, JobProfilCreate, JobProfilRead,
    PeriodeAttente, PeriodeAttenteCreate, PeriodeAttenteRead,
    PeriodeArret, PeriodeArretCreate, PeriodeArretRead,
    PieceProduction, PieceProductionCreate, PieceProductionRead,
    CommandeVoletRoulant, CommandeVoletRoulantCreate, CommandeVoletRoulantRead
)
from auth.models import User, UserCreate, UserRead, Token
from auth.utils import (
    get_current_active_user, create_access_token,
    verify_password, get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(title="API Production", version="2.0.0")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Auth routes
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password)
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# CRUD routes for CentreUsinage
@app.post("/centres/", response_model=CentreUsinageRead)
def create_centre(
    centre: CentreUsinageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_centre = CentreUsinage.from_orm(centre)
    session.add(db_centre)
    session.commit()
    session.refresh(db_centre)
    return db_centre

@app.get("/centres/", response_model=List[CentreUsinageRead])
def read_centres(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    centres = session.exec(select(CentreUsinage).offset(skip).limit(limit)).all()
    return centres

@app.get("/centres/{centre_id}", response_model=CentreUsinageRead)
def read_centre(
    centre_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    centre = session.get(CentreUsinage, centre_id)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    return centre

@app.put("/centres/{centre_id}", response_model=CentreUsinageRead)
def update_centre(
    centre_id: int,
    centre: CentreUsinageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_centre = session.get(CentreUsinage, centre_id)
    if not db_centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    
    centre_data = centre.dict(exclude_unset=True)
    for key, value in centre_data.items():
        setattr(db_centre, key, value)
    
    session.add(db_centre)
    session.commit()
    session.refresh(db_centre)
    return db_centre

@app.delete("/centres/{centre_id}")
def delete_centre(
    centre_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    centre = session.get(CentreUsinage, centre_id)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    
    session.delete(centre)
    session.commit()
    return {"ok": True}

# Similar CRUD routes for SessionProduction
@app.post("/sessions/", response_model=SessionProductionRead)
def create_session(
    session_prod: SessionProductionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_session = SessionProduction.from_orm(session_prod)
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    return db_session

@app.get("/sessions/", response_model=List[SessionProductionRead])
def read_sessions(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    sessions = session.exec(select(SessionProduction).offset(skip).limit(limit)).all()
    return sessions

# CRUD routes for CommandeVoletRoulant
@app.post("/commandes-volets/", response_model=CommandeVoletRoulantRead)
def create_commande_volet(
    commande: CommandeVoletRoulantCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_commande = CommandeVoletRoulant.from_orm(commande)
    session.add(db_commande)
    session.commit()
    session.refresh(db_commande)
    return db_commande

@app.get("/commandes-volets/", response_model=List[CommandeVoletRoulantRead])
def read_commandes_volets(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    commandes = session.exec(select(CommandeVoletRoulant).offset(skip).limit(limit)).all()
    return commandes

@app.get("/commandes-volets/{commande_id}", response_model=CommandeVoletRoulantRead)
def read_commande_volet(
    commande_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    commande = session.get(CommandeVoletRoulant, commande_id)
    if not commande:
        raise HTTPException(status_code=404, detail="Commande not found")
    return commande

@app.put("/commandes-volets/{commande_id}", response_model=CommandeVoletRoulantRead)
def update_commande_volet(
    commande_id: int,
    commande: CommandeVoletRoulantCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_commande = session.get(CommandeVoletRoulant, commande_id)
    if not db_commande:
        raise HTTPException(status_code=404, detail="Commande not found")
    
    commande_data = commande.dict(exclude_unset=True)
    for key, value in commande_data.items():
        setattr(db_commande, key, value)
    
    session.add(db_commande)
    session.commit()
    session.refresh(db_commande)
    return db_commande

@app.delete("/commandes-volets/{commande_id}")
def delete_commande_volet(
    commande_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    commande = session.get(CommandeVoletRoulant, commande_id)
    if not commande:
        raise HTTPException(status_code=404, detail="Commande not found")
    
    session.delete(commande)
    session.commit()
    return {"ok": True}

# Routes de recherche spécifiques pour les commandes de volets roulants
@app.get("/commandes-volets/by-numero/{numero_commande}", response_model=List[CommandeVoletRoulantRead])
def read_commandes_by_numero(
    numero_commande: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    commandes = session.exec(
        select(CommandeVoletRoulant).where(CommandeVoletRoulant.numero_commande == numero_commande)
    ).all()
    return commandes

@app.get("/commandes-volets/by-status/{status}", response_model=List[CommandeVoletRoulantRead])
def read_commandes_by_status(
    status: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    commandes = session.exec(
        select(CommandeVoletRoulant).where(CommandeVoletRoulant.status == status)
    ).all()
    return commandes

# Add similar CRUD routes for JobProfil, PeriodeAttente, PeriodeArret, and PieceProduction
# Following the same pattern as above

# CRUD routes for JobProfil
@app.post("/job-profils/", response_model=JobProfilRead)
def create_job_profil(
    job_profil: JobProfilCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_job_profil = JobProfil.from_orm(job_profil)
    session.add(db_job_profil)
    session.commit()
    session.refresh(db_job_profil)
    return db_job_profil

@app.get("/job-profils/", response_model=List[JobProfilRead])
def read_job_profils(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    job_profils = session.exec(select(JobProfil).offset(skip).limit(limit)).all()
    return job_profils

@app.get("/job-profils/{job_profil_id}", response_model=JobProfilRead)
def read_job_profil(
    job_profil_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    job_profil = session.get(JobProfil, job_profil_id)
    if not job_profil:
        raise HTTPException(status_code=404, detail="JobProfil not found")
    return job_profil

@app.put("/job-profils/{job_profil_id}", response_model=JobProfilRead)
def update_job_profil(
    job_profil_id: int,
    job_profil: JobProfilCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_job_profil = session.get(JobProfil, job_profil_id)
    if not db_job_profil:
        raise HTTPException(status_code=404, detail="JobProfil not found")
    
    job_profil_data = job_profil.dict(exclude_unset=True)
    for key, value in job_profil_data.items():
        setattr(db_job_profil, key, value)
    
    session.add(db_job_profil)
    session.commit()
    session.refresh(db_job_profil)
    return db_job_profil

@app.delete("/job-profils/{job_profil_id}")
def delete_job_profil(
    job_profil_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    job_profil = session.get(JobProfil, job_profil_id)
    if not job_profil:
        raise HTTPException(status_code=404, detail="JobProfil not found")
    
    session.delete(job_profil)
    session.commit()
    return {"ok": True}

# CRUD routes for PeriodeAttente
@app.post("/periodes-attente/", response_model=PeriodeAttenteRead)
def create_periode_attente(
    periode: PeriodeAttenteCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_periode = PeriodeAttente.from_orm(periode)
    session.add(db_periode)
    session.commit()
    session.refresh(db_periode)
    return db_periode

@app.get("/periodes-attente/", response_model=List[PeriodeAttenteRead])
def read_periodes_attente(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    periodes = session.exec(select(PeriodeAttente).offset(skip).limit(limit)).all()
    return periodes

@app.get("/periodes-attente/{periode_id}", response_model=PeriodeAttenteRead)
def read_periode_attente(
    periode_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    periode = session.get(PeriodeAttente, periode_id)
    if not periode:
        raise HTTPException(status_code=404, detail="PeriodeAttente not found")
    return periode

@app.put("/periodes-attente/{periode_id}", response_model=PeriodeAttenteRead)
def update_periode_attente(
    periode_id: int,
    periode: PeriodeAttenteCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_periode = session.get(PeriodeAttente, periode_id)
    if not db_periode:
        raise HTTPException(status_code=404, detail="PeriodeAttente not found")
    
    periode_data = periode.dict(exclude_unset=True)
    for key, value in periode_data.items():
        setattr(db_periode, key, value)
    
    session.add(db_periode)
    session.commit()
    session.refresh(db_periode)
    return db_periode

@app.delete("/periodes-attente/{periode_id}")
def delete_periode_attente(
    periode_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    periode = session.get(PeriodeAttente, periode_id)
    if not periode:
        raise HTTPException(status_code=404, detail="PeriodeAttente not found")
    
    session.delete(periode)
    session.commit()
    return {"ok": True}

# CRUD routes for PeriodeArret
@app.post("/periodes-arret/", response_model=PeriodeArretRead)
def create_periode_arret(
    periode: PeriodeArretCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_periode = PeriodeArret.from_orm(periode)
    session.add(db_periode)
    session.commit()
    session.refresh(db_periode)
    return db_periode

@app.get("/periodes-arret/", response_model=List[PeriodeArretRead])
def read_periodes_arret(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    periodes = session.exec(select(PeriodeArret).offset(skip).limit(limit)).all()
    return periodes

@app.get("/periodes-arret/{periode_id}", response_model=PeriodeArretRead)
def read_periode_arret(
    periode_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    periode = session.get(PeriodeArret, periode_id)
    if not periode:
        raise HTTPException(status_code=404, detail="PeriodeArret not found")
    return periode

@app.put("/periodes-arret/{periode_id}", response_model=PeriodeArretRead)
def update_periode_arret(
    periode_id: int,
    periode: PeriodeArretCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_periode = session.get(PeriodeArret, periode_id)
    if not db_periode:
        raise HTTPException(status_code=404, detail="PeriodeArret not found")
    
    periode_data = periode.dict(exclude_unset=True)
    for key, value in periode_data.items():
        setattr(db_periode, key, value)
    
    session.add(db_periode)
    session.commit()
    session.refresh(db_periode)
    return db_periode

@app.delete("/periodes-arret/{periode_id}")
def delete_periode_arret(
    periode_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    periode = session.get(PeriodeArret, periode_id)
    if not periode:
        raise HTTPException(status_code=404, detail="PeriodeArret not found")
    
    session.delete(periode)
    session.commit()
    return {"ok": True}

# CRUD routes for PieceProduction
@app.post("/pieces-production/", response_model=PieceProductionRead)
def create_piece_production(
    piece: PieceProductionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_piece = PieceProduction.from_orm(piece)
    session.add(db_piece)
    session.commit()
    session.refresh(db_piece)
    return db_piece

@app.get("/pieces-production/", response_model=List[PieceProductionRead])
def read_pieces_production(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    pieces = session.exec(select(PieceProduction).offset(skip).limit(limit)).all()
    return pieces

@app.get("/pieces-production/{piece_id}", response_model=PieceProductionRead)
def read_piece_production(
    piece_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    piece = session.get(PieceProduction, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="PieceProduction not found")
    return piece

@app.put("/pieces-production/{piece_id}", response_model=PieceProductionRead)
def update_piece_production(
    piece_id: int,
    piece: PieceProductionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_piece = session.get(PieceProduction, piece_id)
    if not db_piece:
        raise HTTPException(status_code=404, detail="PieceProduction not found")
    
    piece_data = piece.dict(exclude_unset=True)
    for key, value in piece_data.items():
        setattr(db_piece, key, value)
    
    session.add(db_piece)
    session.commit()
    session.refresh(db_piece)
    return db_piece

@app.delete("/pieces-production/{piece_id}")
def delete_piece_production(
    piece_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    piece = session.get(PieceProduction, piece_id)
    if not piece:
        raise HTTPException(status_code=404, detail="PieceProduction not found")
    
    session.delete(piece)
    session.commit()
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 