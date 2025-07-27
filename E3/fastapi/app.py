from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from datetime import datetime

# FastAPI app
app = FastAPI(title="Chatbot SAV", description="Application de chatbot pour le service après-vente")

# Static files et templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Importer la configuration de base de données
from database import engine

# Importer et inclure les routes
from routes import router
app.include_router(router)

# Créer les tables au démarrage (avec gestion d'erreur)
@app.on_event("startup")
async def startup_event():
    import asyncio
    import time
    
    # Attendre que la base de données soit prête avec retry
    max_retries = 10
    for attempt in range(max_retries):
        try:
            from models import Base, User
            from database import SessionLocal
            from auth import get_password_hash
            
            # Tester la connexion en créant les tables
            Base.metadata.create_all(bind=engine)
            print("✅ Tables créées avec succès")
            
            # Créer les utilisateurs par défaut
            db = SessionLocal()
            try:
                from models import ClientUser, Commande
                
                # Créer l'utilisateur admin
                admin_user = db.query(User).filter(User.username == "admin").first()
                if not admin_user:
                    admin_user = User(
                        username="admin",
                        email="admin@chatbot-sav.com",
                        hashed_password=get_password_hash("admin123"),
                        is_active=True,
                        is_staff=True,
                        is_superuser=True
                    )
                    db.add(admin_user)
                    db.commit()
                    print("✅ Utilisateur admin créé avec succès")
                    print("   👤 Username: admin")
                    print("   🔑 Password: admin123")
                    print("   📧 Email: admin@chatbot-sav.com")
                else:
                    print("ℹ️  Utilisateur admin existe déjà")
                
                # Créer le premier client
                client1_user = db.query(User).filter(User.username == "martin").first()
                if not client1_user:
                    client1_user = User(
                        username="martin",
                        email="martin.dupont@email.com",
                        hashed_password=get_password_hash("client123"),
                        is_active=True,
                        is_staff=False,
                        is_superuser=False,
                        nom="Dupont",
                        prenom="Martin",
                        telephone="01 23 45 67 89",
                        adresse="123 Rue de la Paix, 75001 Paris"
                    )
                    db.add(client1_user)
                    db.commit()
                    db.refresh(client1_user)
                    
                    # Créer le profil client
                    client1_profile = ClientUser(
                        user_id=client1_user.id,
                        is_client_only=True
                    )
                    db.add(client1_profile)
                    
                    # Créer les commandes pour client1
                    commande1 = Commande(
                        numero_commande="CMD2024-001",
                        user_id=client1_user.id,
                        date_commande=datetime(2024, 1, 15, 10, 30),
                        date_livraison=datetime(2024, 1, 25, 14, 0),
                        statut="livree",
                        montant_ht=1250.00,
                        montant_ttc=1500.00,
                        produits=[
                            {"type": "Porte d'entrée", "modele": "P-ALU-DESIGN", "quantite": 1, "prix": 1500.00}
                        ],
                        adresse_livraison="123 Rue de la Paix, 75001 Paris",
                        notes="Livraison en matinée"
                    )
                    db.add(commande1)
                    
                    commande2 = Commande(
                        numero_commande="CMD2024-015",
                        user_id=client1_user.id,
                        date_commande=datetime(2024, 3, 10, 16, 45),
                        statut="en_cours",
                        montant_ht=800.00,
                        montant_ttc=960.00,
                        produits=[
                            {"type": "Fenêtre", "modele": "F-PVC-2V", "quantite": 2, "prix": 480.00}
                        ],
                        adresse_livraison="123 Rue de la Paix, 75001 Paris",
                        notes="Fabrication en cours"
                    )
                    db.add(commande2)
                    
                    db.commit()
                    print("✅ Client Martin Dupont créé avec succès")
                    print("   👤 Username: martin")
                    print("   🔑 Password: client123")
                    print("   📧 Email: martin.dupont@email.com")
                    print("   📦 2 commandes créées")
                else:
                    print("ℹ️  Client Martin existe déjà")
                
                # Créer le deuxième client
                client2_user = db.query(User).filter(User.username == "sophie").first()
                if not client2_user:
                    client2_user = User(
                        username="sophie",
                        email="sophie.martin@email.com",
                        hashed_password=get_password_hash("client123"),
                        is_active=True,
                        is_staff=False,
                        is_superuser=False,
                        nom="Martin",
                        prenom="Sophie",
                        telephone="04 78 12 34 56",
                        adresse="456 Avenue des Champs, 69000 Lyon"
                    )
                    db.add(client2_user)
                    db.commit()
                    db.refresh(client2_user)
                    
                    # Créer le profil client
                    client2_profile = ClientUser(
                        user_id=client2_user.id,
                        is_client_only=True
                    )
                    db.add(client2_profile)
                    
                    # Créer les commandes pour client2
                    commande3 = Commande(
                        numero_commande="CMD2024-008",
                        user_id=client2_user.id,
                        date_commande=datetime(2024, 2, 5, 9, 15),
                        date_livraison=datetime(2024, 2, 20, 11, 30),
                        statut="livree",
                        montant_ht=2100.00,
                        montant_ttc=2520.00,
                        produits=[
                            {"type": "Porte-fenêtre", "modele": "PF-ALU-3V", "quantite": 1, "prix": 2520.00}
                        ],
                        adresse_livraison="456 Avenue des Champs, 69000 Lyon",
                        notes="Installation réussie"
                    )
                    db.add(commande3)
                    
                    commande4 = Commande(
                        numero_commande="CMD2024-025",
                        user_id=client2_user.id,
                        date_commande=datetime(2024, 4, 12, 13, 20),
                        statut="en_cours",
                        montant_ht=600.00,
                        montant_ttc=720.00,
                        produits=[
                            {"type": "Volet roulant", "modele": "VR-ELEC-SOL", "quantite": 3, "prix": 240.00}
                        ],
                        adresse_livraison="456 Avenue des Champs, 69000 Lyon",
                        notes="Commande en préparation"
                    )
                    db.add(commande4)
                    
                    db.commit()
                    print("✅ Client Sophie Martin créé avec succès")
                    print("   👤 Username: sophie")
                    print("   🔑 Password: client123")
                    print("   📧 Email: sophie.martin@email.com")
                    print("   📦 2 commandes créées")
                else:
                    print("ℹ️  Client Sophie existe déjà")
                
                break  # Sortir de la boucle si tout va bien
            except Exception as e:
                print(f"⚠️  Erreur lors de la création des utilisateurs: {e}")
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️  Tentative {attempt + 1}/{max_retries} - Erreur de connexion DB: {e}")
            if attempt < max_retries - 1:
                print("⏳ Nouvelle tentative dans 3 secondes...")
                await asyncio.sleep(3)
            else:
                print("❌ Impossible de se connecter à la base de données après plusieurs tentatives")
                print("Les tables seront créées lors de la première requête")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 