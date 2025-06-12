#!/usr/bin/env python3
"""
Service pour traiter les fichiers LOG depuis un serveur FTP
et les sauvegarder dans une base de données PostgreSQL.

Ce service fait les choses suivantes:
1. Se connecte au serveur FTP
2. Télécharge les fichiers LOG depuis différents dossiers
3. Analyse le contenu des fichiers LOG
4. Sauvegarde les données dans PostgreSQL
5. Supprime les fichiers traités du FTP
"""

import os
import re
import ftplib
from datetime import datetime, timedelta
import psycopg2
from decimal import Decimal
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du système de logs pour voir ce qui se passe
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FTPLogService:
    """
    Classe principale qui gère tout le processus de traitement des logs FTP.
    
    Cette classe fait le lien entre:
    - Le serveur FTP (où sont stockés les fichiers LOG)
    - La base de données PostgreSQL (où on sauvegarde les données)
    """
    
    def __init__(self):
        """
        Initialise le service avec toutes les configurations nécessaires.
        Les valeurs par défaut peuvent être surchargées par des variables d'environnement.
        """
        # Configuration pour se connecter au serveur FTP
        self.ftp_host = os.getenv('FTP_HOST')
        self.ftp_user = os.getenv('FTP_USER')
        self.ftp_pass = os.getenv('FTP_PASS')
        
        # Configuration pour se connecter à la base de données
        self.db_host = os.getenv('POSTGRES_HOST')
        self.db_name = os.getenv('POSTGRES_DB')
        self.db_user = os.getenv('POSTGRES_USER')
        self.db_pass = os.getenv('POSTGRES_PASSWORD')
        
        # Dictionnaire qui fait le lien entre les noms de dossiers FTP et les types de machines
        # Clé = nom du dossier sur le FTP, Valeur = type de machine
        self.cu_directories = {
            'DEM12 (PVC)': 'DEM12',
            'DEMALU (ALU)': 'DEMALU', 
            'SU12 (HYBRIDE)': 'SU12'
        }
        
        # Variables pour stocker les connexions (initialisées à None)
        self.conn = None  # Connexion à la base de données
        self.cur = None   # Curseur pour exécuter les requêtes SQL
        self.ftp = None   # Connexion au serveur FTP

    def connect_db(self):
        """
        Se connecte à la base de données PostgreSQL.
        
        Returns:
            bool: True si la connexion réussit, False sinon
        """
        try:
            logger.info("Tentative de connexion à la base de données...")
            
            # Créer la connexion avec les paramètres configurés
            self.conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_pass
            )
            
            # Créer un curseur pour exécuter les requêtes
            self.cur = self.conn.cursor()
            
            logger.info("✅ Connexion à la base de données réussie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la connexion à la base de données: {e}")
            return False

    def create_tables(self):
        """
        Crée toutes les tables nécessaires dans la base de données si elles n'existent pas déjà.
        
        Structure des tables:
        - centre_usinage: informations sur chaque machine
        - session_production: données de production pour chaque jour
        - job_profil: détails des profils de jobs
        - periode_attente: périodes où la machine attend
        - periode_arret: périodes où la machine est arrêtée
        - piece_production: détails de chaque pièce produite
        
        Returns:
            bool: True si toutes les tables sont créées, False sinon
        """
        try:
            logger.info("Création des tables de la base de données...")
            
            # Table pour stocker les informations sur chaque centre d'usinage (machine)
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS centre_usinage (
                    id SERIAL PRIMARY KEY,
                    nom VARCHAR(100) UNIQUE NOT NULL,
                    type_cu VARCHAR(50) NOT NULL,
                    description TEXT,
                    actif BOOLEAN DEFAULT TRUE,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Table pour stocker les données de production de chaque jour
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS session_production (
                    id SERIAL PRIMARY KEY,
                    centre_usinage_id INTEGER REFERENCES centre_usinage(id),
                    date_production DATE NOT NULL,
                    heure_premiere_piece TIMESTAMP,
                    heure_derniere_piece TIMESTAMP,
                    heure_premier_machine_start TIMESTAMP,
                    heure_dernier_machine_stop TIMESTAMP,
                    total_pieces INTEGER DEFAULT 0,
                    duree_production_totale DECIMAL(10,4),
                    temps_attente DECIMAL(10,4),
                    temps_arret_volontaire DECIMAL(10,4),
                    temps_production_effectif DECIMAL(10,4),
                    taux_occupation DECIMAL(5,2),
                    taux_attente DECIMAL(5,2),
                    taux_arret_volontaire DECIMAL(5,2),
                    fichier_log_source VARCHAR(255),
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(centre_usinage_id, date_production)
                );
            """)
            
            # Table pour stocker les profils de jobs
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS job_profil (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES session_production(id),
                    reference VARCHAR(50) NOT NULL,
                    longueur DECIMAL(10,2),
                    couleur VARCHAR(50),
                    timestamp_debut TIMESTAMP,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Table pour stocker les périodes d'attente
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS periode_attente (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES session_production(id),
                    timestamp_debut TIMESTAMP NOT NULL,
                    timestamp_fin TIMESTAMP NOT NULL,
                    duree_secondes INTEGER NOT NULL,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Table pour stocker les périodes d'arrêt
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS periode_arret (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES session_production(id),
                    timestamp_debut TIMESTAMP NOT NULL,
                    timestamp_fin TIMESTAMP NOT NULL,
                    duree_secondes INTEGER NOT NULL,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Table pour stocker chaque pièce produite
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS piece_production (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES session_production(id),
                    numero_piece INTEGER NOT NULL,
                    timestamp_production TIMESTAMP NOT NULL,
                    details TEXT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Sauvegarder toutes les modifications
            self.conn.commit()
            logger.info("✅ Toutes les tables ont été créées avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création des tables: {e}")
            return False

    def connect_ftp(self):
        """
        Se connecte au serveur FTP.
        
        Returns:
            bool: True si la connexion réussit, False sinon
        """
        try:
            logger.info("Tentative de connexion au serveur FTP...")
            
            # Créer la connexion FTP
            self.ftp = ftplib.FTP(self.ftp_host)
            
            # Se connecter avec les identifiants
            self.ftp.login(self.ftp_user, self.ftp_pass)
            
            logger.info("✅ Connexion FTP réussie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la connexion FTP: {e}")
            self.ftp = None
            return False

    def get_cu_directories_from_ftp(self, ftp):
        """
        Récupère la liste des dossiers de centres d'usinage disponibles sur le FTP.
        
        Args:
            ftp: Connexion FTP active
            
        Returns:
            list: Liste des noms de dossiers trouvés
        """
        try:
            if not ftp:
                logger.error("❌ Pas de connexion FTP active")
                return []
            
            logger.info("Recherche des dossiers de centres d'usinage...")
            
            # Récupérer tous les dossiers à la racine du FTP
            all_dirs = ftp.nlst()
            cu_dirs = []
            
            # Vérifier quels dossiers correspondent à nos centres d'usinage configurés
            for directory in all_dirs:
                if directory in self.cu_directories:
                    cu_dirs.append(directory)
                    cu_type = self.cu_directories[directory]
                    logger.info(f"✅ Dossier trouvé: {directory} -> Type: {cu_type}")
            
            # Afficher un avertissement si aucun dossier n'est trouvé
            if not cu_dirs:
                logger.warning("⚠️ Aucun dossier de centre d'usinage trouvé")
                logger.info(f"Dossiers disponibles sur le FTP: {all_dirs}")
                logger.info(f"Dossiers attendus: {list(self.cu_directories.keys())}")
            
            return cu_dirs
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des dossiers: {e}")
            return []

    def get_log_files_from_directory(self, ftp, directory):
        """
        Récupère la liste des fichiers LOG dans un dossier spécifique.
        
        Args:
            ftp: Connexion FTP active
            directory: Nom du dossier à explorer
            
        Returns:
            list: Liste des noms de fichiers LOG trouvés
        """
        try:
            logger.info(f"Recherche des fichiers LOG dans le dossier: {directory}")
            
            # S'assurer qu'on est à la racine du FTP
            ftp.cwd('/')
            
            # Naviguer dans le dossier spécifique
            ftp.cwd(directory)
            
            # Récupérer tous les fichiers du dossier
            files = ftp.nlst()
            
            # Filtrer pour ne garder que les fichiers qui se terminent par .LOG
            log_files = [f for f in files if f.endswith('.LOG')]
            
            # Revenir à la racine pour éviter les problèmes
            ftp.cwd('/')
            
            logger.info(f"✅ Trouvé {len(log_files)} fichiers LOG dans {directory}")
            return log_files
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des fichiers de {directory}: {e}")
            # En cas d'erreur, toujours essayer de revenir à la racine
            try:
                ftp.cwd('/')
            except:
                pass
            return []

    def download_log_file_from_directory(self, ftp, directory, filename):
        """
        Télécharge un fichier LOG depuis un dossier spécifique du FTP.
        
        Args:
            ftp: Connexion FTP active
            directory: Nom du dossier contenant le fichier
            filename: Nom du fichier à télécharger
            
        Returns:
            str: Contenu du fichier LOG ou None si erreur
        """
        try:
            logger.info(f"Téléchargement du fichier: {directory}/{filename}")
            
            # S'assurer qu'on est à la racine du FTP
            ftp.cwd('/')
            
            # Naviguer dans le dossier contenant le fichier
            ftp.cwd(directory)
            
            # Préparer un conteneur pour recevoir les données du fichier
            log_content_bytes = bytearray()
            
            def handle_binary(data):
                """Fonction appelée pour chaque bloc de données reçu"""
                log_content_bytes.extend(data)
            
            # Télécharger le fichier en mode binaire pour éviter les problèmes d'encodage
            ftp.retrbinary(f'RETR {filename}', handle_binary)
            
            # Convertir les bytes en texte (utiliser latin-1 qui accepte tous les caractères)
            log_content = log_content_bytes.decode('latin-1')
            
            # Revenir à la racine
            ftp.cwd('/')
            
            logger.info(f"✅ Fichier téléchargé: {len(log_content)} caractères")
            return log_content
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du téléchargement de {directory}/{filename}: {e}")
            # En cas d'erreur, toujours essayer de revenir à la racine
            try:
                ftp.cwd('/')
            except:
                pass
            return None

    def delete_log_file_from_directory(self, ftp, directory, filename):
        """
        Supprime un fichier LOG d'un dossier spécifique du FTP.
        
        Args:
            ftp: Connexion FTP active
            directory: Nom du dossier contenant le fichier
            filename: Nom du fichier à supprimer
            
        Returns:
            bool: True si la suppression réussit, False sinon
        """
        try:
            logger.info(f"Suppression du fichier: {directory}/{filename}")
            
            # S'assurer qu'on est à la racine du FTP
            ftp.cwd('/')
            
            # Naviguer dans le dossier contenant le fichier
            ftp.cwd(directory)
            
            # Supprimer le fichier
            ftp.delete(filename)
            
            # Revenir à la racine
            ftp.cwd('/')
            
            logger.info(f"✅ Fichier supprimé du FTP: {directory}/{filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression de {directory}/{filename}: {e}")
            # En cas d'erreur, toujours essayer de revenir à la racine
            try:
                ftp.cwd('/')
            except:
                pass
            return False

    def parse_log_content(self, log_content, filename):
        """
        Analyse le contenu d'un fichier LOG et extrait les événements.
        
        Format attendu des lignes: YYYYMMDD HH:MM:SS|@EventType: Details
        
        Args:
            log_content: Contenu du fichier LOG sous forme de texte
            filename: Nom du fichier (pour les messages de log)
            
        Returns:
            list: Liste de dictionnaires contenant les événements parsés
        """
        try:
            logger.info(f"Analyse du contenu du fichier: {filename}")
            
            # Nettoyer le contenu si c'est des bytes
            if isinstance(log_content, bytes):
                log_content = log_content.decode('latin-1')
            
            # Supprimer les caractères problématiques
            log_content = log_content.replace('\x00', '')  # Supprimer les caractères null
            
            # Diviser le contenu en lignes
            lines = log_content.strip().split('\n')
            data = []
            
            # Analyser chaque ligne
            for line in lines:
                line = line.strip()
                
                # Ignorer les lignes vides ou qui ne contiennent pas le séparateur
                if not line or '|@' not in line:
                    continue
                
                try:
                    # Diviser la ligne en timestamp et événement
                    timestamp_str, event_part = line.split('|@', 1)
                    
                    # Nettoyer le timestamp
                    timestamp_str = timestamp_str.strip()
                    # Garder seulement les caractères ASCII pour le timestamp
                    timestamp_str = ''.join(c for c in timestamp_str if ord(c) < 128)
                    
                    # Convertir le timestamp en objet datetime
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d %H:%M:%S')
                    
                    # Analyser la partie événement
                    if ':' in event_part:
                        event_type, details = event_part.split(':', 1)
                        event_type = event_type.strip()
                        details = details.strip()
                    else:
                        event_type = event_part.strip()
                        details = ""
                    
                    # Ajouter l'événement à notre liste
                    data.append({
                        "Timestamp": timestamp,
                        "Event": event_type,
                        "Details": details
                    })
                    
                except Exception as e:
                    # Ignorer les lignes qui ne peuvent pas être parsées
                    continue
            
            if not data:
                logger.warning(f"⚠️ Aucune donnée trouvée dans {filename}")
                return []
                
            logger.info(f"✅ Fichier {filename} analysé: {len(data)} événements trouvés")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse de {filename}: {e}")
            return []

    def analyze_machine_performance(self, data, log_file_name, cu_type):
        """
        Analyse les performances d'une machine à partir des événements du log.
        
        Cette fonction calcule:
        - Le nombre de pièces produites
        - Les temps de production, d'attente et d'arrêt
        - Les taux d'occupation
        - Les détails des jobs et périodes
        
        Args:
            data: Liste des événements parsés
            log_file_name: Nom du fichier LOG
            cu_type: Type de centre d'usinage (PVC, ALU, HYBRIDE)
            
        Returns:
            dict: Dictionnaire contenant toutes les métriques calculées
        """
        if not data:
            logger.warning("Aucune donnée à analyser")
            return None
        
        logger.info(f"Analyse des performances pour {log_file_name} (Type: {cu_type})")
        
        # Extraire la date du premier événement
        log_date = data[0]["Timestamp"].date()
        
        # Créer un identifiant unique pour ce centre d'usinage
        cu_id = f"{cu_type}_{os.path.splitext(log_file_name)[0]}"
        
        # === ANALYSE DES PIÈCES PRODUITES ===
        # Chercher tous les événements "StukUitgevoerd" (pièce terminée)
        stuk_events = [event for event in data if event["Event"] == "StukUitgevoerd"]
        
        # Calculer les temps de première et dernière pièce
        first_piece_time = stuk_events[0]["Timestamp"] if stuk_events else None
        last_piece_time = stuk_events[-1]["Timestamp"] if stuk_events else None
        total_pieces = len(stuk_events)
        
        # Calculer la durée totale de production
        production_duration = None
        if first_piece_time and last_piece_time:
            production_duration = (last_piece_time - first_piece_time).total_seconds() / 3600  # en heures
        
        # === ANALYSE DES TEMPS D'ATTENTE ===
        # Chercher tous les événements "MachineWait"
        wait_events = [event for event in data if event["Event"] == "MachineWait"]
        
        total_wait_time = 0  # en secondes
        wait_periods = []
        
        # Analyser chaque période d'attente
        for event in wait_events:
            try:
                # Chercher la durée dans les détails (format: "X sec" ou "X.X")
                wait_matches = re.findall(r"(\d+) sec", str(event["Details"]))
                wait_duration = 0
                
                if wait_matches:
                    wait_duration = float(wait_matches[0])
                else:
                    # Chercher un nombre décimal
                    decimal_matches = re.findall(r"(\d+\.\d+)", str(event["Details"]))
                    if decimal_matches:
                        wait_duration = float(decimal_matches[0])
                
                if wait_duration > 0:
                    wait_start = event["Timestamp"]
                    wait_end = wait_start + timedelta(seconds=wait_duration)
                    wait_periods.append({
                        "Start": wait_start,
                        "End": wait_end,
                        "Duration": wait_duration
                    })
                    total_wait_time += wait_duration
                    
            except Exception as e:
                # Ignorer les événements qui ne peuvent pas être analysés
                continue
        
        total_wait_hours = total_wait_time / 3600  # convertir en heures
        
        # === ANALYSE DES ARRÊTS VOLONTAIRES ===
        # Chercher les événements de démarrage et d'arrêt de machine
        stop_events = [event for event in data if event["Event"] in ["MachineStop", "MachineStart"]]
        
        # Trouver le dernier arrêt et le premier démarrage
        machine_stop_events = [event for event in data if event["Event"] == "MachineStop"]
        last_machine_stop = machine_stop_events[-1]["Timestamp"] if machine_stop_events else None
        
        machine_start_events = [event for event in data if event["Event"] == "MachineStart"]
        first_machine_start = machine_start_events[0]["Timestamp"] if machine_start_events else None
        
        total_stop_time = 0  # en secondes
        stop_periods = []
        
        # Calculer les périodes d'arrêt (entre MachineStop et MachineStart)
        if stop_events:
            for i in range(len(stop_events) - 1):
                if (stop_events[i]["Event"] == "MachineStop" and 
                    stop_events[i + 1]["Event"] == "MachineStart"):
                    
                    stop_start = stop_events[i]["Timestamp"]
                    stop_end = stop_events[i + 1]["Timestamp"]
                    stop_duration = (stop_end - stop_start).total_seconds()
                    
                    stop_periods.append({
                        "Start": stop_start,
                        "End": stop_end,
                        "Duration": stop_duration
                    })
                    total_stop_time += stop_duration
        
        total_stop_hours = total_stop_time / 3600  # convertir en heures
        
        # === ANALYSE DES PROFILS DE JOBS ===
        # Chercher tous les événements "JobProfiel"
        job_events = [event for event in data if event["Event"] == "JobProfiel"]
        
        job_details = []
        for event in job_events:
            try:
                job = event["Details"]
                # Extraire les informations avec des expressions régulières
                ref_match = re.search(r"R:(\w+)", job)      # Référence
                length_match = re.search(r"L:(\d+\.\d+)", job)  # Longueur
                color_match = re.search(r"C:(\w+)", job)    # Couleur
                
                if ref_match and length_match:
                    ref = ref_match.group(1)
                    length = float(length_match.group(1))
                    color = color_match.group(1) if color_match else "N/A"
                    timestamp = event["Timestamp"]
                    
                    job_details.append({
                        "Reference": ref,
                        "Length": length,
                        "Color": color,
                        "Timestamp": timestamp
                    })
            except:
                # Ignorer les jobs qui ne peuvent pas être analysés
                continue
        
        # === COLLECTE DES DÉTAILS DES PIÈCES ===
        piece_events = []
        for i, event in enumerate(stuk_events):
            piece_events.append({
                "Timestamp": event["Timestamp"],
                "Piece": event["Details"]
            })
        
        # === CALCUL DES INDICATEURS DE PERFORMANCE ===
        if production_duration and production_duration > 0:
            # Temps de production effectif = temps total - attentes - arrêts
            effective_production_time = production_duration - total_wait_hours - total_stop_hours
            total_available_time = production_duration
            
            # Calculer les pourcentages
            occupation_rate = (effective_production_time / total_available_time) * 100
            wait_rate = (total_wait_hours / total_available_time) * 100
            stop_rate = (total_stop_hours / total_available_time) * 100
        else:
            effective_production_time = 0
            occupation_rate = 0
            wait_rate = 0
            stop_rate = 0
        
        # === RETOURNER TOUS LES RÉSULTATS ===
        results = {
            "CU_ID": cu_id,
            "Date": log_date,
            "PremierePiece": first_piece_time,
            "DernierePiece": last_piece_time,
            "PremierMachineStart": first_machine_start,
            "DernierMachineStop": last_machine_stop,
            "TotalPieces": total_pieces,
            "DureeProduction": production_duration,
            "TempsAttente": total_wait_hours,
            "TempsArretVolontaire": total_stop_hours,
            "TempsProductionEffectif": effective_production_time,
            "TauxOccupation": occupation_rate,
            "TauxAttente": wait_rate,
            "TauxArretVolontaire": stop_rate,
            "JobDetails": job_details,
            "WaitPeriods": wait_periods,
            "StopPeriods": stop_periods,
            "PieceEvents": piece_events
        }
        
        logger.info(f"✅ Analyse terminée: {total_pieces} pièces, {occupation_rate:.1f}% d'occupation")
        return results

    def save_to_database(self, results, cu_type, log_file_name, directory):
        """
        Sauvegarde tous les résultats d'analyse dans la base de données.
        
        Cette fonction:
        1. Crée ou met à jour le centre d'usinage
        2. Crée ou met à jour la session de production
        3. Sauvegarde tous les détails (jobs, périodes, pièces)
        
        Args:
            results: Dictionnaire contenant tous les résultats d'analyse
            cu_type: Type de centre d'usinage
            log_file_name: Nom du fichier LOG source
            directory: Nom du dossier FTP source
            
        Returns:
            bool: True si la sauvegarde réussit, False sinon
        """
        try:
            logger.info(f"Sauvegarde des données en base pour {cu_type}")
            
            # Créer un nom unique pour ce centre d'usinage
            cu_name = f"{cu_type}_{os.path.splitext(log_file_name)[0]}"
            
            # === ÉTAPE 1: CRÉER OU METTRE À JOUR LE CENTRE D'USINAGE ===
            # Approche alternative : vérifier s'il existe déjà, sinon l'insérer
            self.cur.execute("""
                SELECT id FROM centre_usinage WHERE nom = %s
            """, (cu_name,))
            
            centre_result = self.cur.fetchone()
            
            if centre_result:
                # Mettre à jour le centre existant
                centre_usinage_id = centre_result[0]
                self.cur.execute("""
                    UPDATE centre_usinage 
                    SET type_cu = %s, description = %s
                    WHERE id = %s
                """, (cu_type, f'Centre d\'usinage {cu_type} - {directory}', centre_usinage_id))
            else:
                # Créer un nouveau centre
                self.cur.execute("""
                    INSERT INTO centre_usinage (nom, type_cu, description, actif)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                """, (cu_name, cu_type, f'Centre d\'usinage {cu_type} - {directory}', True))
                centre_usinage_id = self.cur.fetchone()[0]
            
            # === ÉTAPE 2: CRÉER OU METTRE À JOUR LA SESSION DE PRODUCTION ===
            # Approche alternative : vérifier s'il existe déjà, sinon l'insérer
            self.cur.execute("""
                SELECT id FROM session_production 
                WHERE centre_usinage_id = %s AND date_production = %s
            """, (centre_usinage_id, results["Date"]))
            
            session_result = self.cur.fetchone()
            
            if session_result:
                # Mettre à jour la session existante
                session_id = session_result[0]
                self.cur.execute("""
                    UPDATE session_production SET
                        heure_premiere_piece = %s,
                        heure_derniere_piece = %s,
                        heure_premier_machine_start = %s,
                        heure_dernier_machine_stop = %s,
                        total_pieces = %s,
                        duree_production_totale = %s,
                        temps_attente = %s,
                        temps_arret_volontaire = %s,
                        temps_production_effectif = %s,
                        taux_occupation = %s,
                        taux_attente = %s,
                        taux_arret_volontaire = %s,
                        fichier_log_source = %s
                    WHERE id = %s
                """, (
                    results["PremierePiece"], 
                    results["DernierePiece"],
                    results["PremierMachineStart"], 
                    results["DernierMachineStop"], 
                    results["TotalPieces"],
                    Decimal(str(results["DureeProduction"] or 0)), 
                    Decimal(str(results["TempsAttente"] or 0)),
                    Decimal(str(results["TempsArretVolontaire"] or 0)), 
                    Decimal(str(results["TempsProductionEffectif"] or 0)),
                    Decimal(str(results["TauxOccupation"] or 0)), 
                    Decimal(str(results["TauxAttente"] or 0)),
                    Decimal(str(results["TauxArretVolontaire"] or 0)), 
                    f"{directory}/{log_file_name}",
                    session_id
                ))
            else:
                # Créer une nouvelle session
                self.cur.execute("""
                    INSERT INTO session_production (
                        centre_usinage_id, date_production, heure_premiere_piece, heure_derniere_piece,
                        heure_premier_machine_start, heure_dernier_machine_stop, total_pieces,
                        duree_production_totale, temps_attente, temps_arret_volontaire,
                        temps_production_effectif, taux_occupation, taux_attente,
                        taux_arret_volontaire, fichier_log_source
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    centre_usinage_id, 
                    results["Date"], 
                    results["PremierePiece"], 
                    results["DernierePiece"],
                    results["PremierMachineStart"], 
                    results["DernierMachineStop"], 
                    results["TotalPieces"],
                    Decimal(str(results["DureeProduction"] or 0)), 
                    Decimal(str(results["TempsAttente"] or 0)),
                    Decimal(str(results["TempsArretVolontaire"] or 0)), 
                    Decimal(str(results["TempsProductionEffectif"] or 0)),
                    Decimal(str(results["TauxOccupation"] or 0)), 
                    Decimal(str(results["TauxAttente"] or 0)),
                    Decimal(str(results["TauxArretVolontaire"] or 0)), 
                    f"{directory}/{log_file_name}"
                ))
                session_id = self.cur.fetchone()[0]
            
            # === ÉTAPE 3: SUPPRIMER LES ANCIENNES DONNÉES DÉTAILLÉES ===
            # (pour éviter les doublons si on retraite le même fichier)
            self.cur.execute("DELETE FROM job_profil WHERE session_id = %s", (session_id,))
            self.cur.execute("DELETE FROM periode_attente WHERE session_id = %s", (session_id,))
            self.cur.execute("DELETE FROM periode_arret WHERE session_id = %s", (session_id,))
            self.cur.execute("DELETE FROM piece_production WHERE session_id = %s", (session_id,))
            
            # === ÉTAPE 4: SAUVEGARDER LES PROFILS DE JOBS ===
            for job in results["JobDetails"]:
                self.cur.execute("""
                    INSERT INTO job_profil (session_id, reference, longueur, couleur, timestamp_debut)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session_id, job["Reference"], Decimal(str(job["Length"])), job["Color"], job["Timestamp"]))
            
            # === ÉTAPE 5: SAUVEGARDER LES PÉRIODES D'ATTENTE ===
            for wait in results["WaitPeriods"]:
                self.cur.execute("""
                    INSERT INTO periode_attente (session_id, timestamp_debut, timestamp_fin, duree_secondes)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, wait["Start"], wait["End"], int(wait["Duration"])))
            
            # === ÉTAPE 6: SAUVEGARDER LES PÉRIODES D'ARRÊT ===
            for stop in results["StopPeriods"]:
                self.cur.execute("""
                    INSERT INTO periode_arret (session_id, timestamp_debut, timestamp_fin, duree_secondes)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, stop["Start"], stop["End"], int(stop["Duration"])))
            
            # === ÉTAPE 7: SAUVEGARDER LES PIÈCES PRODUITES ===
            for i, piece in enumerate(results["PieceEvents"], 1):
                self.cur.execute("""
                    INSERT INTO piece_production (session_id, numero_piece, timestamp_production, details)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, i, piece["Timestamp"], piece["Piece"]))
            
            # === ÉTAPE 8: CONFIRMER TOUTES LES MODIFICATIONS ===
            self.conn.commit()
            logger.info(f"✅ Données sauvegardées avec succès pour {cu_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            # En cas d'erreur, annuler toutes les modifications
            self.conn.rollback()
            return False

    def process_all_logs(self, delete_after_processing=True):
        """
        Fonction principale qui traite tous les fichiers LOG du FTP.
        
        Cette fonction:
        1. Se connecte à la base de données et au FTP
        2. Crée les tables nécessaires
        3. Explore tous les dossiers de centres d'usinage
        4. Traite chaque fichier LOG trouvé
        5. Supprime les fichiers traités (optionnel)
        
        Args:
            delete_after_processing: Si True, supprime les fichiers du FTP après traitement
            
        Returns:
            bool: True si tout s'est bien passé, False s'il y a eu des erreurs
        """
        try:
            logger.info("🚀 DÉBUT DU TRAITEMENT DE TOUS LES LOGS FTP")
            
            # === ÉTAPE 1: ÉTABLIR LES CONNEXIONS ===
            if not self.connect_db():
                logger.error("❌ Impossible de se connecter à la base de données")
                return False
                
            if not self.connect_ftp():
                logger.error("❌ Impossible de se connecter au FTP")
                return False
            
            # === ÉTAPE 2: CRÉER LES TABLES ===
            if not self.create_tables():
                logger.error("❌ Impossible de créer les tables")
                return False
            
            # === ÉTAPE 3: RÉCUPÉRER LES DOSSIERS DE CENTRES D'USINAGE ===
            cu_directories = self.get_cu_directories_from_ftp(self.ftp)
            
            if not cu_directories:
                logger.error("❌ Aucun dossier de centre d'usinage trouvé")
                return False
            
            # Variables pour compter les résultats
            total_processed = 0
            total_errors = 0
            
            # === ÉTAPE 4: TRAITER CHAQUE DOSSIER ===
            for directory in cu_directories:
                cu_type = self.cu_directories[directory]
                logger.info(f"\n📁 === TRAITEMENT DU DOSSIER {directory} (Type: {cu_type}) ===")
                
                # Récupérer tous les fichiers LOG de ce dossier
                log_files = self.get_log_files_from_directory(self.ftp, directory)
                
                if not log_files:
                    logger.warning(f"⚠️ Aucun fichier LOG trouvé dans {directory}")
                    continue
                
                # Compteurs pour ce dossier
                processed_count = 0
                error_count = 0
                
                # === ÉTAPE 5: TRAITER CHAQUE FICHIER LOG ===
                for filename in log_files:
                    try:
                        logger.info(f"📄 Traitement de {directory}/{filename}...")
                        
                        # Télécharger le fichier depuis le FTP
                        log_content = self.download_log_file_from_directory(self.ftp, directory, filename)
                        if not log_content:
                            logger.error(f"❌ Échec du téléchargement de {filename}")
                            error_count += 1
                            continue
                        
                        # Analyser le contenu du fichier
                        data = self.parse_log_content(log_content, filename)
                        if not data:
                            logger.error(f"❌ Échec de l'analyse de {filename}")
                            error_count += 1
                            continue
                        
                        # Calculer les performances de la machine
                        results = self.analyze_machine_performance(data, filename, cu_type)
                        if not results:
                            logger.error(f"❌ Échec du calcul des performances pour {filename}")
                            error_count += 1
                            continue
                        
                        # Sauvegarder les résultats en base de données
                        if self.save_to_database(results, cu_type, filename, directory):
                            logger.info(f"✅ {directory}/{filename} traité avec succès")
                            
                            # Supprimer le fichier du FTP si demandé
                            if delete_after_processing:
                                if self.delete_log_file_from_directory(self.ftp, directory, filename):
                                    logger.info(f"🗑️ Fichier supprimé du FTP")
                                else:
                                    logger.warning(f"⚠️ Fichier traité mais non supprimé du FTP")
                            
                            processed_count += 1
                        else:
                            logger.error(f"❌ Échec de la sauvegarde pour {filename}")
                            error_count += 1
                            
                    except Exception as e:
                        logger.error(f"❌ Erreur inattendue lors du traitement de {directory}/{filename}: {e}")
                        error_count += 1
                
                # Résumé pour ce dossier
                logger.info(f"📊 Dossier {directory} terminé: {processed_count} fichiers traités, {error_count} erreurs")
                total_processed += processed_count
                total_errors += error_count
            
            # === RÉSUMÉ FINAL ===
            logger.info(f"\n🎯 === TRAITEMENT GLOBAL TERMINÉ ===")
            logger.info(f"📈 Total: {total_processed} fichiers traités avec succès")
            logger.info(f"❌ Total: {total_errors} erreurs rencontrées")
            
            # Retourner True seulement s'il n'y a eu aucune erreur
            return total_errors == 0
            
        except Exception as e:
            logger.error(f"❌ Erreur générale lors du traitement: {e}")
            return False
        finally:
            # Toujours fermer les connexions à la fin
            self.close_connections()

    def close_connections(self):
        """
        Ferme proprement toutes les connexions ouvertes.
        Cette fonction est appelée automatiquement à la fin du traitement.
        """
        logger.info("🔌 Fermeture des connexions...")
        
        # Fermer la connexion FTP
        if self.ftp:
            try:
                self.ftp.quit()
                logger.info("✅ Connexion FTP fermée")
            except:
                logger.warning("⚠️ Erreur lors de la fermeture FTP")
        
        # Fermer le curseur de base de données
        if self.cur:
            try:
                self.cur.close()
                logger.info("✅ Curseur de base de données fermé")
            except:
                logger.warning("⚠️ Erreur lors de la fermeture du curseur")
        
        # Fermer la connexion à la base de données
        if self.conn:
            try:
                self.conn.close()
                logger.info("✅ Connexion à la base de données fermée")
            except:
                logger.warning("⚠️ Erreur lors de la fermeture de la base de données")


def main():
    """
    Fonction principale qui peut être appelée directement.
    Utile pour tester le service ou l'exécuter manuellement.
    """
    logger.info("🎬 Démarrage du service FTP Log")
    
    # Créer une instance du service
    service = FTPLogService()
    
    # Traiter tous les logs (avec suppression des fichiers après traitement)
    success = service.process_all_logs(delete_after_processing=True)
    
    if success:
        logger.info("🎉 Traitement terminé avec succès!")
    else:
        logger.error("💥 Traitement terminé avec des erreurs!")


# Point d'entrée du script
if __name__ == "__main__":
    main() 