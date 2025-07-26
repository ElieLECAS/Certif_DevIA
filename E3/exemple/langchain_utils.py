import os
import json
import fitz
from datetime import datetime
import csv
from django.conf import settings
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub

# Fonction pour sauvegarder l'image téléchargée
def save_uploaded_file(uploaded_file):
    # Créer un répertoire pour sauvegarder les images si nécessaire
    upload_dir = os.path.join(settings.MEDIA_ROOT, "uploaded_images")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Générer un nom de fichier unique avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    
    # Enregistrer l'image avec un nom unique
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    
    # Retourner l'URL relative pour l'accès via navigateur
    media_url = settings.MEDIA_URL.rstrip('/')
    relative_path = f"{media_url}/uploaded_images/{filename}"
    
    return relative_path

# Fonction pour lire un fichier JSON
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

# Fonction pour charger tous les JSON nécessaires
def load_all_jsons(user=None):
    base_path = os.path.join(settings.BASE_DIR, 'RAG', 'preprompts')
    
    # S'assurer que le répertoire existe
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    preprompt_path = os.path.join(base_path, 'preprompt_SAV.json')
    client_path = os.path.join(base_path, 'client_id.json')
    renseignements_path = os.path.join(base_path, 'protocole_renseignements.json')
    retours_path = os.path.join(base_path, 'protocole_retour.json')
    commandes_path = os.path.join(base_path, 'commandes_client.json')
    
    # Charger les fichiers s'ils existent, sinon retourner des objets vides
    preprompt = load_json(preprompt_path) if os.path.exists(preprompt_path) else {"content": "Vous êtes un assistant SAV professionnel."}
    
    # Si un utilisateur est fourni, créer un objet client à partir de ses informations
    if user and user.is_authenticated:
        try:
            from django.contrib.auth.models import User
            from .models import ClientUser
            
            # Récupérer les informations du client
            client_info = {}
            
            # On vérifie si l'utilisateur est un client avec un profil
            try:
                client_profile = ClientUser.objects.get(user=user)
                
                # Créer un objet client avec les informations de l'utilisateur connecté
                client_info = {
                    "client_informations": {
                        "id": user.id,
                        "nom": user.last_name,
                        "prenom": user.first_name,
                        "adresse": "",  # À compléter si vous stockez cette information
                        "telephone": "",  # À compléter si vous stockez cette information
                        "email": user.email,
                        "date_creation": user.date_joined.strftime("%Y-%m-%d"),
                        "historique": {
                            "nb_commandes": 0,  # À récupérer de la base de données si disponible
                            "derniere_commande": "",  # À récupérer de la base de données si disponible
                            "interventions_precedentes": []  # À récupérer de la base de données si disponible
                        }
                    }
                }
            except ClientUser.DoesNotExist:
                # Si l'utilisateur n'est pas un client, on utilise quand même ses infos de base
                client_info = {
                    "client_informations": {
                        "id": user.id,
                        "nom": user.last_name,
                        "prenom": user.first_name,
                        "email": user.email,
                        "date_creation": user.date_joined.strftime("%Y-%m-%d")
                    }
                }
                
            client = client_info
        except Exception as e:
            # En cas d'erreur, on utilise le fichier JSON statique
            client = load_json(client_path) if os.path.exists(client_path) else {}
    else:
        # Si aucun utilisateur n'est fourni, on utilise le fichier JSON statique
        client = load_json(client_path) if os.path.exists(client_path) else {}
    
    renseignements = load_json(renseignements_path) if os.path.exists(renseignements_path) else {}
    retours = load_json(retours_path) if os.path.exists(retours_path) else {}
    commandes = load_json(commandes_path) if os.path.exists(commandes_path) else {"commandes": []}
    
    return preprompt, client, renseignements, retours, commandes

# Initialiser ou charger l'index FAISS
def initialize_faiss(openai_api_key):
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    pdf_directory = os.path.join(settings.BASE_DIR, "RAG", "Catalogues")
    faiss_index_path = os.path.join(settings.BASE_DIR, "faiss_index_pdf")
    
    # Créer les répertoires s'ils n'existent pas
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)
    
    if not os.path.exists(faiss_index_path):
        all_documents = []
        
        # Vérifier si le répertoire contient des PDFs
        if os.path.exists(pdf_directory) and os.listdir(pdf_directory):
            # Charger les documents PDF
            for filename in os.listdir(pdf_directory):
                if filename.endswith(".pdf"):
                    pdf_path = os.path.join(pdf_directory, filename)
                    try:
                        with fitz.open(pdf_path) as pdf_file:
                            text = ""
                            for page in pdf_file:
                                text += page.get_text()  # Extraire le texte de chaque page
                            all_documents.append(text)  # Ajouter le texte du PDF
                    except Exception as e:
                        print(f"Erreur lors de la lecture du PDF {filename}: {str(e)}")
        
        # S'il y a des documents à indexer
        if all_documents:
            # Fractionner les documents en parties gérables
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=30, separator="\n")
            split_documents = text_splitter.split_text("\n".join(all_documents))  # Concaténer les documents avant fractionnement
            
            # Créer un vectorstore depuis les documents
            vectorstore = FAISS.from_texts(split_documents, embeddings)
            os.makedirs(os.path.dirname(faiss_index_path), exist_ok=True)
            vectorstore.save_local(faiss_index_path)
        else:
            # Créer un vectorstore vide s'il n'y a pas de documents
            vectorstore = FAISS.from_texts(["Aucun document disponible."], embeddings)
            os.makedirs(os.path.dirname(faiss_index_path), exist_ok=True)
            vectorstore.save_local(faiss_index_path)
    else:
        vectorstore = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
    
    return vectorstore

# Obtenir l'historique de conversation au format texte
def get_conversation_history(conversation_history):
    history = ""
    for message in conversation_history:
        if message['role'] == 'user':
            history += f"User: {message['content']}\n"
        elif message['role'] == 'assistant':
            history += f"Assistant: {message['content']}\n"
        elif message['role'] == 'system':
            history += f"System: {message['content']}\n"
    return history

# Sauvegarder les données dans un fichier CSV
def save_conversation_to_csv(client_id, summary):
    # Créer une structure unifiée pour sauvegarder les informations
    conversation_data = {
        "client_id": client_id,
        "timestamp": str(datetime.now()),  # Date et heure de la conversation
        "summary": summary
    }
    
    file_path = os.path.join(settings.BASE_DIR, "conversation_summary.csv")
    
    # Si le fichier CSV existe déjà, ajoutez une nouvelle ligne
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=conversation_data.keys())
        
        # Si c'est le premier enregistrement, ajoutez l'entête
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(conversation_data) 