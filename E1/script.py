#!/usr/bin/env python3
"""
Script principal pour traiter les fichiers LOG depuis le FTP
et les stocker en base de données PostgreSQL.

Ce script est conçu pour être exécuté par cron de manière périodique.
"""

import sys
import os
import logging
from datetime import datetime

# Ajouter le répertoire courant au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ftp_log_service import FTPLogService

# Configuration du logging pour le script principal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/cron.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Fonction principale du script"""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"DÉBUT DU TRAITEMENT DES LOGS FTP - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Créer une instance du service
        service = FTPLogService()
        
        # Traiter tous les fichiers LOG
        # delete_after_processing=True pour supprimer les fichiers après traitement
        service.process_all_logs(delete_after_processing=True)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info(f"TRAITEMENT TERMINÉ AVEC SUCCÈS - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Durée totale: {duration}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.error("=" * 60)
        logger.error(f"ERREUR LORS DU TRAITEMENT - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error(f"Durée avant erreur: {duration}")
        logger.error(f"Erreur: {str(e)}")
        logger.error("=" * 60)
        
        # Importer traceback pour plus de détails sur l'erreur
        import traceback
        logger.error("Détails de l'erreur:")
        logger.error(traceback.format_exc())
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
