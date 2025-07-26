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

def load_all_jsons(user=None) -> Tuple[Dict, Dict, Dict, Dict, Dict]:
    """
    Charger tous les fichiers JSON nécessaires pour le contexte
    """
    try:
        # Chemins vers les fichiers JSON (adaptés de la structure Django)
        base_path = Path("RAG/preprompts")
        
        # S'assurer que le répertoire existe
        base_path.mkdir(parents=True, exist_ok=True)
        
        preprompt_path = base_path / "preprompt_SAV.json"
        client_path = base_path / "client_id.json"
        renseignements_path = base_path / "protocole_renseignements.json"
        retours_path = base_path / "protocole_retour.json"
        commandes_path = base_path / "commandes_client.json"
        
        # Charger les fichiers s'ils existent, sinon retourner des objets par défaut
        preprompt = load_json(str(preprompt_path)) if preprompt_path.exists() else {
            "content": "Vous êtes un assistant SAV professionnel."
        }
        
        # Si un utilisateur est fourni, créer un objet client à partir de ses informations
        if user:
            try:
                # Créer un objet client avec les informations de l'utilisateur connecté
                client_info = {
                    "client_informations": {
                        "id": user.id,
                        "nom": getattr(user, 'last_name', '') or user.username.split('_')[-1] if '_' in user.username else '',
                        "prenom": getattr(user, 'first_name', '') or user.username.split('_')[0] if '_' in user.username else user.username,
                        "adresse": "",  # À compléter si vous stockez cette information
                        "telephone": "",  # À compléter si vous stockez cette information
                        "email": user.email,
                        "date_creation": user.created_at.strftime("%Y-%m-%d") if hasattr(user, 'created_at') else datetime.now().strftime("%Y-%m-%d"),
                        "historique": {
                            "nb_commandes": 0,  # À récupérer de la base de données si disponible
                            "derniere_commande": "",  # À récupérer de la base de données si disponible
                            "interventions_precedentes": []  # À récupérer de la base de données si disponible
                        }
                    }
                }
                client = client_info
            except Exception as e:
                print(f"Erreur lors de la création des infos client: {e}")
                # En cas d'erreur, on utilise le fichier JSON statique
                client = load_json(str(client_path)) if client_path.exists() else {}
        else:
            # Si aucun utilisateur n'est fourni, on utilise le fichier JSON statique
            client = load_json(str(client_path)) if client_path.exists() else {}
        
        renseignements = load_json(str(renseignements_path)) if renseignements_path.exists() else {}
        retours = load_json(str(retours_path)) if retours_path.exists() else {}
        commandes = load_json(str(commandes_path)) if commandes_path.exists() else {"commandes": []}
        
        return preprompt, client, renseignements, retours, commandes
        
    except Exception as e:
        print(f"Erreur lors du chargement des JSONs: {e}")
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
        
        if not faiss_index_path.exists():
            all_documents = []
            
            # Vérifier si le répertoire contient des PDFs
            if pdf_directory.exists() and any(pdf_directory.glob("*.pdf")):
                # Charger les documents PDF
                for pdf_file in pdf_directory.glob("*.pdf"):
                    try:
                        with fitz.open(str(pdf_file)) as pdf_doc:
                            text = ""
                            for page in pdf_doc:
                                text += page.get_text()  # Extraire le texte de chaque page
                            all_documents.append(text)  # Ajouter le texte du PDF
                    except Exception as e:
                        print(f"Erreur lors de la lecture du PDF {pdf_file.name}: {str(e)}")
            
            # S'il y a des documents à indexer
            if all_documents:
                # Fractionner les documents en parties gérables
                text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=30, separator="\n")
                split_documents = text_splitter.split_text("\n".join(all_documents))  # Concaténer les documents avant fractionnement
                
                # Créer un vectorstore depuis les documents
                vectorstore = FAISS.from_texts(split_documents, embeddings)
                faiss_index_path.mkdir(parents=True, exist_ok=True)
                vectorstore.save_local(str(faiss_index_path))
            else:
                # Créer un vectorstore avec des documents par défaut s'il n'y a pas de PDFs
                default_documents = [
                    "Pour résoudre les problèmes de connexion, vérifiez d'abord votre câble réseau et redémarrez votre équipement.",
                    "Les retours de produits sont acceptés dans les 30 jours suivant l'achat avec la facture d'origine.",
                    "Pour les problèmes de performance, essayez de vider le cache et redémarrer l'application.",
                    "Le support technique est disponible du lundi au vendredi de 9h à 18h.",
                    "En cas de problème persistant, contactez notre service client au 01 23 45 67 89."
                ]
                vectorstore = FAISS.from_texts(default_documents, embeddings)
                faiss_index_path.mkdir(parents=True, exist_ok=True)
                vectorstore.save_local(str(faiss_index_path))
        else:
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



def create_sample_data():
    """
    Créer des données d'exemple pour tester l'application
    """
    try:
        # Créer le dossier RAG/preprompts (comme dans Django)
        rag_dir = Path("RAG/preprompts")
        rag_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer le dossier RAG/Catalogues pour les PDFs
        catalogues_dir = Path("RAG/Catalogues")
        catalogues_dir.mkdir(parents=True, exist_ok=True)
        
        # Preprompt SAV d'exemple
        preprompt_sav = {
            "content": "Vous êtes un assistant virtuel expert en service après-vente. Vous aidez les clients avec leurs questions techniques, leurs commandes, et leurs problèmes de produits. Soyez professionnel, courtois et précis dans vos réponses. Utilisez les informations des catalogues et des protocoles pour donner des réponses précises."
        }
        
        with open(rag_dir / "preprompt_SAV.json", 'w', encoding='utf-8') as f:
            json.dump(preprompt_sav, f, indent=2, ensure_ascii=False)
        
        # Client ID d'exemple
        client_id = {
            "client_informations": {
                "id": 1,
                "nom": "Dupont",
                "prenom": "Jean",
                "adresse": "123 Rue de la Paix, 75001 Paris",
                "telephone": "01 23 45 67 89",
                "email": "jean.dupont@email.com",
                "date_creation": "2024-01-15",
                "historique": {
                    "nb_commandes": 3,
                    "derniere_commande": "2024-07-15",
                    "interventions_precedentes": [
                        "Problème de connexion résolu le 2024-06-10",
                        "Remplacement pièce défectueuse le 2024-05-20"
                    ]
                }
            }
        }
        
        with open(rag_dir / "client_id.json", 'w', encoding='utf-8') as f:
            json.dump(client_id, f, indent=2, ensure_ascii=False)
        
        # Protocole renseignements
        protocole_renseignements = {
            "procedures_diagnostic": [
                "Vérifiez d'abord l'état de votre connexion internet",
                "Redémarrez l'équipement en cas de problème",
                "Consultez le manuel d'utilisation",
                "Vérifiez les voyants lumineux sur l'équipement"
            ],
            "questions_types": [
                "Depuis quand le problème se manifeste-t-il ?",
                "Avez-vous effectué des modifications récentes ?",
                "Le problème est-il permanent ou intermittent ?",
                "Avez-vous des messages d'erreur spécifiques ?"
            ],
            "faq": [
                {
                    "question": "Comment redémarrer mon équipement ?",
                    "reponse": "Débranchez l'alimentation pendant 30 secondes, puis rebranchez."
                },
                {
                    "question": "Que faire si mon produit ne fonctionne pas ?",
                    "reponse": "Vérifiez les connexions et consultez le guide de dépannage."
                }
            ]
        }
        
        with open(rag_dir / "protocole_renseignements.json", 'w', encoding='utf-8') as f:
            json.dump(protocole_renseignements, f, indent=2, ensure_ascii=False)
        
        # Protocole retour
        protocole_retour = {
            "conditions_retour": [
                "Retour possible dans les 30 jours suivant l'achat",
                "Produit en bon état de fonctionnement",
                "Emballage d'origine conservé",
                "Facture d'achat obligatoire"
            ],
            "procedure": [
                "Contactez le service client au 01 23 45 67 89",
                "Obtenez un numéro de retour (RMA)",
                "Emballez soigneusement le produit",
                "Expédiez avec le transporteur indiqué"
            ],
            "delais": {
                "traitement_demande": "24-48h",
                "remboursement": "7-10 jours ouvrés",
                "echange": "5-7 jours ouvrés"
            }
        }
        
        with open(rag_dir / "protocole_retour.json", 'w', encoding='utf-8') as f:
            json.dump(protocole_retour, f, indent=2, ensure_ascii=False)
        
        # Commandes client
        commandes_client = {
            "commandes": [
                {
                    "numero": "CMD-2024-001",
                    "date": "2024-07-15",
                    "statut": "Livrée",
                    "produits": ["Routeur WiFi Pro", "Câble Ethernet 5m"],
                    "montant": 89.99
                },
                {
                    "numero": "CMD-2024-002",
                    "date": "2024-06-10",
                    "statut": "Expédiée",
                    "produits": ["Adaptateur USB-C"],
                    "montant": 25.50
                }
            ],
            "statuts_possibles": [
                "En préparation",
                "Expédiée",
                "Livrée",
                "Retournée",
                "Annulée"
            ]
        }
        
        with open(rag_dir / "commandes_client.json", 'w', encoding='utf-8') as f:
            json.dump(commandes_client, f, indent=2, ensure_ascii=False)
        
        print("Données d'exemple créées avec succès dans RAG/preprompts/")
        print("Placez vos fichiers PDF dans RAG/Catalogues/ pour la recherche FAISS")
        
    except Exception as e:
        print(f"Erreur lors de la création des données d'exemple: {e}")

# Créer les données d'exemple au démarrage si elles n'existent pas
if not Path("RAG").exists():
    create_sample_data() 