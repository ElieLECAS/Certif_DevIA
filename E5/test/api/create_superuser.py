#!/usr/bin/env python3
"""
Script pour créer le superuser GMAO
"""

import os
import sys
import time
from sqlalchemy import create_engine, text
from auth import get_password_hash

def wait_for_database_tables(engine, max_retries=15, delay=1):
    """Attendre que la table utilisateurs soit créée"""
    print("⏳ Attente de la création des tables de base de données...")
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                # Vérifier si la table utilisateurs existe
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'utilisateurs'
                    );
                """))
                
                if result.fetchone()[0]:
                    print("✅ Table utilisateurs trouvée!")
                    return True
                    
        except Exception as e:
            if attempt < 3:  # Afficher les erreurs seulement pour les 3 premières tentatives
                print(f"Tentative {attempt + 1}/{max_retries}: {e}")
        
        if attempt < max_retries - 1:  # Ne pas attendre après la dernière tentative
            print(f"⏳ Attente de {delay} seconde(s) avant la prochaine tentative...")
            time.sleep(delay)
    
    print("❌ Impossible de trouver la table utilisateurs après plusieurs tentatives")
    return False

def create_superuser():
    """Créer le superuser si les variables d'environnement sont définies"""
    
    # Récupérer les variables d'environnement
    username = os.getenv('SUPERUSER_USERNAME')
    email = os.getenv('SUPERUSER_EMAIL')
    nom_complet = os.getenv('SUPERUSER_NOM_COMPLET')
    password = os.getenv('SUPERUSER_PASSWORD')
    role = os.getenv('SUPERUSER_ROLE')
    
    # Vérifier si toutes les variables sont définies
    if not all([username, email, nom_complet, password, role]):
        print("Variables SUPERUSER_* non définies - aucun superuser créé")
        return
    
    # Connexion à la base de données
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:postgres@postgres:5432/db')
    engine = create_engine(database_url)
    
    # Attendre que les tables soient créées
    if not wait_for_database_tables(engine):
        print("❌ Échec de la création du superuser: tables non disponibles")
        return
    
    try:
        with engine.connect() as conn:
            # Vérifier si l'utilisateur existe déjà
            result = conn.execute(text("SELECT id FROM utilisateurs WHERE username = :username"), 
                                {"username": username})
            if result.fetchone():
                print(f"✅ Utilisateur {username} existe déjà")
                return
            
            # Créer le superuser
            hashed_password = get_password_hash(password)
            
            conn.execute(text("""
                INSERT INTO utilisateurs (username, email, nom_complet, hashed_password, role, statut)
                VALUES (:username, :email, :nom_complet, :hashed_password, :role, 'actif')
            """), {
                "username": username,
                "email": email,
                "nom_complet": nom_complet,
                "hashed_password": hashed_password,
                "role": role
            })
            
            conn.commit()
            print(f"✅ Superuser {username} créé avec succès (rôle: {role})")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du superuser: {e}")

if __name__ == "__main__":
    create_superuser() 