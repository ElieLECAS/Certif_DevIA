#!/usr/bin/env python3
"""
Script pour vider complètement la base de données
"""

import os
import psycopg2
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_database():
    """Vide complètement la base de données"""
    try:
        # Configuration base de données
        db_host = os.getenv('DB_HOST', 'db')
        db_name = os.getenv('DB_NAME', 'logsdb')
        db_user = os.getenv('DB_USER', 'user')
        db_pass = os.getenv('DB_PASS', 'password')
        
        # Connexion à la base de données
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass
        )
        cur = conn.cursor()
        
        logger.info("🗑️ Début du nettoyage de la base de données...")
        
        # Liste des tables dans l'ordre de suppression (à cause des clés étrangères)
        tables = [
            'piece_production',
            'periode_arret', 
            'periode_attente',
            'job_profil',
            'session_production',
            'centre_usinage'
        ]
        
        # Supprimer toutes les données
        for table in tables:
            try:
                cur.execute(f"DELETE FROM {table}")
                count = cur.rowcount
                logger.info(f"✅ Table {table}: {count} lignes supprimées")
            except Exception as e:
                logger.warning(f"⚠️ Erreur suppression {table}: {e}")
        
        # Remettre à zéro les séquences (auto-increment)
        sequences = [
            'centre_usinage_id_seq',
            'session_production_id_seq',
            'job_profil_id_seq',
            'periode_attente_id_seq',
            'periode_arret_id_seq',
            'piece_production_id_seq'
        ]
        
        for seq in sequences:
            try:
                cur.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1")
                logger.info(f"🔄 Séquence {seq} remise à zéro")
            except Exception as e:
                logger.warning(f"⚠️ Erreur reset séquence {seq}: {e}")
        
        # Valider les changements
        conn.commit()
        
        # Vérifier que tout est vide
        logger.info("\n📊 Vérification du nettoyage:")
        for table in reversed(tables):  # Ordre inverse pour l'affichage
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            status = "✅ VIDE" if count == 0 else f"❌ {count} lignes restantes"
            logger.info(f"   {table}: {status}")
        
        cur.close()
        conn.close()
        
        logger.info("\n🎉 Base de données complètement nettoyée !")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage base de données: {e}")
        return False

if __name__ == "__main__":
    clean_database() 