#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement du service FTPLogService
"""

import os
import sys
import logging
from datetime import datetime

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ftp_log_service import FTPLogService

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test de connexion à la base de données"""
    logger.info("Test de connexion à la base de données...")
    
    service = FTPLogService()
    try:
        service.connect_db()
        logger.info("✅ Connexion à la base de données réussie")
        service.close_connections()
        return True
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à la base de données: {e}")
        return False


def test_ftp_connection():
    """Test de connexion au FTP"""
    logger.info("Test de connexion au FTP...")
    
    service = FTPLogService()
    try:
        success = service.connect_ftp()
        if not success:
            logger.error("❌ Échec de la connexion FTP")
            return False
        
        # Tester la récupération des dossiers CU
        directories = service.get_cu_directories_from_ftp(service.ftp)
        logger.info(f"✅ Connexion FTP réussie, {len(directories)} dossiers CU trouvés: {directories}")
        
        # Tester la récupération des fichiers LOG dans chaque dossier
        total_files = 0
        for directory in directories:
            files = service.get_log_files_from_directory(service.ftp, directory)
            total_files += len(files)
            logger.info(f"  - {directory}: {len(files)} fichiers LOG")
        
        logger.info(f"Total: {total_files} fichiers LOG trouvés dans tous les dossiers")
        
        service.ftp.quit()
        return True
    except Exception as e:
        logger.error(f"❌ Erreur de connexion FTP: {e}")
        return False


def test_directory_exploration():
    """Test spécifique de l'exploration des dossiers"""
    logger.info("Test de l'exploration des dossiers...")
    
    service = FTPLogService()
    try:
        success = service.connect_ftp()
        if not success:
            logger.error("❌ Échec de la connexion FTP")
            return False
        
        # Lister tous les éléments à la racine
        all_items = service.ftp.nlst()
        logger.info(f"Éléments à la racine FTP: {all_items}")
        
        # Vérifier les dossiers CU configurés
        for directory_name, cu_type in service.cu_directories.items():
            if directory_name in all_items:
                logger.info(f"✅ Dossier {directory_name} ({cu_type}) trouvé")
                
                # Tester l'accès au dossier
                try:
                    files = service.get_log_files_from_directory(service.ftp, directory_name)
                    logger.info(f"  - {len(files)} fichiers LOG dans {directory_name}")
                    if files:
                        logger.info(f"  - Exemples: {files[:3]}...")
                except Exception as e:
                    logger.error(f"  - Erreur accès à {directory_name}: {e}")
            else:
                logger.warning(f"❌ Dossier {directory_name} ({cu_type}) non trouvé")
        
        service.ftp.quit()
        return True
    except Exception as e:
        logger.error(f"❌ Erreur exploration dossiers: {e}")
        return False


def test_single_file_processing():
    """Test du traitement d'un seul fichier (sans suppression)"""
    logger.info("Test du traitement d'un fichier...")
    
    service = FTPLogService()
    try:
        service.connect_db()
        success = service.connect_ftp()
        if not success:
            logger.error("❌ Échec de la connexion FTP")
            return False
        
        # Chercher un fichier à traiter
        directories = service.get_cu_directories_from_ftp(service.ftp)
        
        for directory in directories:
            files = service.get_log_files_from_directory(service.ftp, directory)
            if files:
                # Prendre le premier fichier
                filename = files[0]
                cu_type = service.cu_directories[directory]
                
                logger.info(f"Test avec {directory}/{filename} (Type: {cu_type})")
                
                # Télécharger et parser
                log_content = service.download_log_file_from_directory(service.ftp, directory, filename)
                if log_content:
                    data = service.parse_log_content(log_content, filename)
                    if data:
                        results = service.analyze_machine_performance(data, filename, cu_type)
                        if results:
                            logger.info(f"✅ Analyse réussie: {results['TotalPieces']} pièces, {results['TauxOccupation']:.1f}% occupation")
                            
                            # Test de sauvegarde (sans commit pour ne pas polluer)
                            try:
                                service.save_to_database(results, cu_type, filename, directory)
                                service.conn.rollback()  # Annuler pour ne pas sauvegarder vraiment
                                logger.info("✅ Test de sauvegarde réussi")
                            except Exception as e:
                                logger.error(f"❌ Erreur test sauvegarde: {e}")
                                service.conn.rollback()
                            
                            service.ftp.quit()
                            service.close_connections()
                            return True
                
                break
        
        logger.warning("Aucun fichier trouvé pour le test")
        service.ftp.quit()
        service.close_connections()
        return False
        
    except Exception as e:
        logger.error(f"❌ Erreur test fichier: {e}")
        return False


def test_full_process():
    """Test du processus complet (sans suppression des fichiers)"""
    logger.info("Test du processus complet...")
    
    service = FTPLogService()
    try:
        # Traiter sans supprimer les fichiers pour le test
        service.process_all_logs(delete_after_processing=False)
        logger.info("✅ Processus complet réussi")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur dans le processus complet: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Fonction principale de test"""
    logger.info("=" * 60)
    logger.info("DÉBUT DES TESTS DU SERVICE FTP LOG (STRUCTURE DOSSIERS)")
    logger.info("=" * 60)
    
    tests = [
        ("Connexion Base de Données", test_database_connection),
        ("Connexion FTP", test_ftp_connection),
        ("Exploration Dossiers", test_directory_exploration),
        ("Traitement Fichier Unique", test_single_file_processing),
        ("Processus Complet", test_full_process)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Test: {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    logger.info("\n" + "=" * 60)
    logger.info("RÉSUMÉ DES TESTS")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 TOUS LES TESTS ONT RÉUSSI!")
        return 0
    else:
        logger.error("💥 CERTAINS TESTS ONT ÉCHOUÉ!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 