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
    PieceProduction, PieceProductionCreate, PieceProductionRead
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

# Add similar CRUD routes for JobProfil, PeriodeAttente, PeriodeArret, and PieceProduction
# Following the same pattern as above

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 