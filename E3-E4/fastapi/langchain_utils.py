import os
import json
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import aiofiles
from fastapi import UploadFile

from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub

# Fonction pour sauvegarder l'image téléchargée
async def save_uploaded_file(uploaded_file: UploadFile) -> str:
    """
    Sauvegarder un fichier uploadé et retourner le chemin
    """
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
            content = await uploaded_file.read()
            await f.write(content)
        
        # Retourner l'URL relative pour l'accès via navigateur
        return f"/uploads/uploaded_images/{filename}"
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier: {e}")
        raise Exception(f"Impossible de sauvegarder le fichier: {e}")

# Fonction pour lire un fichier JSON
def load_json(file_path: str) -> Dict:
    """Charger un fichier JSON"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def load_all_jsons(user=None, db=None) -> Tuple[Dict, Dict, Dict, Dict, Dict]:
    """
    Charger tous les fichiers JSON nécessaires pour le contexte
    """
    try:
        # Chemins vers les fichiers JSON (adaptés de la structure Django)
        base_path = Path("RAG/preprompts")
        
        # S'assurer que le répertoire existe
        base_path.mkdir(parents=True, exist_ok=True)
        
        preprompt_path = base_path / "preprompt_SAV.json"
        renseignements_path = base_path / "protocole_renseignements.json"
        retours_path = base_path / "protocole_retour.json"
        
        # Charger les fichiers s'ils existent, sinon retourner des objets par défaut
        preprompt = load_json(str(preprompt_path)) if preprompt_path.exists() else {
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
                        "adresse_livraison": cmd.adresse_livraison,
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
                        "nom": user.nom or user.username.split('_')[-1] if '_' in user.username else user.username,
                        "prenom": user.prenom or user.username.split('_')[0] if '_' in user.username else user.username,
                        "adresse": user.adresse or "",
                        "telephone": user.telephone or "",
                        "email": user.email,
                        "date_creation": user.created_at.strftime("%Y-%m-%d") if hasattr(user, 'created_at') else datetime.now().strftime("%Y-%m-%d"),
                        "historique": {
                            "nb_commandes": len(user_commandes),
                            "derniere_commande": user_commandes[-1].date_commande.strftime("%Y-%m-%d") if user_commandes else "",
                            "interventions_precedentes": []  # À compléter si vous ajoutez une table d'interventions
                        }
                    }
                }
                
                # Créer l'objet commandes
                commandes = {"commandes": commandes_list}
                
                print(f"✅ Chargement des infos client et commandes pour {user.username} depuis la BDD")
                print(f"   📦 {len(user_commandes)} commandes trouvées")
                
            except Exception as e:
                print(f"Erreur lors de la récupération des données client depuis la BDD: {e}")
                # En cas d'erreur, créer des objets par défaut
                client_info = {
                    "client_informations": {
                        "id": user.id,
                        "nom": user.username,
                        "prenom": user.username,
                        "email": user.email,
                        "date_creation": user.created_at.strftime("%Y-%m-%d") if hasattr(user, 'created_at') else datetime.now().strftime("%Y-%m-%d"),
                        "historique": {
                            "nb_commandes": 0,
                            "derniere_commande": "",
                            "interventions_precedentes": []
                        }
                    }
                }
                commandes = {"commandes": []}
        else:
            # Si aucun utilisateur n'est fourni, créer des objets par défaut
            client_info = {
                "client_informations": {
                    "id": 0,
                    "nom": "Client",
                    "prenom": "Anonyme",
                    "email": "",
                    "date_creation": datetime.now().strftime("%Y-%m-%d"),
                    "historique": {
                        "nb_commandes": 0,
                        "derniere_commande": "",
                        "interventions_precedentes": []
                    }
                }
            }
            commandes = {"commandes": []}
        
        renseignements = load_json(str(renseignements_path)) if renseignements_path.exists() else {}
        retours = load_json(str(retours_path)) if retours_path.exists() else {}
        
        return preprompt, client_info, renseignements, retours, commandes
        
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        # Retourner des valeurs par défaut en cas d'erreur
        return (
            {"content": "Assistant SAV"},
            {"client_informations": {"nom": "Client"}},
            {},
            {},
            {"commandes": []}
        )

# Initialiser ou charger l'index FAISS
def initialize_faiss(openai_api_key: str):
    """
    Initialiser FAISS avec des documents PDF pour le SAV
    """
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        pdf_directory = Path("RAG/Catalogues")
        faiss_index_path = Path("faiss_index_pdf")
        
        # Créer les répertoires s'ils n'existent pas
        pdf_directory.mkdir(parents=True, exist_ok=True)
        
        # Vérifier s'il y a des PDFs et forcer la recréation si nécessaire
        pdf_files = list(pdf_directory.glob("*.pdf"))
        should_recreate = not faiss_index_path.exists()
        
        if should_recreate:
            all_documents = []
            
            # Charger les documents PDF
            if pdf_files:
                print(f"Chargement de {len(pdf_files)} fichiers PDF...")
                for pdf_file in pdf_files:
                    try:
                        print(f"Traitement de {pdf_file.name}...")
                        with fitz.open(str(pdf_file)) as pdf_doc:
                            text = f"=== DOCUMENT: {pdf_file.name} ===\n"
                            for page_num, page in enumerate(pdf_doc):
                                page_text = page.get_text()
                                if page_text.strip():  # Ne pas ajouter de pages vides
                                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                            all_documents.append(text)
                            print(f"✓ {pdf_file.name} traité ({len(text)} caractères)")
                    except Exception as e:
                        print(f"❌ Erreur lors de la lecture du PDF {pdf_file.name}: {str(e)}")
            else:
                print("Aucun fichier PDF trouvé dans le dossier Catalogues")
            
            # S'il y a des documents à indexer
            if all_documents:
                print(f"Indexation de {len(all_documents)} documents...")
                # Fractionner les documents en parties gérables
                text_splitter = CharacterTextSplitter(
                    chunk_size=1500, 
                    chunk_overlap=200, 
                    separator="\n",
                    length_function=len
                )
                
                # Traiter chaque document séparément pour garder le contexte
                all_chunks = []
                for doc in all_documents:
                    chunks = text_splitter.split_text(doc)
                    all_chunks.extend(chunks)
                
                print(f"Création de l'index FAISS avec {len(all_chunks)} chunks...")
                # Créer un vectorstore depuis les documents
                vectorstore = FAISS.from_texts(all_chunks, embeddings)
                faiss_index_path.mkdir(parents=True, exist_ok=True)
                vectorstore.save_local(str(faiss_index_path))
                print(f"✓ Index FAISS créé et sauvegardé dans {faiss_index_path}")
            else:
                # Créer un vectorstore avec des documents par défaut s'il n'y a pas de PDFs
                print("Aucun document PDF trouvé, utilisation des documents par défaut")
                default_documents = [
                    "PROFERM est spécialisé dans les portes d'entrée, les vitrages et les stores.",
                    "La gamme LUMEAL propose des solutions d'éclairage intégrées pour les portes d'entrée.",
                    "Les produits INNOSLIDE sont des systèmes de vitrage coulissants innovants.",
                    "Le catalogue général PROFERM 2024 contient toutes nos références de portes d'entrée.",
                    "Les stores PROFERM sont disponibles en différentes couleurs et matériaux.",
                    "Pour résoudre les problèmes de connexion, vérifiez d'abord votre câble réseau et redémarrez votre équipement.",
                    "Les retours de produits sont acceptés dans les 30 jours suivant l'achat avec la facture d'origine.",
                    "Le support technique est disponible du lundi au vendredi de 9h à 18h.",
                    "En cas de problème persistant, contactez notre service client au 01 23 45 67 89."
                ]
                vectorstore = FAISS.from_texts(default_documents, embeddings)
                faiss_index_path.mkdir(parents=True, exist_ok=True)
                vectorstore.save_local(str(faiss_index_path))
        else:
            print(f"Chargement de l'index FAISS existant depuis {faiss_index_path}")
            vectorstore = FAISS.load_local(str(faiss_index_path), embeddings, allow_dangerous_deserialization=True)
        
        return vectorstore
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation de FAISS: {e}")
        # Retourner un vectorstore minimal en cas d'erreur
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        default_documents = ["Assistant SAV disponible pour vous aider."]
        return FAISS.from_texts(default_documents, embeddings)

# Obtenir l'historique de conversation au format texte
def get_conversation_history(conversation_history: List[Dict]) -> str:
    """
    Convertir l'historique de conversation en texte
    """
    if not conversation_history:
        return ""
    
    history = ""
    for message in conversation_history:
        role = message.get('role', '')
        content = message.get('content', '')
        
        if role == 'user':
            history += f"User: {content}\n"
        elif role == 'assistant':
            history += f"Assistant: {content}\n"
        elif role == 'system':
            history += f"System: {content}\n"
    
    return history




        
 