#!/usr/bin/env python3
"""
Script principal pour traiter automatiquement les fichiers LOG depuis le serveur FTP
et les sauvegarder dans la base de données PostgreSQL.

Ce script est conçu pour être exécuté automatiquement par cron (tâche planifiée).
Il fait le travail suivant:
1. Se connecte au serveur FTP
2. Télécharge tous les fichiers LOG des différents centres d'usinage
3. Analyse le contenu de chaque fichier
4. Sauvegarde les données dans PostgreSQL
5. Supprime les fichiers traités du FTP

Utilisation:
- Exécution manuelle: python script.py
- Exécution par cron: 0 */6 * * * /usr/bin/python3 /app/script.py
"""

import sys
import os
import logging
from datetime import datetime

# Ajouter le répertoire courant au path pour pouvoir importer notre service
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ftp_log_service import FTPLogService

# Configuration du système de logs pour le script principal
# Les logs seront écrits dans un fichier ET affichés à l'écran
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Écrire les logs dans un fichier (pour cron)
        logging.FileHandler('/app/cron.log'),
        # Afficher les logs à l'écran (pour exécution manuelle)
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Fonction principale du script qui orchestre tout le processus.
    
    Returns:
        int: Code de sortie (0 = succès, 1 = erreur)
    """
    # Enregistrer l'heure de début pour calculer la durée totale
    start_time = datetime.now()
    
    # === EN-TÊTE DU TRAITEMENT ===
    logger.info("=" * 80)
    logger.info(f"🚀 DÉBUT DU TRAITEMENT DES LOGS FTP - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        # === ÉTAPE 1: CRÉER UNE INSTANCE DU SERVICE ===
        logger.info("📋 Initialisation du service FTP Log...")
        service = FTPLogService()
        
        # === ÉTAPE 2: TRAITER TOUS LES FICHIERS LOG ===
        logger.info("🔄 Démarrage du traitement de tous les fichiers LOG...")
        
        # delete_after_processing=True pour supprimer les fichiers après traitement
        # C'est le comportement normal en production
        success = service.process_all_logs(delete_after_processing=True)
        
        # === ÉTAPE 3: CALCULER LA DURÉE ET AFFICHER LE RÉSULTAT ===
        end_time = datetime.now()
        duration = end_time - start_time
        
        if success:
            # === TRAITEMENT RÉUSSI ===
            logger.info("=" * 80)
            logger.info(f"🎉 TRAITEMENT TERMINÉ AVEC SUCCÈS - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"⏱️ Durée totale: {duration}")
            logger.info("=" * 80)
            
            return 0  # Code de sortie 0 = succès
        else:
            # === TRAITEMENT AVEC ERREURS ===
            logger.error("=" * 80)
            logger.error(f"⚠️ TRAITEMENT TERMINÉ AVEC DES ERREURS - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.error(f"⏱️ Durée totale: {duration}")
            logger.error("=" * 80)
            
            return 1  # Code de sortie 1 = erreur
        
    except Exception as e:
        # === ERREUR INATTENDUE ===
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.error("=" * 80)
        logger.error(f"💥 ERREUR CRITIQUE LORS DU TRAITEMENT - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error(f"⏱️ Durée avant erreur: {duration}")
        logger.error(f"❌ Erreur: {str(e)}")
        logger.error("=" * 80)
        
        # Afficher les détails complets de l'erreur pour le débogage
        import traceback
        logger.error("🔍 Détails complets de l'erreur:")
        logger.error(traceback.format_exc())
        
        return 1  # Code de sortie 1 = erreur


# Point d'entrée du script
if __name__ == "__main__":
    # Exécuter la fonction principale et utiliser son code de sortie
    exit_code = main()
    
    # Terminer le script avec le code de sortie approprié
    # Ceci permet aux systèmes de surveillance (comme cron) de savoir si le script a réussi
    sys.exit(exit_code)
