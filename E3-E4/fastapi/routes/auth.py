from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from models import User, ClientUser
from auth import authenticate_user, create_access_token, get_client_user, get_password_hash
from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

@router.get("/", response_model=None)
async def root():
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@router.get("/login", response_class=HTMLResponse, response_model=None)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_model=None)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Identifiants invalides."}
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    client_user = get_client_user(db, user)
    if client_user and client_user.is_client_only:
        response = RedirectResponse(url="/client_home", status_code=status.HTTP_302_FOUND)
    else:
        response = RedirectResponse(url="/conversations", status_code=status.HTTP_302_FOUND)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,
        expires=1800
    )
    return response

@router.get("/logout", response_model=None)
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

@router.get("/register", response_class=HTMLResponse, response_model=None)
async def register_page(request: Request):
    return templates.TemplateResponse("client_register.html", {"request": request})

@router.post("/register", response_model=None)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "client_register.html",
            {"request": request, "error": "Nom d'utilisateur ou email déjà utilisé."}
        )

    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    client_user = ClientUser(
        user_id=user.id,
        is_client_only=True
    )
    db.add(client_user)
    db.commit()

    return RedirectResponse(url="/login?message=Compte créé avec succès", status_code=status.HTTP_302_FOUND)

