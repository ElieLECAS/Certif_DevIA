from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import json
import os
from pathlib import Path
import logging
from models import User, ClientUser, Conversation
from auth import authenticate_user, create_access_token, get_current_active_user, get_client_user, is_client_only, is_staff_or_admin, get_password_hash
from langchain_utils import initialize_faiss, load_all_jsons, get_conversation_history, save_uploaded_file

# Import de la fonction get_db depuis database
from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

# Variable globale pour stocker l'index FAISS
_vectorstore = None

def get_vectorstore(openai_api_key: str):
    """Obtenir l'index FAISS (initialisé une seule fois)"""
    global _vectorstore
    if _vectorstore is None:
        logger.info("\ud83d\udd04 Initialisation de l'index FAISS...")
        _vectorstore = initialize_faiss(openai_api_key)
        logger.info("\u2705 Index FAISS initialisé avec succ\u00e8s")
    else:
        logger.info("\ud83d\udcda Utilisation de l'index FAISS existant")
    return _vectorstore


def get_or_create_conversation(
    db: Session,
    user: User,
    conversation_id: Optional[str],
    client_name: str,
) -> Conversation:
    """Récupérer une conversation existante ou en créer une nouvelle."""
    conversation = None
    if conversation_id and conversation_id != "temp":
        try:
            conv_id = int(conversation_id)
            conversation = (
                db.query(Conversation).filter(Conversation.id == conv_id).first()
            )
        except (ValueError, TypeError):
            conversation = None

    if not conversation:
        conversation = Conversation(
            client_name=client_name,
            status="nouveau",
            user_id=user.id,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation

# Route de connexion (GET)
@router.get("/login", response_class=HTMLResponse, response_model=None)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Route de connexion (POST)
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
    
    # Vérifier si l'utilisateur est un client
    client_user = get_client_user(db, user)
    if client_user and client_user.is_client_only:
        response = RedirectResponse(url="/client_home", status_code=status.HTTP_302_FOUND)
    else:
        response = RedirectResponse(url="/conversations", status_code=status.HTTP_302_FOUND)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,  # 30 minutes
        expires=1800
    )
    return response

# Route de déconnexion
@router.get("/logout", response_model=None)
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

# Route d'inscription client (GET)
@router.get("/register", response_class=HTMLResponse, response_model=None)
async def register_page(request: Request):
    return templates.TemplateResponse("client_register.html", {"request": request})

# Route d'inscription client (POST)
@router.post("/register", response_model=None)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        return templates.TemplateResponse(
            "client_register.html",
            {"request": request, "error": "Nom d'utilisateur ou email déjà utilisé."}
        )
    
    # Créer l'utilisateur
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
    
    # Créer le profil client
    client_user = ClientUser(
        user_id=user.id,
        is_client_only=True
    )
    db.add(client_user)
    db.commit()
    
    return RedirectResponse(url="/login?message=Compte créé avec succès", status_code=status.HTTP_302_FOUND)

# Route liste des conversations (pour les admins)
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
        query = query.filter(Conversation.status == status_filter)
    
    conversations = query.order_by(Conversation.updated_at.desc()).all()
    
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

# Route détail d'une conversation
@router.get("/conversation/{conversation_id}", response_class=HTMLResponse, response_model=None)
async def conversation_detail(
    request: Request,
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        if is_staff_or_admin(current_user):
            return RedirectResponse(url="/conversations", status_code=status.HTTP_302_FOUND)
        else:
            return RedirectResponse(url="/client_home", status_code=status.HTTP_302_FOUND)
    
    # Vérifier les permissions
    if not is_staff_or_admin(current_user):
        client_user = get_client_user(db, current_user)
        if client_user and client_user.is_client_only:
            if conversation.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Filtrer les messages (exclure les messages système)
    messages = []
    if conversation.history:
        messages = [msg for msg in conversation.history if msg.get('role') != 'system']
    
    return templates.TemplateResponse(
        "conversation_detail.html",
        {
            "request": request,
            "conversation": conversation,
            "messages": messages,
            "is_admin": is_staff_or_admin(current_user),
            "user": current_user
        }
    )

# Route page d'accueil client
@router.get("/client_home", response_class=HTMLResponse, response_model=None)
async def client_home(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    client_user = get_client_user(db, current_user)
    if not client_user:
        return RedirectResponse(url="/conversations", status_code=status.HTTP_302_FOUND)
    
    # Récupérer les conversations du client
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).limit(10).all()
    
    return templates.TemplateResponse(
        "client_home.html",
        {
            "request": request,
            "user": current_user,
            "conversations": conversations
        }
    )

# Route chat OpenAI (GET)
@router.get("/chat", response_class=HTMLResponse, response_model=None)
async def chat_page(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Récupérer la conversation active
    conversation_id = "temp"
    history = "[]"
    
    client_user = get_client_user(db, current_user)
    if client_user and client_user.active_conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == client_user.active_conversation_id
        ).first()
        if conversation:
            conversation_id = conversation.id
            history = json.dumps(conversation.history)
    
    # Récupérer les informations du client
    try:
        preprompt, client_json, renseignements, retours, commandes = load_all_jsons(
            user=current_user, db=db
        )
    except Exception as e:
        logger.error(
            "Erreur lors du chargement des informations client : %s",
            e,
        )
        client_json = {}
    
    return templates.TemplateResponse(
        "openai_chat.html",
        {
            "request": request,
            "user": current_user,
            "conversation_id": conversation_id,
            "history": history,
            "client_info": client_json
        }
    )

# API endpoint pour envoyer un message
@router.post("/api/chat")
async def send_message(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Récupérer les données du formulaire
        form_data = await request.form()
        user_input = form_data.get("message", "").strip()
        conversation_id = form_data.get("conversation_id", "temp")
        
        # Récupérer les images si présentes
        images = []
        for key, value in form_data.items():
            if key.startswith("images") and hasattr(value, 'file'):
                images.append(value)
        
        if not user_input:
            raise HTTPException(status_code=400, detail="Le message ne peut pas être vide")
        
        # Configuration OpenAI
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="Clé API OpenAI non configurée")
        
        # Récupérer les données contextuelles
        preprompt, client_json, renseignements, retours, commandes = load_all_jsons(user=current_user, db=db)
        
        # Extraire le nom du client
        client_name = current_user.username  # Utiliser le username par défaut
        if client_json and isinstance(client_json, dict):
            if 'client_informations' in client_json:
                client_info = client_json['client_informations']
                nom = client_info.get('nom', '')
                prenom = client_info.get('prenom', '')
                if nom and prenom:
                    client_name = f"{prenom} {nom}"
                elif nom:
                    client_name = nom
        
        # Récupérer ou créer une conversation
        conversation = get_or_create_conversation(
            db=db,
            user=current_user,
            conversation_id=conversation_id,
            client_name=client_name,
        )
        
        # Initialiser LLM et FAISS
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", max_tokens=500, temperature=0.4)
        vectorstore = get_vectorstore(openai_api_key)
        
        # Ajouter le message utilisateur
        conversation.add_message("user", user_input)
        
        # Ajouter les prompts système si c'est le premier message
        if len(conversation.history) <= 1:
            system_prompts = [
                {"role": "system", "content": preprompt.get("content", "Vous êtes un assistant virtuel serviable et professionnel.")},
                {"role": "system", "content": json.dumps(client_json)},
                {"role": "system", "content": json.dumps(retours)},
                {"role": "system", "content": json.dumps(commandes)}
            ]
            conversation.history = system_prompts + conversation.history
        
        # Recherche FAISS améliorée
        try:
            faiss_results = vectorstore.similarity_search(user_input, k=5)  # Récupérer 5 résultats
            faiss_context = "\n".join([doc.page_content for doc in faiss_results])
            logger.info("R\xc3\xa9sultats FAISS trouv\xc3\xa9s: %d", len(faiss_results))
        except Exception as e:
            logger.error("Erreur recherche FAISS: %s", e)
            faiss_context = "Informations g\xc3\xa9n\xc3\xa9rales PROFERM: sp\xc3\xa9cialiste des portes d'entr\xc3\xa9e, vitrages et stores."
        
        # Préparer le contexte
        history_text = get_conversation_history(conversation.history)
        complete_context = (
            f"{history_text}\n\n"
            f"Informations des catalogues PROFERM:\n{faiss_context}\n\n"
            f"Instructions: Utilisez les informations des catalogues PROFERM ci-dessus pour répondre aux questions sur nos produits. "
            f"Si vous ne trouvez pas d'informations spécifiques, redirigez poliment vers notre service client.\n\n"
            f"User: {user_input}"
        )
        
        # Obtenir la réponse
        response = llm.invoke(complete_context)
        assistant_response = response.content if hasattr(response, 'content') else "Aucune réponse trouvée."
        
        # Ajouter la réponse
        conversation.add_message("assistant", assistant_response)
        
        # Sauvegarder
        db.commit()
        
        return {
            "success": True,
            "response": assistant_response,
            "conversation_id": conversation.id,
            "history": conversation.history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# API endpoint pour fermer une conversation
@router.post("/api/close_conversation", response_model=None)
async def close_conversation(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Récupérer les données du formulaire
        form_data = await request.form()
        conversation_id = form_data.get("conversation_id")
        summary = form_data.get("summary", "Conversation clôturée par l'utilisateur")
        
        if not conversation_id or conversation_id == "temp":
            return {"status": "success", "message": "Aucune conversation active à clôturer"}
        
        # Convertir en int si c'est une chaîne
        try:
            conversation_id = int(conversation_id)
        except (ValueError, TypeError):
            return {"status": "success", "message": "ID de conversation invalide"}
        
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        # Vérifier s'il y a des messages réels
        has_real_messages = False
        if conversation.history:
            for msg in conversation.history:
                if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                    has_real_messages = True
                    break
        
        # Si pas de messages réels, supprimer la conversation
        if not has_real_messages:
            db.delete(conversation)
            db.commit()
            return {"status": "success", "message": "Conversation vide supprimée"}
        
        # Générer un résumé
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", max_tokens=500, temperature=0.3)
            
            conversation_text = get_conversation_history(conversation.history)
            summary_prompt = f"\n{conversation_text}\n\nGénère un résumé de l'entière de la conversation avec le client pour le transmettre à un technicien SAV humain, donne lui les points importants pour lui permettre de gagner du temps sur la relecture de la conversation SAV."
            summary_response = llm.invoke(summary_prompt)
            summary = summary_response.content if hasattr(summary_response, 'content') else "Résumé indisponible."
            
            conversation.summary = summary
            db.commit()
            
            return {"status": "success", "summary": summary}
        
        return {"status": "success", "message": "Conversation fermée"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# API endpoint pour upload d'images
@router.post("/api/upload_images", response_model=None)
async def upload_images(
    images: List[UploadFile] = File(...),
    conversation_id: str = Form("temp"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        if not images:
            raise HTTPException(status_code=400, detail="Aucune image téléchargée")
        
        # Configuration OpenAI
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="Clé API OpenAI non configurée")
        
        # Charger les informations client et récupérer ou créer la conversation
        preprompt, client_json, renseignements, retours, commandes = load_all_jsons(user=current_user)
        client_name = "Client"
        if client_json and isinstance(client_json, dict):
            if 'client_informations' in client_json:
                client_info = client_json['client_informations']
                nom = client_info.get('nom', '')
                prenom = client_info.get('prenom', '')
                if nom and prenom:
                    client_name = f"{prenom} {nom}"
                elif nom:
                    client_name = nom

        conversation = get_or_create_conversation(
            db=db,
            user=current_user,
            conversation_id=conversation_id,
            client_name=client_name,
        )
        
        # Sauvegarder les images
        image_paths = []
        for image in images:
            path = await save_uploaded_file(image)
            image_paths.append(path)
            conversation.add_message(
                "user",
                f"📤 Image envoyée: {os.path.basename(path)}",
                image_path=path
            )
        
        # Initialiser LLM et FAISS
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", max_tokens=500, temperature=0.4)
        vectorstore = get_vectorstore(openai_api_key)
        
        # Générer une réponse pour les images
        history_text = get_conversation_history(conversation.history)
        faiss_results = vectorstore.similarity_search("Photos envoyées pour SAV")
        faiss_context = "\n".join([doc.page_content for doc in faiss_results])
        
        complete_context = (
            f"{history_text}\n"
            "Context from FAISS:\n"
            f"{faiss_context}\n"
            "User: Des photos ont été envoyées. Veuillez les analyser et donner des premiers conseils au client."
        )
        
        response = llm.invoke(complete_context)
        assistant_response = response.content if hasattr(response, 'content') else "J'ai bien reçu vos images. Comment puis-je vous aider avec ces photos ?"
        
        conversation.add_message("assistant", assistant_response)
        db.commit()
        
        return {
            "response": assistant_response,
            "conversation_id": conversation.id,
            "history": conversation.history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# API endpoint pour reset du chat
@router.post("/api/reset_chat", response_model=None)
async def reset_chat():
    return {"status": "success", "conversation_id": "temp"}

# API endpoint pour mettre à jour le nom du client
@router.post("/api/update_client_name", response_model=None)
async def update_client_name(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Récupérer les données du formulaire
        form_data = await request.form()
        conversation_id = form_data.get("conversation_id")
        client_name = form_data.get("client_name", "")
        
        # Convertir en int si c'est une chaîne
        try:
            conversation_id = int(conversation_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="ID de conversation invalide")
        
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        conversation.client_name = client_name
        db.commit()
        
        return {"status": "success", "message": "Nom du client mis à jour avec succès"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# Route racine - redirection vers login
@router.get("/", response_model=None)
async def root():
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

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