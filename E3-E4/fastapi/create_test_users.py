#!/usr/bin/env python3
"""
Script pour créer des utilisateurs de test avec leurs données
Usage: python create_test_users.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire courant au path
sys.path.append(str(Path(__file__).parent))

from database import SessionLocal
from models import User, ClientUser, Commande
from auth import get_password_hash

def create_test_users():
    """Créer les utilisateurs de test avec leurs données"""
    db = SessionLocal()
    try:
        print("🚀 Création des utilisateurs de test...")
        
        # Créer le premier client - Martin Dupont
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
        
        # Créer le deuxième client - Sophie Martin
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
        
        print("\n🎉 Création des utilisateurs de test terminée !")
        print("\n📋 Récapitulatif des comptes :")
        print("   👑 Admin: admin / admin123")
        print("   👤 Client 1: martin / client123")
        print("   👤 Client 2: sophie / client123")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des utilisateurs de test: {e}")
        db.rollback()
    finally:
        db.close()

def list_test_users():
    """Lister les utilisateurs de test"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.username.in_(["admin", "martin", "sophie"])).all()
        print("\n📋 Liste des utilisateurs de test:")
        print("-" * 50)
        for user in users:
            roles = []
            if user.is_staff:
                roles.append("Staff")
            if user.is_superuser:
                roles.append("Superuser")
            if user.is_active:
                roles.append("Actif")
            else:
                roles.append("Inactif")
            
            print(f"👤 {user.username} ({user.email})")
            print(f"   🛡️  Rôles: {', '.join(roles)}")
            if user.nom and user.prenom:
                print(f"   📝 Nom: {user.prenom} {user.nom}")
            if user.telephone:
                print(f"   📞 Téléphone: {user.telephone}")
            if user.adresse:
                print(f"   🏠 Adresse: {user.adresse}")
            
            # Compter les commandes
            commandes_count = db.query(Commande).filter(Commande.user_id == user.id).count()
            print(f"   📦 Commandes: {commandes_count}")
            print()
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_test_users()
    else:
        create_test_users() 