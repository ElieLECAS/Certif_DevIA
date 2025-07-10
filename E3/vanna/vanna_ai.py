from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
import os
from dotenv import load_dotenv
from langfuse.openai import openai

load_dotenv()

# Configuration des variables d'environnement pour Langfuse
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv('LANGFUSE_SECRET_KEY', '')
os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv('LANGFUSE_PUBLIC_KEY', '')
os.environ["LANGFUSE_HOST"] = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        
        # Remplacer le client OpenAI par la version instrumentée Langfuse
        if hasattr(self, '_client'):
            # Sauvegarder la clé API
            api_key = getattr(self._client, 'api_key', config.get('api_key'))
            # Remplacer par le client Langfuse (drop-in replacement)
            self._client = openai.OpenAI(api_key=api_key)
            print("✅ Client OpenAI instrumenté avec Langfuse")

vn = MyVanna(config={'api_key':os.getenv('OPENAI_API_KEY'), 'model': 'gpt-4-mini'})
# vn.remove_training_data()

vn.connect_to_postgres(host=os.getenv('POSTGRES_HOST'), dbname=os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), port=os.getenv('POSTGRES_PORT'))

from vanna.flask import VannaFlaskApp

# Créer l'application Flask avec monitoring automatique Langfuse
flask_app = VannaFlaskApp(vn, allow_llm_to_see_data=True)

print(f"📊 Dashboard: \nhttps://cloud.langfuse.com \n")

# Vérifier la connexion Langfuse
try:
    # Test simple pour vérifier la configuration
    test_keys = [
        ("LANGFUSE_SECRET_KEY", os.getenv('LANGFUSE_SECRET_KEY')),
        ("LANGFUSE_PUBLIC_KEY", os.getenv('LANGFUSE_PUBLIC_KEY'))
    ]
    
    missing_keys = [name for name, value in test_keys if not value]
    
    if missing_keys:
        print(f"⚠️ Variables manquantes: {', '.join(missing_keys)}")
        print("💡 Ajoutez-les à votre fichier .env pour activer le monitoring")
        
except Exception as e:
    print(f"⚠️ Erreur de configuration Langfuse: {e}")

# Lancer l'application
flask_app.run(host='0.0.0.0', port=8084)