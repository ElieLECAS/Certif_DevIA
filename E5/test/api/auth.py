from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import os
from fastapi import Request
from fastapi.responses import RedirectResponse

# Configuration JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 heures par défaut

# Configuration du hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration du bearer token
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe en clair correspond au hash"""
    # Compatible avec le hachage bcrypt de PostgreSQL (pgcrypto)
    # et avec le hachage bcrypt de Python (passlib)
    try:
        # Essayer d'abord avec passlib (pour les nouveaux utilisateurs)
        if pwd_context.verify(plain_password, hashed_password):
            return True
    except:
        pass
    
    # Si passlib échoue, essayer avec PostgreSQL pgcrypto
    # Le format PostgreSQL est: $2a$10$... ou $2b$10$...
    if hashed_password.startswith('$2a$') or hashed_password.startswith('$2b$'):
        try:
            # Utiliser passlib avec le hash PostgreSQL
            return pwd_context.verify(plain_password, hashed_password)
        except:
            pass
    
    return False

def get_password_hash(password: str) -> str:
    """Génère un hash du mot de passe"""
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.Utilisateur]:
    """Authentifie un utilisateur avec username et password"""
    user = db.query(models.Utilisateur).filter(models.Utilisateur.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.statut != 'actif':
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[schemas.TokenData]:
    """Vérifie et décode un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        if username is None:
            return None
        
        token_data = schemas.TokenData(
            username=username,
            user_id=user_id,
            role=role
        )
        return token_data
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.Utilisateur:
    """Récupère l'utilisateur actuel à partir du token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = db.query(models.Utilisateur).filter(
        models.Utilisateur.username == token_data.username
    ).first()
    
    if user is None:
        raise credentials_exception
    
    if user.statut != 'actif':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte utilisateur inactif"
        )
    
    return user

async def get_current_active_user(
    current_user: models.Utilisateur = Depends(get_current_user)
) -> models.Utilisateur:
    """Vérifie que l'utilisateur actuel est actif"""
    if current_user.statut != "actif":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
    return current_user

def require_role(required_role: str):
    """Décorateur pour vérifier le rôle de l'utilisateur"""
    def role_checker(current_user: models.Utilisateur = Depends(get_current_active_user)):
        if current_user.role != required_role and current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissions insuffisantes"
            )
        return current_user
    return role_checker

def require_admin():
    """Décorateur pour vérifier que l'utilisateur est admin"""
    return require_role('admin')

def update_last_login(db: Session, user: models.Utilisateur):
    """Met à jour la date de dernière connexion"""
    user.derniere_connexion = datetime.utcnow()
    db.commit()

async def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[models.Utilisateur]:
    """Récupère l'utilisateur actuel à partir du token dans les cookies pour les routes web"""
    # Essayer de récupérer le token depuis le cookie
    token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    # Supprimer le préfixe "Bearer " s'il existe
    if token.startswith("Bearer "):
        token = token[7:]
    
    token_data = verify_token(token)
    if token_data is None:
        return None
    
    user = db.query(models.Utilisateur).filter(
        models.Utilisateur.username == token_data.username
    ).first()
    
    if user is None or user.statut != 'actif':
        return None
    
    return user

async def require_authentication_web(
    request: Request,
    db: Session = Depends(get_db)
) -> models.Utilisateur:
    """Vérifie l'authentification sur les routes web"""
    user = await get_current_user_from_cookie(request, db)
    if user is None:
        # Rediriger vers la page de connexion
        from fastapi.responses import RedirectResponse
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Redirection vers login",
            headers={"Location": "/login"}
        )
    return user

async def require_admin_web(
    request: Request,
    db: Session = Depends(get_db)
) -> models.Utilisateur:
    """Middleware pour les routes web nécessitant des droits administrateur"""
    current_user = await require_authentication_web(request, db)
    
    if current_user.role != 'admin':
        from fastapi.responses import RedirectResponse
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Redirection vers index",
            headers={"Location": "/"}
        )
    
    return current_user

async def require_manager_or_admin_web(
    request: Request,
    db: Session = Depends(get_db)
) -> models.Utilisateur:
    """Middleware pour les routes web nécessitant des droits manager ou administrateur"""
    current_user = await require_authentication_web(request, db)
    
    if current_user.role not in ['admin', 'manager']:
        from fastapi.responses import RedirectResponse
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Redirection vers index",
            headers={"Location": "/"}
        )
    
    return current_user

def check_permission(user: models.Utilisateur, required_role: str) -> bool:
    """Vérifier si un utilisateur a les permissions requises"""
    role_hierarchy = {
        'utilisateur': 1,
        'manager': 2,
        'admin': 3
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def get_user_permissions(user: models.Utilisateur) -> dict:
    """Retourner les permissions d'un utilisateur selon son rôle"""
    permissions = {
        'can_view_stock': False,
        'can_view_movements': False,
        'can_request_material': True,
        'can_scan_qr': False,
        'can_manage_stock': False,
        'can_manage_requests': False,
        'can_manage_products': False,
        'can_manage_suppliers': False,
        'can_manage_locations': False,
        'can_manage_tables': False,
        'can_manage_users': False,
        'can_view_admin_section': False
    }
    
    if user.role in ['manager', 'admin']:
        permissions.update({
            'can_view_stock': True,
            'can_view_movements': True,
            'can_scan_qr': True,
            'can_manage_stock': True,
            'can_manage_requests': True
        })
    
    if user.role == 'admin':
        permissions.update({
            'can_manage_products': True,
            'can_manage_suppliers': True,
            'can_manage_locations': True,
            'can_manage_tables': True,
            'can_manage_users': True,
            'can_view_admin_section': True
        })
    
    return permissions 