#!/usr/bin/env python3
"""
Script pour créer un utilisateur administrateur
Usage: python create_admin.py [username] [password] [email]
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.append(str(Path(__file__).parent))

from database import SessionLocal
from models import User
from auth import get_password_hash

def create_admin_user(username="admin", password="admin123", email="admin@chatbot-sav.com"):
    """Créer un utilisateur administrateur"""
    db = SessionLocal()
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"⚠️  L'utilisateur '{username}' existe déjà")
            return False
        
        # Créer le nouvel utilisateur admin
        admin_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("✅ Utilisateur administrateur créé avec succès !")
        print(f"   👤 Username: {username}")
        print(f"   🔑 Password: {password}")
        print(f"   📧 Email: {email}")
        print(f"   🛡️  Rôles: Staff + Superuser")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def list_users():
    """Lister tous les utilisateurs"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("\n📋 Liste des utilisateurs:")
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
            print(f"   📅 Créé le: {user.created_at}")
            print()
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_users()
    else:
        # Récupérer les arguments ou utiliser les valeurs par défaut
        username = sys.argv[1] if len(sys.argv) > 1 else "admin"
        password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
        email = sys.argv[3] if len(sys.argv) > 3 else "admin@chatbot-sav.com"
        
        print("🚀 Création d'un utilisateur administrateur...")
        create_admin_user(username, password, email) 