import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import aiofiles
from fastapi import UploadFile

import fitz  # PyMuPDF
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from monitoring_utils import monitor_faiss_search, FAISSMonitor


logger = logging.getLogger(__name__)

PREPROMPTS_DIR = Path("RAG/preprompts")
CATALOGUES_DIR = Path("RAG/Catalogues")
FAISS_INDEX_DIR = Path("faiss_index_pdf")


@dataclass
class Historique:
    nb_commandes: int = 0
    derniere_commande: str = ""
    interventions_precedentes: List[str] = field(default_factory=list)


@dataclass
class ClientInformations:
    id: int
    nom: str
    prenom: str
    adresse: str = ""
    telephone: str = ""
    email: str = ""
    date_creation: str = ""
    historique: Historique = field(default_factory=Historique)


@dataclass
class Commande:
    id_commande: str
    date: str
    produits: str
    statut: str
    montant_ht: float
    montant_ttc: float
    adresse_livraison: str
    notes: str = ""
    date_livraison: str = ""
    garantie_jusqu_au: str = ""

# Fonction pour sauvegarder l'image téléchargée
async def save_uploaded_file(uploaded_file: UploadFile) -> str:
    """
    Sauvegarder un fichier uploadé et retourner le chemin
    """
    # Validation du type de fichier
    if not uploaded_file.content_type or not uploaded_file.content_type.startswith('image/'):
        raise ValueError(f"Type de fichier non autorisé: {uploaded_file.content_type}")
    
    # Validation de la taille du fichier (max 10MB)
    content = await uploaded_file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise ValueError("Fichier trop volumineux (max 10MB)")
    
    try:
        # Créer le dossier uploads s'il n'existe pas
        upload_dir = Path("uploads/uploaded_images")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.filename}"
        file_path = upload_dir / filename
        
        # Sauvegarder le fichier
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Retourner l'URL relative pour l'accès via navigateur
        return f"/uploads/uploaded_images/{filename}"
        
    except Exception as e:
        logger.error("Erreur lors de la sauvegarde du fichier: %s", e)
        raise Exception(f"Impossible de sauvegarder le fichier: {e}")

# Fonction pour lire un fichier JSON
def load_json(file_path: Path) -> Dict:
    """Charger un fichier JSON"""
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def load_all_jsons(user=None, db=None) -> Tuple[Dict, Dict, Dict, Dict, Dict]:
    """
    Charger tous les fichiers JSON nécessaires pour le contexte
    """
    try:
        # Chemins vers les fichiers JSON
        base_path = PREPROMPTS_DIR
        
        # S'assurer que le répertoire existe
        base_path.mkdir(parents=True, exist_ok=True)
        
        preprompt_path = base_path / "preprompt_SAV.json"
        renseignements_path = base_path / "protocole_renseignements.json"
        retours_path = base_path / "protocole_retour.json"
        
        # Charger les fichiers s'ils existent, sinon retourner des objets par défaut
        preprompt = load_json(preprompt_path) if preprompt_path.exists() else {
            "content": "Vous êtes un assistant SAV professionnel."
        }
        
        # Si un utilisateur est fourni, récupérer les informations depuis la BDD
        if user and db:
            try:
                from models import Commande
                
                # Récupérer les commandes de l'utilisateur depuis la BDD
                user_commandes = db.query(Commande).filter(Commande.user_id == user.id).all()
                
                # Convertir les commandes en format JSON
                commandes_list = []
                for cmd in user_commandes:
                    commande_dict = {
                        "id_commande": cmd.numero_commande,
                        "date": cmd.date_commande.strftime("%Y-%m-%d"),
                        "produits": cmd.produits,
                        "statut": cmd.statut,
                        "montant_ht": cmd.montant_ht,
                        "montant_ttc": cmd.montant_ttc,
                        # "adresse_livraison": cmd.adresse_livraison,
                        "notes": cmd.notes
                    }
                    
                    if cmd.date_livraison:
                        commande_dict["date_livraison"] = cmd.date_livraison.strftime("%Y-%m-%d")
                        # Calculer la garantie (5 ans après livraison)
                        garantie_date = cmd.date_livraison.replace(year=cmd.date_livraison.year + 5)
                        commande_dict["garantie_jusqu_au"] = garantie_date.strftime("%Y-%m-%d")
                    
                    commandes_list.append(commande_dict)
                
                # Créer l'objet client avec les informations de l'utilisateur
                client_info = {
                    "client_informations": {
                        "id": user.id,
                        # "nom": user.nom or user.username.split('_')[-1] if '_' in user.username else user.username,
                        "prenom": user.prenom or user.username.split('_')[0] if '_' in user.username else user.username,
                        # "adresse": user.adresse or "",
                        # "telephone": user.telephone or "",
                        # "email": user.email,
                        "date_creation": user.created_at.strftime("%Y-%m-%d") if hasattr(user, 'created_at') else datetime.now().strftime("%Y-%m-%d"),
                        "historique": {
                            "nb_commandes": len(user_commandes),
                            "derniere_commande": user_commandes[-1].date_commande.strftime("%Y-%m-%d") if user_commandes else "",
                            "interventions_precedentes": []
                        }
                    }
                }
                
                # Créer l'objet commandes
                commandes = {"commandes": commandes_list}

                logger.info("Chargement des infos client et commandes pour %s depuis la BDD", user.username)
                logger.info("%d commandes trouvées", len(user_commandes))
                
            except Exception as e:
                logger.error("Erreur lors de la récupération des données client depuis la BDD: %s", e)
                  
        renseignements = load_json(renseignements_path) if renseignements_path.exists() else {}
        retours = load_json(retours_path) if retours_path.exists() else {}
        
        return preprompt, client_info, renseignements, retours, commandes
        
    except Exception as e:
        logger.error("Erreur lors du chargement des données: %s", e)
        # Retourner des valeurs par défaut en cas d'erreur
        return (
            {"content": "Assistant SAV"},
            {"client_informations": {"nom": "Client"}},
            {},
            {},
            {"commandes": []}
        )

# Initialiser ou charger l'index FAISS
@monitor_faiss_search(operation="initialize")
def initialize_faiss(openai_api_key: str, *, chunk_size: int = 1500, chunk_overlap: int = 200):
    """
    Initialiser FAISS avec des documents PDF pour le SAV
    """
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        pdf_directory = CATALOGUES_DIR
        faiss_index_path = FAISS_INDEX_DIR
        
        # Créer les répertoires s'ils n'existent pas
        pdf_directory.mkdir(parents=True, exist_ok=True)
        
        # Vérifier s'il y a des PDFs et forcer la recréation si nécessaire
        pdf_files = list(pdf_directory.glob("*.pdf"))
        should_recreate = not faiss_index_path.exists()
        
        if should_recreate:
            all_documents = []
            
            # Charger les documents PDF
            if pdf_files:
                logger.info("Chargement de %d fichiers PDF...", len(pdf_files))
                for pdf_file in pdf_files:
                    try:
                        logger.debug("Traitement de %s...", pdf_file.name)
                        with fitz.open(str(pdf_file)) as pdf_doc:
                            text = f"=== DOCUMENT: {pdf_file.name} ===\n"
                            for page_num, page in enumerate(pdf_doc):
                                page_text = page.get_text()
                                if page_text.strip():  # Ne pas ajouter de pages vides
                                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                            all_documents.append(text)
                            logger.debug("%s traité (%d caractères)", pdf_file.name, len(text))
                    except Exception as e:
                        logger.warning("Erreur lors de la lecture du PDF %s: %s", pdf_file.name, e)
            else:
                logger.info("Aucun fichier PDF trouvé dans le dossier Catalogues")
            
            # S'il y a des documents à indexer
            if all_documents:
                logger.info("Indexation de %d documents...", len(all_documents))
                # Fractionner les documents en parties gérables
                text_splitter = CharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separator="\n",
                    length_function=len
                )
                
                # Traiter chaque document séparément pour garder le contexte
                all_chunks = []
                for doc in all_documents:
                    chunks = text_splitter.split_text(doc)
                    all_chunks.extend(chunks)
                
                logger.info("Création de l'index FAISS avec %d chunks...", len(all_chunks))
                # Créer un vectorstore depuis les documents
                vectorstore = FAISS.from_texts(all_chunks, embeddings)
                faiss_index_path.mkdir(parents=True, exist_ok=True)
                vectorstore.save_local(str(faiss_index_path))
                logger.info("Index FAISS créé et sauvegardé dans %s", faiss_index_path)
            
        else:
            logger.info("Chargement de l'index FAISS existant depuis %s", faiss_index_path)
            vectorstore = FAISS.load_local(str(faiss_index_path), embeddings, allow_dangerous_deserialization=True)
        
        return vectorstore
        
    except Exception as e:
        logger.error("Erreur lors de l'initialisation de FAISS: %s", e)
        # Retourner un vectorstore minimal en cas d'erreur
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        default_documents = ["Assistant SAV disponible pour vous aider."]
        return FAISS.from_texts(default_documents, embeddings)

# Obtenir l'historique de conversation au format texte
def get_conversation_history(conversation_history: List[Dict]) -> str:
    """Convertir l'historique de conversation en texte."""
    prefixes = {"user": "User", "assistant": "Assistant", "system": "System"}
    return "\n".join(
        f"{prefixes.get(m.get('role'), '')}: {m.get('content', '')}"
        for m in conversation_history if m.get('content')
    )
