#!/usr/bin/env python3
"""
Script de test pour vérifier que le service FTPLogService fonctionne correctement.

Ce script teste toutes les fonctionnalités principales:
- Connexion à la base de données
- Connexion au serveur FTP
- Exploration des dossiers
- Traitement d'un fichier
- Processus complet

Utilisation: python test_service.py
"""

import os
import sys
import logging
from datetime import datetime

# Ajouter le répertoire courant au path pour pouvoir importer notre service
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ftp_log_service import FTPLogService

# Configuration du système de logs pour voir ce qui se passe pendant les tests
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """
    Test pour vérifier que la connexion à la base de données fonctionne.
    
    Returns:
        bool: True si le test réussit, False sinon
    """
    logger.info("🔍 Test de connexion à la base de données...")
    
    # Créer une instance du service
    service = FTPLogService()
    
    try:
        # Essayer de se connecter à la base de données
        success = service.connect_db()
        
        if success:
            logger.info("✅ Connexion à la base de données réussie")
            # Fermer proprement les connexions
            service.close_connections()
            return True
        else:
            logger.error("❌ Échec de la connexion à la base de données")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de la connexion à la base de données: {e}")
        return False


def test_ftp_connection():
    """
    Test pour vérifier que la connexion au serveur FTP fonctionne
    et qu'on peut récupérer les dossiers et fichiers.
    
    Returns:
        bool: True si le test réussit, False sinon
    """
    logger.info("🔍 Test de connexion au serveur FTP...")
    
    # Créer une instance du service
    service = FTPLogService()
    
    try:
        # Essayer de se connecter au FTP
        success = service.connect_ftp()
        if not success:
            logger.error("❌ Échec de la connexion FTP")
            return False
        
        # Tester la récupération des dossiers de centres d'usinage
        directories = service.get_cu_directories_from_ftp(service.ftp)
        logger.info(f"✅ Connexion FTP réussie, {len(directories)} dossiers CU trouvés: {directories}")
        
        # Tester la récupération des fichiers LOG dans chaque dossier
        total_files = 0
        for directory in directories:
            files = service.get_log_files_from_directory(service.ftp, directory)
            total_files += len(files)
            logger.info(f"  📁 {directory}: {len(files)} fichiers LOG")
        
        logger.info(f"📊 Total: {total_files} fichiers LOG trouvés dans tous les dossiers")
        
        # Fermer la connexion FTP
        service.ftp.quit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de connexion FTP: {e}")
        return False


def test_directory_exploration():
    """
    Test spécifique pour explorer en détail les dossiers du FTP
    et vérifier qu'on peut accéder aux fichiers.
    
    Returns:
        bool: True si le test réussit, False sinon
    """
    logger.info("🔍 Test de l'exploration détaillée des dossiers...")
    
    # Créer une instance du service
    service = FTPLogService()
    
    try:
        # Se connecter au FTP
        success = service.connect_ftp()
        if not success:
            logger.error("❌ Échec de la connexion FTP")
            return False
        
        # Lister tous les éléments à la racine du FTP
        all_items = service.ftp.nlst()
        logger.info(f"📂 Éléments à la racine FTP: {all_items}")
        
        # Vérifier chaque dossier de centre d'usinage configuré
        for directory_name, cu_type in service.cu_directories.items():
            if directory_name in all_items:
                logger.info(f"✅ Dossier {directory_name} ({cu_type}) trouvé")
                
                # Tester l'accès au dossier et compter les fichiers
                try:
                    files = service.get_log_files_from_directory(service.ftp, directory_name)
                    logger.info(f"  📄 {len(files)} fichiers LOG dans {directory_name}")
                    
                    # Afficher quelques exemples de fichiers
                    if files:
                        examples = files[:3]  # Prendre les 3 premiers
                        logger.info(f"  📋 Exemples: {examples}...")
                        
                except Exception as e:
                    logger.error(f"  ❌ Erreur accès à {directory_name}: {e}")
            else:
                logger.warning(f"❌ Dossier {directory_name} ({cu_type}) non trouvé")
        
        # Fermer la connexion FTP
        service.ftp.quit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exploration des dossiers: {e}")
        return False


def test_single_file_processing():
    """
    Test pour traiter un seul fichier LOG du début à la fin
    (sans le supprimer du FTP pour ne pas perturber les autres tests).
    
    Returns:
        bool: True si le test réussit, False sinon
    """
    logger.info("🔍 Test du traitement d'un fichier LOG complet...")
    
    # Créer une instance du service
    service = FTPLogService()
    
    try:
        # Se connecter à la base de données et au FTP
        if not service.connect_db():
            logger.error("❌ Échec de la connexion à la base de données")
            return False
            
        success = service.connect_ftp()
        if not success:
            logger.error("❌ Échec de la connexion FTP")
            return False
        
        # Chercher un fichier à traiter dans les dossiers disponibles
        directories = service.get_cu_directories_from_ftp(service.ftp)
        
        for directory in directories:
            files = service.get_log_files_from_directory(service.ftp, directory)
            
            if files:
                # Prendre le premier fichier trouvé
                filename = files[0]
                cu_type = service.cu_directories[directory]
                
                logger.info(f"📄 Test avec {directory}/{filename} (Type: {cu_type})")
                
                # === ÉTAPE 1: TÉLÉCHARGER LE FICHIER ===
                log_content = service.download_log_file_from_directory(service.ftp, directory, filename)
                if not log_content:
                    logger.error("❌ Échec du téléchargement")
                    continue
                
                logger.info(f"✅ Fichier téléchargé: {len(log_content)} caractères")
                
                # === ÉTAPE 2: ANALYSER LE CONTENU ===
                data = service.parse_log_content(log_content, filename)
                if not data:
                    logger.error("❌ Échec de l'analyse du contenu")
                    continue
                
                logger.info(f"✅ Contenu analysé: {len(data)} événements trouvés")
                
                # === ÉTAPE 3: CALCULER LES PERFORMANCES ===
                results = service.analyze_machine_performance(data, filename, cu_type)
                if not results:
                    logger.error("❌ Échec du calcul des performances")
                    continue
                
                logger.info(f"✅ Performances calculées: {results['TotalPieces']} pièces, {results['TauxOccupation']:.1f}% occupation")
                
                # === ÉTAPE 4: TEST DE SAUVEGARDE (SANS COMMIT) ===
                try:
                    # Sauvegarder en base de données
                    service.save_to_database(results, cu_type, filename, directory)
                    
                    # Annuler la transaction pour ne pas polluer la base de données
                    service.conn.rollback()
                    logger.info("✅ Test de sauvegarde réussi (transaction annulée)")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur lors du test de sauvegarde: {e}")
                    service.conn.rollback()
                
                # Fermer les connexions
                service.ftp.quit()
                service.close_connections()
                return True
        
        # Si on arrive ici, aucun fichier n'a été trouvé
        logger.warning("⚠️ Aucun fichier LOG trouvé pour le test")
        service.ftp.quit()
        service.close_connections()
        return False
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de traitement de fichier: {e}")
        return False


def test_full_process():
    """
    Test du processus complet de traitement de tous les logs
    (sans supprimer les fichiers du FTP pour ne pas les perdre).
    
    Returns:
        bool: True si le test réussit, False sinon
    """
    logger.info("🔍 Test du processus complet de traitement...")
    
    # Créer une instance du service
    service = FTPLogService()
    
    try:
        # Lancer le processus complet SANS supprimer les fichiers
        # (delete_after_processing=False pour les tests)
        success = service.process_all_logs(delete_after_processing=False)
        
        if success:
            logger.info("✅ Processus complet réussi")
            return True
        else:
            logger.error("❌ Le processus complet a rencontré des erreurs")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur inattendue dans le processus complet: {e}")
        # Afficher plus de détails sur l'erreur
        import traceback
        logger.error("Détails de l'erreur:")
        logger.error(traceback.format_exc())
        return False


def main():
    """
    Fonction principale qui exécute tous les tests dans l'ordre
    et affiche un résumé des résultats.
    """
    logger.info("=" * 80)
    logger.info("🚀 DÉBUT DES TESTS DU SERVICE FTP LOG")
    logger.info("=" * 80)
    
    # Liste de tous les tests à exécuter
    # Chaque test est un tuple (nom_du_test, fonction_de_test)
    tests = [
        ("Connexion Base de Données", test_database_connection),
        ("Connexion FTP", test_ftp_connection),
        ("Exploration Dossiers", test_directory_exploration),
        ("Traitement Fichier Unique", test_single_file_processing),
        ("Processus Complet", test_full_process)
    ]
    
    # Liste pour stocker les résultats de chaque test
    results = []
    
    # Exécuter chaque test
    for test_name, test_func in tests:
        logger.info(f"\n--- 🧪 Test: {test_name} ---")
        
        try:
            # Exécuter le test et stocker le résultat
            result = test_func()
            results.append((test_name, result))
            
            # Afficher le résultat immédiatement
            if result:
                logger.info(f"✅ {test_name}: RÉUSSI")
            else:
                logger.error(f"❌ {test_name}: ÉCHEC")
                
        except Exception as e:
            logger.error(f"💥 Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))
    
    # === AFFICHAGE DU RÉSUMÉ FINAL ===
    logger.info("\n" + "=" * 80)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("=" * 80)
    
    # Compter les succès et échecs
    all_passed = True
    passed_count = 0
    failed_count = 0
    
    for test_name, result in results:
        if result:
            status = "✅ RÉUSSI"
            passed_count += 1
        else:
            status = "❌ ÉCHEC"
            failed_count += 1
            all_passed = False
        
        logger.info(f"{test_name:.<40} {status}")
    
    # Affichage du résultat global
    logger.info("=" * 80)
    logger.info(f"📈 Tests réussis: {passed_count}")
    logger.info(f"❌ Tests échoués: {failed_count}")
    
    if all_passed:
        logger.info("🎉 TOUS LES TESTS ONT RÉUSSI!")
        return 0  # Code de sortie 0 = succès
    else:
        logger.error("💥 CERTAINS TESTS ONT ÉCHOUÉ!")
        return 1  # Code de sortie 1 = échec


# Point d'entrée du script
if __name__ == "__main__":
    # Exécuter les tests et utiliser le code de sortie pour indiquer le résultat
    exit_code = main()
    sys.exit(exit_code) 