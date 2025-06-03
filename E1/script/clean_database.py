#!/usr/bin/env python3
"""
Script pour nettoyer complètement la base de données.

Ce script supprime toutes les données des tables de production
et remet les compteurs automatiques à zéro.

⚠️ ATTENTION: Ce script supprime TOUTES les données!
Utilisez-le seulement pour les tests ou pour repartir à zéro.

Utilisation: python clean_database.py
"""

import os
import psycopg2
import logging

# Configuration du système de logs pour voir ce qui se passe
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_database():
    """
    Fonction principale qui vide complètement la base de données.
    
    Cette fonction:
    1. Se connecte à la base de données
    2. Supprime toutes les données de toutes les tables
    3. Remet les compteurs automatiques (séquences) à zéro
    4. Vérifie que tout est bien vide
    
    Returns:
        bool: True si le nettoyage réussit, False sinon
    """
    try:
        logger.info("🧹 Démarrage du nettoyage de la base de données...")
        
        # === ÉTAPE 1: RÉCUPÉRER LA CONFIGURATION ===
        # Les paramètres de connexion peuvent être surchargés par des variables d'environnement
        # Utilisation des variables d'environnement du docker-compose.yaml
        db_host = os.getenv('POSTGRES_HOST')  # 'db' est le nom du service dans docker-compose
        db_name = os.getenv('POSTGRES_DB')
        db_user = os.getenv('POSTGRES_USER')
        db_pass = os.getenv('POSTGRES_PASSWORD')
        
        logger.info(f"📡 Connexion à la base de données: {db_host}/{db_name}")
        
        # === ÉTAPE 2: SE CONNECTER À LA BASE DE DONNÉES ===
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass
        )
        cur = conn.cursor()
        
        logger.info("✅ Connexion à la base de données réussie")
        
        # === ÉTAPE 3: SUPPRIMER TOUTES LES DONNÉES ===
        logger.info("🗑️ Suppression de toutes les données...")
        
        # Liste des tables dans l'ordre de suppression
        # IMPORTANT: L'ordre est crucial à cause des clés étrangères!
        # On doit supprimer d'abord les tables "enfants" puis les tables "parents"
        tables = [
            'piece_production',      # Dépend de session_production
            'periode_arret',         # Dépend de session_production
            'periode_attente',       # Dépend de session_production
            'job_profil',           # Dépend de session_production
            'session_production',    # Dépend de centre_usinage
            'centre_usinage'        # Table principale (pas de dépendance)
        ]
        
        # Supprimer les données de chaque table
        for table in tables:
            try:
                logger.info(f"  🗂️ Nettoyage de la table: {table}")
                
                # Exécuter la commande DELETE pour vider la table
                cur.execute(f"DELETE FROM {table}")
                
                # Récupérer le nombre de lignes supprimées
                count = cur.rowcount
                logger.info(f"    ✅ {count} lignes supprimées de {table}")
                
            except Exception as e:
                logger.warning(f"    ⚠️ Erreur lors de la suppression de {table}: {e}")
        
        # === ÉTAPE 4: REMETTRE LES COMPTEURS À ZÉRO ===
        logger.info("🔄 Remise à zéro des compteurs automatiques...")
        
        # Liste des séquences (compteurs automatiques) à remettre à zéro
        # Ces séquences gèrent les ID auto-incrémentés des tables
        sequences = [
            'centre_usinage_id_seq',
            'session_production_id_seq',
            'job_profil_id_seq',
            'periode_attente_id_seq',
            'periode_arret_id_seq',
            'piece_production_id_seq'
        ]
        
        # Remettre chaque séquence à 1
        for seq in sequences:
            try:
                logger.info(f"  🔢 Remise à zéro de: {seq}")
                
                # Commande pour remettre la séquence à 1
                cur.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1")
                logger.info(f"    ✅ {seq} remise à 1")
                
            except Exception as e:
                logger.warning(f"    ⚠️ Erreur lors de la remise à zéro de {seq}: {e}")
        
        # === ÉTAPE 5: CONFIRMER TOUTES LES MODIFICATIONS ===
        logger.info("💾 Sauvegarde des modifications...")
        conn.commit()
        logger.info("✅ Toutes les modifications ont été sauvegardées")
        
        # === ÉTAPE 6: VÉRIFIER QUE TOUT EST VIDE ===
        logger.info("🔍 Vérification que le nettoyage est complet...")
        
        all_empty = True
        
        # Vérifier chaque table (dans l'ordre inverse pour l'affichage)
        for table in reversed(tables):
            try:
                # Compter le nombre de lignes restantes
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                
                if count == 0:
                    status = "✅ VIDE"
                else:
                    status = f"❌ {count} lignes restantes"
                    all_empty = False
                
                logger.info(f"  📊 {table}: {status}")
                
            except Exception as e:
                logger.error(f"  ❌ Erreur lors de la vérification de {table}: {e}")
                all_empty = False
        
        # === ÉTAPE 7: FERMER LES CONNEXIONS ===
        cur.close()
        conn.close()
        
        # === RÉSULTAT FINAL ===
        if all_empty:
            logger.info("\n🎉 BASE DE DONNÉES COMPLÈTEMENT NETTOYÉE!")
            logger.info("✨ Toutes les tables sont vides et prêtes pour de nouvelles données")
            return True
        else:
            logger.error("\n⚠️ Le nettoyage n'est pas complet!")
            logger.error("Certaines tables contiennent encore des données")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur critique lors du nettoyage de la base de données: {e}")
        
        # Afficher plus de détails sur l'erreur
        import traceback
        logger.error("🔍 Détails de l'erreur:")
        logger.error(traceback.format_exc())
        
        return False


def main():
    """
    Fonction principale avec demande de confirmation.
    
    Returns:
        int: Code de sortie (0 = succès, 1 = erreur)
    """
    logger.info("=" * 80)
    logger.info("🧹 SCRIPT DE NETTOYAGE DE LA BASE DE DONNÉES")
    logger.info("=" * 80)
    
    # Avertissement de sécurité
    logger.warning("⚠️ ATTENTION: Ce script va supprimer TOUTES les données!")
    logger.warning("⚠️ Cette action est IRRÉVERSIBLE!")
    
    # Demander confirmation à l'utilisateur
    try:
        response = input("\n❓ Êtes-vous sûr de vouloir continuer? (tapez 'OUI' pour confirmer): ")
        
        if response.upper() != 'OUI':
            logger.info("❌ Nettoyage annulé par l'utilisateur")
            return 0
        
    except KeyboardInterrupt:
        logger.info("\n❌ Nettoyage interrompu par l'utilisateur (Ctrl+C)")
        return 0
    
    # Exécuter le nettoyage
    logger.info("\n🚀 Démarrage du nettoyage...")
    success = clean_database()
    
    if success:
        logger.info("\n🎯 Nettoyage terminé avec succès!")
        return 0
    else:
        logger.error("\n💥 Erreur lors du nettoyage!")
        return 1


# Point d'entrée du script
if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 