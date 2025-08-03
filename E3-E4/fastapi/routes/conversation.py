from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import os
import logging

from models import User, Conversation
from auth import get_current_active_user, get_client_user, is_staff_or_admin
from langchain_utils import initialize_faiss, load_all_jsons, get_conversation_history, save_uploaded_file
from utils import get_openai_api_key, MISSING_OPENAI_KEY_MSG
from schemas import ChatMessage, ChatResponse, ConversationClose, ClientNameUpdate
from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

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
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    client_user = get_client_user(db, current_user)
    if not client_user:
        return RedirectResponse(url="/conversations", status_code=status.HTTP_302_FOUND)
    
    # Récupérer les conversations du client
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    
    # Appliquer le filtre de statut si spécifié
    if status_filter:
        logger.info(f"Filtrage client par statut: {status_filter}")
        query = query.filter(Conversation.status == status_filter)
    else:
        logger.info("Aucun filtre de statut appliqué pour le client")
    
    conversations = query.order_by(Conversation.updated_at.desc()).all()
    logger.info(f"Nombre de conversations client trouvées: {len(conversations)}")
    
    return templates.TemplateResponse(
        "client_home.html",
        {
            "request": request,
            "user": current_user,
            "conversations": conversations,
            "status_filter": status_filter
        }
    )

@router.get("/chat", response_class=HTMLResponse, response_model=None)
async def chat_page(
    request: Request,
    conversation_id: Optional[str] = None,  # Récupérer conversation_id depuis l'URL
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Récupérer la conversation depuis l'URL ou la conversation active
    history = "[]"
    
    # Priorité 1: conversation_id depuis l'URL
    if conversation_id and conversation_id != "temp":
        try:
            conv_id = int(conversation_id)
            conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conversation:
                history = json.dumps(conversation.history)
        except (ValueError, TypeError):
            conversation_id = "temp"
    
    # Priorité 2: conversation active du client si pas d'URL
    if not conversation_id or conversation_id == "temp":
        conversation_id = "temp"
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
        
        # Validation des entrées avec ChatMessage
        chat_message = ChatMessage(message=user_input, conversation_id=conversation_id)
        
        # Récupérer les images si présentes
        images = []
        for key, value in form_data.items():
            if key.startswith("images") and hasattr(value, 'file'):
                images.append(value)
        
        if not chat_message.message:
            raise HTTPException(status_code=400, detail="Le message ne peut pas être vide")
        
        # Configuration OpenAI
        try:
            openai_api_key = get_openai_api_key()
        except EnvironmentError:
            raise HTTPException(status_code=401, detail=MISSING_OPENAI_KEY_MSG)
        
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
        
        # Ajouter le message utilisateur (comme Django)
        conversation.add_message("user", user_input)
        
        # Récupérer l'historique complet
        conversation_history = conversation.history
        
        # Ajouter les prompts système s'ils n'existent pas déjà (EXACTEMENT comme Django)
        if len(conversation_history) <= 1:  # Seulement le message utilisateur qu'on vient d'ajouter
            system_prompts = [
                {"role": "system", "content": preprompt.get("content", "Vous êtes un assistant virtuel serviable et professionnel.")},
                {"role": "system", "content": json.dumps(client_json)},
                {"role": "system", "content": json.dumps(retours)},
                {"role": "system", "content": json.dumps(commandes)}
            ]
            # Insérer au début de l'historique (comme Django)
            conversation.history = system_prompts + conversation_history
            db.commit()  # Sauvegarder
            conversation_history = conversation.history
        
        # Recherche FAISS améliorée
        try:
            faiss_results = vectorstore.similarity_search(user_input, k=5)  # Récupérer 5 résultats
            faiss_context = "\n".join([doc.page_content for doc in faiss_results])
            logger.info("R\xc3\xa9sultats FAISS trouv\xc3\xa9s: %d", len(faiss_results))
        except Exception as e:
            logger.error("Erreur recherche FAISS: %s", e)
            faiss_context = "Informations g\xc3\xa9n\xc3\xa9rales PROFERM: sp\xc3\xa9cialiste des portes d'entr\xc3\xa9e, vitrages et stores."
        
        # Convertir l'historique de conversation en texte (comme Django)
        history_text = get_conversation_history(conversation_history)
        
        # Préparer le contexte complet (EXACTEMENT comme Django)
        complete_context = history_text + "\nContext from FAISS:\n" + faiss_context
        
        # Obtenir la réponse du modèle (EXACTEMENT comme Django)
        response = llm.invoke(complete_context + "\nUser: " + user_input)
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

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
        
        # Validation avec ConversationClose
        if conversation_id and conversation_id != "temp":
            try:
                conv_close = ConversationClose(conversation_id=int(conversation_id))
                conversation_id = conv_close.conversation_id
            except (ValueError, TypeError):
                return {"status": "success", "message": "ID de conversation invalide"}
        
        if not conversation_id or conversation_id == "temp":
            return {"status": "success", "message": "Aucune conversation active à clôturer"}
        
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
        try:
            openai_api_key = get_openai_api_key()
        except EnvironmentError:
            openai_api_key = None
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

@router.post("/api/upload_images", response_model=None)
async def upload_images(
    images: List[UploadFile] = File(...),
    conversation_id: str = Form("temp"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Validation des fichiers uploadés
        if not images:
            raise HTTPException(status_code=400, detail="Aucune image téléchargée")
        
        # Validation des types de fichiers
        for image in images:
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail=f"Type de fichier non autorisé: {image.content_type}")
        
        # Configuration OpenAI
        try:
            openai_api_key = get_openai_api_key()
        except EnvironmentError:
            raise HTTPException(status_code=401, detail=MISSING_OPENAI_KEY_MSG)
        
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
        
    except HTTPException:
        raise
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
        
        # Validation avec ClientNameUpdate
        try:
            client_update = ClientNameUpdate(conversation_id=int(conversation_id), client_name=client_name)
            conversation_id = client_update.conversation_id
            client_name = client_update.client_name
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

