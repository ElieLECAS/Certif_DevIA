from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import logging

from models import User, Conversation
from auth import get_current_active_user, get_client_user, is_staff_or_admin
from langchain_utils import load_all_jsons
from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

@router.get("/conversations", response_class=HTMLResponse, response_model=None)
async def conversations_list(
    request: Request,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Vérifier les permissions
    if not is_staff_or_admin(current_user):
        client_user = get_client_user(db, current_user)
        if client_user and client_user.is_client_only:
            return RedirectResponse(url="/client_home", status_code=status.HTTP_302_FOUND)
    
    # Récupérer les conversations
    query = db.query(Conversation)
    if status_filter:
        logger.info(f"Filtrage par statut: {status_filter}")
        query = query.filter(Conversation.status == status_filter)
    else:
        logger.info("Aucun filtre de statut appliqué")
    
    conversations = query.order_by(Conversation.updated_at.desc()).all()
    logger.info(f"Nombre de conversations trouvées: {len(conversations)}")
    
    # Améliorer les informations client pour chaque conversation
    for conversation in conversations:
        if conversation.user_id:
            # Récupérer les informations de l'utilisateur
            user = db.query(User).filter(User.id == conversation.user_id).first()
            if user:
                # Récupérer les informations client depuis la BDD
                try:
                    preprompt, client_json, renseignements, retours, commandes = load_all_jsons(user=user, db=db)
                    if client_json and isinstance(client_json, dict) and 'client_informations' in client_json:
                        client_info = client_json['client_informations']
                        nom = client_info.get('nom', '')
                        prenom = client_info.get('prenom', '')
                        if nom and prenom:
                            conversation.client_name = f"{prenom} {nom}"
                        elif nom:
                            conversation.client_name = nom
                        elif prenom:
                            conversation.client_name = prenom
                        else:
                            conversation.client_name = user.username
                    else:
                        conversation.client_name = user.username
                except Exception as e:
                    logger.error(
                        "Erreur lors du chargement des informations client : %s",
                        e,
                    )
                    conversation.client_name = user.username
            else:
                conversation.client_name = "Utilisateur inconnu"
        else:
            conversation.client_name = conversation.client_name or "Anonyme"
    
    return templates.TemplateResponse(
        "conversations_list.html",
        {
            "request": request,
            "conversations": conversations,
            "status_filter": status_filter,
            "count": len(conversations),
            "user": current_user
        }
    )

@router.put("/api/conversation/{conversation_id}/status", response_model=None)
async def update_conversation_status(
    conversation_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Vérifier les permissions (seuls les admins peuvent modifier le statut)
        if not is_staff_or_admin(current_user):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Récupérer les données JSON
        data = await request.json()
        new_status = data.get("status")
        
        # Valider le statut
        valid_statuses = ["nouveau", "en_cours", "termine"]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Statut invalide")
        
        # Récupérer la conversation
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        # Mettre à jour le statut
        conversation.set_status(new_status)
        db.commit()
        
        return {"status": "success", "message": "Statut mis à jour avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
# Route de test pour diagnostiquer les problèmes de DB
@router.get("/test-db", response_model=None)
async def test_database():
    try:
        from database import engine
        from models import Base
        
        # Tester la connexion
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()
            
        # Tester la création des tables
        Base.metadata.create_all(bind=engine)
        
        return {
            "status": "success",
            "message": "Connexion PostgreSQL réussie",
            "version": version[0] if version else "Unknown"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur de connexion: {str(e)}",
            "type": type(e).__name__
        } 
# Route dashboard admin
@router.get("/dashboard", response_class=HTMLResponse, response_model=None)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Vérifier les permissions (seuls les admins peuvent accéder au dashboard)
    if not is_staff_or_admin(current_user):
        return RedirectResponse(url="/client_home", status_code=status.HTTP_302_FOUND)
    
    # Statistiques générales
    total_conversations = db.query(Conversation).count()
    
    # Conversations par statut
    nouveau_count = db.query(Conversation).filter(Conversation.status == "nouveau").count()
    en_cours_count = db.query(Conversation).filter(Conversation.status == "en_cours").count()
    termine_count = db.query(Conversation).filter(Conversation.status == "termine").count()
    
    # Conversations aujourd'hui
    from datetime import datetime, timedelta
    today = datetime.now().date()
    today_conversations = db.query(Conversation).filter(
        Conversation.created_at >= today
    ).count()
    
    # Conversations des 30 derniers jours
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_conversations = db.query(Conversation).filter(
        Conversation.created_at >= thirty_days_ago
    ).count()
    
    # Données pour le graphique des 30 derniers jours
    daily_stats = []
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = db.query(Conversation).filter(
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        ).count()
        
        daily_stats.append({
            "date": date.strftime("%d/%m"),
            "count": count
        })
    
    # Inverser pour avoir les dates dans l'ordre chronologique
    daily_stats.reverse()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "total_conversations": total_conversations,
            "nouveau_count": nouveau_count,
            "en_cours_count": en_cours_count,
            "termine_count": termine_count,
            "today_conversations": today_conversations,
            "recent_conversations": recent_conversations,
            "daily_stats": daily_stats
        }
    ) 
@router.get("/api/dashboard/stats")
async def get_dashboard_stats(
    period: str = "month",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Vérifier les permissions
    if not is_staff_or_admin(current_user):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    from datetime import datetime, timedelta
    
    # Définir la période selon le paramètre
    if period == "week":
        days = 7
        date_format = "%d/%m"
    elif period == "month":
        days = 30
        date_format = "%d/%m"
    elif period == "quarter":
        days = 90
        date_format = "%d/%m"
    elif period == "year":
        days = 365
        date_format = "%d/%m"
    else:
        days = 30
        date_format = "%d/%m"
    
    # Générer les statistiques pour la période
    stats = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = db.query(Conversation).filter(
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        ).count()
        
        stats.append({
            "date": date.strftime(date_format),
            "count": count
        })
    
    # Inverser pour avoir les dates dans l'ordre chronologique
    stats.reverse()
    
    return {"stats": stats}
