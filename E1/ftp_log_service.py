import os
import re
import ftplib
from datetime import datetime, timedelta
import psycopg2
from decimal import Decimal
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FTPLogService:
    def __init__(self):
        # Configuration FTP
        self.ftp_host = os.getenv('FTP_HOST', 'ftp')
        self.ftp_user = os.getenv('FTP_USER', 'monuser')
        self.ftp_pass = os.getenv('FTP_PASS', 'motdepasse')
        
        # Configuration base de données
        self.db_host = os.getenv('DB_HOST', 'db')
        self.db_name = os.getenv('DB_NAME', 'logsdb')
        self.db_user = os.getenv('DB_USER', 'user')
        self.db_pass = os.getenv('DB_PASS', 'password')
        
        # Mapping des dossiers CU (noms originaux avec espaces et parenthèses)
        self.cu_directories = {
            'DEM12 (PVC)': 'PVC',
            'DEMALU (ALU)': 'ALU', 
            'SU12 (HYBRIDE)': 'HYBRIDE'
        }
        
        # Connexions
        self.conn = None
        self.cur = None
        self.ftp = None

    def connect_db(self):
        """Connexion à la base de données PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_pass
            )
            self.cur = self.conn.cursor()
            logger.info("Connexion à la base de données réussie")
            return True
        except Exception as e:
            logger.error(f"Erreur connexion DB: {e}")
            return False

    def create_tables(self):
        """Création des tables si elles n'existent pas"""
        try:
            # Table centre_usinage
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
            
            # Table session_production
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
            
            # Table job_profil
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
            
            # Table periode_attente
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
            
            # Table periode_arret
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
            
            # Table piece_production
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
            
            self.conn.commit()
            logger.info("Tables créées avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur création tables: {e}")
            return False

    def connect_ftp(self):
        """Connexion au serveur FTP"""
        try:
            self.ftp = ftplib.FTP(self.ftp_host)
            self.ftp.login(self.ftp_user, self.ftp_pass)
            logger.info("Connexion FTP réussie")
            return True
        except Exception as e:
            logger.error(f"Erreur connexion FTP: {e}")
            self.ftp = None
            return False

    def get_cu_directories_from_ftp(self, ftp):
        """Récupère la liste des dossiers CU disponibles sur le FTP"""
        try:
            if not ftp:
                logger.error("Connexion FTP non établie")
                return []
                
            all_dirs = ftp.nlst()
            cu_dirs = []
            
            for directory in all_dirs:
                if directory in self.cu_directories:
                    cu_dirs.append(directory)
                    logger.info(f"Dossier CU trouvé: {directory} -> Type: {self.cu_directories[directory]}")
            
            if not cu_dirs:
                logger.warning("Aucun dossier CU reconnu trouvé sur le FTP")
                logger.info(f"Dossiers disponibles: {all_dirs}")
                logger.info(f"Dossiers attendus: {list(self.cu_directories.keys())}")
            
            return cu_dirs
        except Exception as e:
            logger.error(f"Erreur récupération dossiers CU: {e}")
            return []

    def get_log_files_from_directory(self, ftp, directory):
        """Récupère la liste des fichiers LOG d'un dossier"""
        try:
            # S'assurer qu'on est à la racine
            ftp.cwd('/')
            
            # Naviguer directement dans le dossier (les espaces sont gérés automatiquement par ftplib)
            ftp.cwd(directory)
            files = ftp.nlst()
            log_files = [f for f in files if f.endswith('.LOG')]
            
            # Revenir à la racine
            ftp.cwd('/')
            
            logger.info(f"Trouvé {len(log_files)} fichiers LOG dans {directory}")
            return log_files
        except Exception as e:
            logger.error(f"Erreur récupération fichiers de {directory}: {e}")
            # Toujours revenir à la racine en cas d'erreur
            try:
                ftp.cwd('/')
            except:
                pass
            return []

    def download_log_file_from_directory(self, ftp, directory, filename):
        """Télécharge un fichier LOG depuis un dossier spécifique"""
        try:
            # S'assurer qu'on est à la racine
            ftp.cwd('/')
            
            # Naviguer directement dans le dossier (les espaces sont gérés automatiquement par ftplib)
            ftp.cwd(directory)
            
            # Utiliser retrbinary pour éviter les problèmes d'encodage
            log_content_bytes = bytearray()
            def handle_binary(data):
                log_content_bytes.extend(data)
            
            ftp.retrbinary(f'RETR {filename}', handle_binary)
            
            # Décoder manuellement avec latin-1 qui accepte tous les bytes
            log_content = log_content_bytes.decode('latin-1')
            
            # Revenir à la racine
            ftp.cwd('/')
            
            logger.info(f"Fichier {directory}/{filename} téléchargé: {len(log_content)} caractères")
            return log_content
        except Exception as e:
            logger.error(f"Erreur téléchargement {directory}/{filename}: {e}")
            # Toujours revenir à la racine en cas d'erreur
            try:
                ftp.cwd('/')
            except:
                pass
            return None

    def delete_log_file_from_directory(self, ftp, directory, filename):
        """Supprime un fichier LOG d'un dossier spécifique"""
        try:
            # S'assurer qu'on est à la racine
            ftp.cwd('/')
            
            # Naviguer directement dans le dossier (les espaces sont gérés automatiquement par ftplib)
            ftp.cwd(directory)
            ftp.delete(filename)
            
            # Revenir à la racine
            ftp.cwd('/')
            
            logger.info(f"Fichier {directory}/{filename} supprimé du FTP")
            return True
        except Exception as e:
            logger.error(f"Erreur suppression {directory}/{filename}: {e}")
            # Toujours revenir à la racine en cas d'erreur
            try:
                ftp.cwd('/')
            except:
                pass
            return False

    def parse_log_content(self, log_content, filename):
        """Parse le contenu d'un fichier LOG et retourne une liste de dictionnaires"""
        try:
            # Nettoyer le contenu pour éviter les problèmes d'encodage
            if isinstance(log_content, bytes):
                log_content = log_content.decode('latin-1')
            
            # Remplacer les caractères problématiques
            log_content = log_content.replace('\x00', '')  # Supprimer les caractères null
            
            lines = log_content.strip().split('\n')
            data = []
            
            for line in lines:
                line = line.strip()
                if not line or '|@' not in line:
                    continue
                
                try:
                    # Format: YYYYMMDD HH:MM:SS|@EventType: Details
                    timestamp_str, event_part = line.split('|@', 1)
                    
                    # Parser le timestamp - nettoyer d'abord
                    timestamp_str = timestamp_str.strip()
                    # Garder seulement les caractères ASCII pour le timestamp
                    timestamp_str = ''.join(c for c in timestamp_str if ord(c) < 128)
                    
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d %H:%M:%S')
                    
                    # Parser l'événement
                    if ':' in event_part:
                        event_type, details = event_part.split(':', 1)
                        event_type = event_type.strip()
                        details = details.strip()
                    else:
                        event_type = event_part.strip()
                        details = ""
                    
                    data.append({
                        "Timestamp": timestamp,
                        "Event": event_type,
                        "Details": details
                    })
                except Exception as e:
                    # Ignorer les lignes problématiques
                    continue
            
            if not data:
                logger.warning(f"Aucune donnée trouvée dans {filename}")
                return []
                
            logger.info(f"Fichier {filename} parsé: {len(data)} événements")
            return data
            
        except Exception as e:
            logger.error(f"Erreur parsing {filename}: {e}")
            return []

    def analyze_machine_performance(self, data, log_file_name, cu_type):
        """Analyse les performances d'une machine à partir des données de log"""
        if not data:
            return None
        
        # Extraire la date du log
        log_date = data[0]["Timestamp"].date()
        
        # Identifier le centre d'usinage (utiliser le type de CU comme nom)
        cu_id = f"{cu_type}_{os.path.splitext(log_file_name)[0]}"
        
        # Analyser les pièces produites
        stuk_events = [event for event in data if event["Event"] == "StukUitgevoerd"]
        first_piece_time = stuk_events[0]["Timestamp"] if stuk_events else None
        last_piece_time = stuk_events[-1]["Timestamp"] if stuk_events else None
        total_pieces = len(stuk_events)
        
        # Durée totale de production
        production_duration = None
        if first_piece_time and last_piece_time:
            production_duration = (last_piece_time - first_piece_time).total_seconds() / 3600
        
        # Analyser les temps d'attente
        wait_events = [event for event in data if event["Event"] == "MachineWait"]
        
        total_wait_time = 0
        wait_periods = []
        
        for event in wait_events:
            try:
                wait_matches = re.findall(r"(\d+) sec", str(event["Details"]))
                wait_duration = 0
                
                if wait_matches:
                    wait_duration = float(wait_matches[0])
                else:
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
                continue
        
        total_wait_hours = total_wait_time / 3600
        
        # Analyser les arrêts volontaires
        stop_events = [event for event in data if event["Event"] in ["MachineStop", "MachineStart"]]
        
        machine_stop_events = [event for event in data if event["Event"] == "MachineStop"]
        last_machine_stop = machine_stop_events[-1]["Timestamp"] if machine_stop_events else None
        
        machine_start_events = [event for event in data if event["Event"] == "MachineStart"]
        first_machine_start = machine_start_events[0]["Timestamp"] if machine_start_events else None
        
        total_stop_time = 0
        stop_periods = []
        
        if stop_events:
            for i in range(len(stop_events) - 1):
                if stop_events[i]["Event"] == "MachineStop" and stop_events[i + 1]["Event"] == "MachineStart":
                    stop_start = stop_events[i]["Timestamp"]
                    stop_end = stop_events[i + 1]["Timestamp"]
                    stop_duration = (stop_end - stop_start).total_seconds()
                    stop_periods.append({
                        "Start": stop_start,
                        "End": stop_end,
                        "Duration": stop_duration
                    })
                    total_stop_time += stop_duration
        
        total_stop_hours = total_stop_time / 3600
        
        # Analyser les profils de jobs
        job_events = [event for event in data if event["Event"] == "JobProfiel"]
        
        job_details = []
        for event in job_events:
            try:
                job = event["Details"]
                ref_match = re.search(r"R:(\w+)", job)
                length_match = re.search(r"L:(\d+\.\d+)", job)
                color_match = re.search(r"C:(\w+)", job)
                
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
                continue
        
        # Collecter les pièces produites
        piece_events = []
        for i, event in enumerate(stuk_events):
            piece_events.append({
                "Timestamp": event["Timestamp"],
                "Piece": event["Details"]
            })
        
        # Calculer les indicateurs de performance
        if production_duration:
            effective_production_time = production_duration - total_wait_hours - total_stop_hours
            total_available_time = production_duration
            
            occupation_rate = (effective_production_time / total_available_time) * 100
            wait_rate = (total_wait_hours / total_available_time) * 100
            stop_rate = (total_stop_hours / total_available_time) * 100
        else:
            effective_production_time = 0
            occupation_rate = 0
            wait_rate = 0
            stop_rate = 0
        
        return {
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

    def save_to_database(self, results, cu_type, log_file_name, directory):
        """Sauvegarde les résultats d'analyse en base de données"""
        try:
            # Déterminer le nom du centre d'usinage
            cu_name = f"{cu_type}_{os.path.splitext(log_file_name)[0]}"
            
            # Créer ou récupérer le centre d'usinage
            self.cur.execute("""
                INSERT INTO centre_usinage (nom, type_cu, description, actif)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nom) DO UPDATE SET
                    type_cu = EXCLUDED.type_cu,
                    description = EXCLUDED.description
                RETURNING id;
            """, (cu_name, cu_type, f'Centre d\'usinage {cu_type} - {directory}', True))
            
            centre_usinage_id = self.cur.fetchone()[0]
            
            # Créer ou mettre à jour la session de production
            self.cur.execute("""
                INSERT INTO session_production (
                    centre_usinage_id, date_production, heure_premiere_piece, heure_derniere_piece,
                    heure_premier_machine_start, heure_dernier_machine_stop, total_pieces,
                    duree_production_totale, temps_attente, temps_arret_volontaire,
                    temps_production_effectif, taux_occupation, taux_attente,
                    taux_arret_volontaire, fichier_log_source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (centre_usinage_id, date_production) DO UPDATE SET
                    heure_premiere_piece = EXCLUDED.heure_premiere_piece,
                    heure_derniere_piece = EXCLUDED.heure_derniere_piece,
                    heure_premier_machine_start = EXCLUDED.heure_premier_machine_start,
                    heure_dernier_machine_stop = EXCLUDED.heure_dernier_machine_stop,
                    total_pieces = EXCLUDED.total_pieces,
                    duree_production_totale = EXCLUDED.duree_production_totale,
                    temps_attente = EXCLUDED.temps_attente,
                    temps_arret_volontaire = EXCLUDED.temps_arret_volontaire,
                    temps_production_effectif = EXCLUDED.temps_production_effectif,
                    taux_occupation = EXCLUDED.taux_occupation,
                    taux_attente = EXCLUDED.taux_attente,
                    taux_arret_volontaire = EXCLUDED.taux_arret_volontaire,
                    fichier_log_source = EXCLUDED.fichier_log_source
                RETURNING id;
            """, (
                centre_usinage_id, results["Date"], results["PremierePiece"], results["DernierePiece"],
                results["PremierMachineStart"], results["DernierMachineStop"], results["TotalPieces"],
                Decimal(str(results["DureeProduction"] or 0)), Decimal(str(results["TempsAttente"] or 0)),
                Decimal(str(results["TempsArretVolontaire"] or 0)), Decimal(str(results["TempsProductionEffectif"] or 0)),
                Decimal(str(results["TauxOccupation"] or 0)), Decimal(str(results["TauxAttente"] or 0)),
                Decimal(str(results["TauxArretVolontaire"] or 0)), f"{directory}/{log_file_name}"
            ))
            
            session_id = self.cur.fetchone()[0]
            
            # Supprimer les données existantes pour cette session
            self.cur.execute("DELETE FROM job_profil WHERE session_id = %s", (session_id,))
            self.cur.execute("DELETE FROM periode_attente WHERE session_id = %s", (session_id,))
            self.cur.execute("DELETE FROM periode_arret WHERE session_id = %s", (session_id,))
            self.cur.execute("DELETE FROM piece_production WHERE session_id = %s", (session_id,))
            
            # Insérer les profils de jobs
            for job in results["JobDetails"]:
                self.cur.execute("""
                    INSERT INTO job_profil (session_id, reference, longueur, couleur, timestamp_debut)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session_id, job["Reference"], Decimal(str(job["Length"])), job["Color"], job["Timestamp"]))
            
            # Insérer les périodes d'attente
            for wait in results["WaitPeriods"]:
                self.cur.execute("""
                    INSERT INTO periode_attente (session_id, timestamp_debut, timestamp_fin, duree_secondes)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, wait["Start"], wait["End"], int(wait["Duration"])))
            
            # Insérer les périodes d'arrêt
            for stop in results["StopPeriods"]:
                self.cur.execute("""
                    INSERT INTO periode_arret (session_id, timestamp_debut, timestamp_fin, duree_secondes)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, stop["Start"], stop["End"], int(stop["Duration"])))
            
            # Insérer les pièces produites
            for i, piece in enumerate(results["PieceEvents"], 1):
                self.cur.execute("""
                    INSERT INTO piece_production (session_id, numero_piece, timestamp_production, details)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, i, piece["Timestamp"], piece["Piece"]))
            
            self.conn.commit()
            logger.info(f"Données sauvegardées pour {cu_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
            self.conn.rollback()
            return False

    def process_all_logs(self, delete_after_processing=True):
        """Traite tous les fichiers LOG du FTP en explorant les sous-dossiers"""
        try:
            # Connexions
            if not self.connect_db():
                return False
            if not self.connect_ftp():
                return False
            
            # Créer les tables
            if not self.create_tables():
                return False
            
            # Récupérer la liste des dossiers de centres d'usinage
            cu_directories = self.get_cu_directories_from_ftp(self.ftp)
            
            if not cu_directories:
                logger.error("Aucun dossier CU trouvé")
                return False
            
            total_processed = 0
            total_errors = 0
            
            # Traiter chaque dossier CU
            for directory in cu_directories:
                cu_type = self.cu_directories[directory]
                logger.info(f"\n=== Traitement du dossier {directory} (Type: {cu_type}) ===")
                
                # Récupérer les fichiers LOG de ce dossier
                log_files = self.get_log_files_from_directory(self.ftp, directory)
                
                if not log_files:
                    logger.warning(f"Aucun fichier LOG trouvé dans {directory}")
                    continue
                
                processed_count = 0
                error_count = 0
                
                # Traiter chaque fichier LOG
                for filename in log_files:
                    try:
                        logger.info(f"Traitement de {directory}/{filename}...")
                        
                        # Télécharger le fichier
                        log_content = self.download_log_file_from_directory(self.ftp, directory, filename)
                        if not log_content:
                            error_count += 1
                            continue
                        
                        # Parser le contenu
                        data = self.parse_log_content(log_content, filename)
                        if not data:
                            error_count += 1
                            continue
                        
                        # Analyser les performances
                        results = self.analyze_machine_performance(data, filename, cu_type)
                        if not results:
                            error_count += 1
                            continue
                        
                        # Sauvegarder en base
                        if self.save_to_database(results, cu_type, filename, directory):
                            logger.info(f"✅ {directory}/{filename} traité avec succès")
                            
                            # Supprimer le fichier du FTP si demandé
                            if delete_after_processing:
                                self.delete_log_file_from_directory(self.ftp, directory, filename)
                            
                            processed_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.error(f"Erreur traitement {directory}/{filename}: {e}")
                        error_count += 1
                
                logger.info(f"Dossier {directory} terminé: {processed_count} fichiers traités, {error_count} erreurs")
                total_processed += processed_count
                total_errors += error_count
            
            logger.info(f"\n=== TRAITEMENT GLOBAL TERMINÉ ===")
            logger.info(f"Total: {total_processed} fichiers traités, {total_errors} erreurs")
            
            return total_errors == 0
            
        except Exception as e:
            logger.error(f"Erreur générale: {e}")
            return False
        finally:
            self.close_connections()

    def close_connections(self):
        """Ferme toutes les connexions"""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                pass
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

def main():
    """Fonction principale"""
    service = FTPLogService()
    success = service.process_all_logs(delete_after_processing=True)
    
    if success:
        logger.info("Traitement terminé avec succès")
    else:
        logger.error("Traitement terminé avec des erreurs")

if __name__ == "__main__":
    main() 