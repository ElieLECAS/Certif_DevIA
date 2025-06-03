import os
import re
import pandas as pd
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import CentreUsinage, SessionProduction, JobProfil, PeriodeAttente, PeriodeArret, PieceProduction


class LogImportService:
    """Service pour importer les données des fichiers LOG vers la base de données"""
    
    def __init__(self):
        self.log_pattern = re.compile(r"(\d{8} \d{2}:\d{2}:\d{2})\|@(\w+)(?:\s*:?\s*(.*))?")
    
    def parse_log_file(self, log_file_path):
        """Analyse un fichier log et retourne un DataFrame avec les données structurées"""
        print(f"Analyse du fichier: {log_file_path}")
        
        data = []
        
        try:
            with open(log_file_path, "r", encoding="ISO-8859-1") as file:
                for line in file:
                    match = self.log_pattern.match(line.strip())
                    if match:
                        timestamp_str, event, details = match.groups()
                        
                        # Convertir le timestamp en objet datetime
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d %H:%M:%S")
                        data.append({
                            "Timestamp": timestamp,
                            "TimestampStr": timestamp_str,
                            "Event": event,
                            "Details": details.strip() if details else None
                        })
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier {log_file_path}: {str(e)}")
            return None
            
        if not data:
            print(f"Aucune donnée trouvée dans le fichier {log_file_path}")
            return None
            
        df = pd.DataFrame(data)
        return df
    
    def analyze_machine_performance(self, df, log_file_name):
        """Analyse les performances d'une machine à partir des données de log"""
        if df is None or df.empty:
            return None
        
        # Extraire la date du log
        log_date = df["Timestamp"].iloc[0].date()
        
        # Identifier le centre d'usinage
        cu_id = os.path.splitext(log_file_name)[0]
        
        # Analyser les pièces produites
        stuk_df = df[df["Event"] == "StukUitgevoerd"]
        first_piece_time = stuk_df["Timestamp"].iloc[0] if not stuk_df.empty else None
        last_piece_time = stuk_df["Timestamp"].iloc[-1] if not stuk_df.empty else None
        total_pieces = len(stuk_df)
        
        # Durée totale de production
        production_duration = None
        if first_piece_time and last_piece_time:
            production_duration = (last_piece_time - first_piece_time).total_seconds() / 3600
        
        # Analyser les temps d'attente
        wait_times = df[df["Event"] == "MachineWait"]["Details"].dropna()
        wait_timestamps = df[df["Event"] == "MachineWait"]["Timestamp"].dropna()
        
        total_wait_time = 0
        wait_periods = []
        
        for i, wait in enumerate(wait_times):
            try:
                wait_matches = re.findall(r"(\d+) sec", str(wait))
                wait_duration = 0
                
                if wait_matches:
                    wait_duration = float(wait_matches[0])
                else:
                    decimal_matches = re.findall(r"(\d+\.\d+)", str(wait))
                    if decimal_matches:
                        wait_duration = float(decimal_matches[0])
                
                if wait_duration > 0 and i < len(wait_timestamps):
                    wait_start = wait_timestamps.iloc[i]
                    wait_end = wait_start + pd.Timedelta(seconds=wait_duration)
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
        stop_events = df[df["Event"].isin(["MachineStop", "MachineStart"])].copy()
        
        # Extraire l'heure du dernier MachineStop
        machine_stop_events = df[df["Event"] == "MachineStop"]
        last_machine_stop = machine_stop_events["Timestamp"].iloc[-1] if not machine_stop_events.empty else None
        
        # Extraire l'heure du premier MachineStart
        machine_start_events = df[df["Event"] == "MachineStart"]
        first_machine_start = machine_start_events["Timestamp"].iloc[0] if not machine_start_events.empty else None
        
        total_stop_time = 0
        stop_periods = []
        
        if not stop_events.empty:
            stop_events = stop_events.reset_index()
            
            for i in range(len(stop_events) - 1):
                if stop_events.loc[i, "Event"] == "MachineStop" and stop_events.loc[i + 1, "Event"] == "MachineStart":
                    stop_start = stop_events.loc[i, "Timestamp"]
                    stop_end = stop_events.loc[i + 1, "Timestamp"]
                    stop_duration = (stop_end - stop_start).total_seconds()
                    stop_periods.append({
                        "Start": stop_start,
                        "End": stop_end,
                        "Duration": stop_duration
                    })
                    total_stop_time += stop_duration
        
        total_stop_hours = total_stop_time / 3600
        
        # Analyser les profils de jobs
        job_profiles = df[df["Event"] == "JobProfiel"]["Details"].dropna()
        job_timestamps = df[df["Event"] == "JobProfiel"]["Timestamp"].dropna()
        
        job_details = []
        for i, job in enumerate(job_profiles):
            try:
                ref_match = re.search(r"R:(\w+)", job)
                length_match = re.search(r"L:(\d+\.\d+)", job)
                color_match = re.search(r"C:(\w+)", job)
                
                if ref_match and length_match and i < len(job_timestamps):
                    ref = ref_match.group(1)
                    length = float(length_match.group(1))
                    color = color_match.group(1) if color_match else "N/A"
                    timestamp = job_timestamps.iloc[i]
                    
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
        for idx, row in stuk_df.iterrows():
            piece_events.append({
                "Timestamp": row["Timestamp"],
                "Piece": row["Details"]
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
    
    @transaction.atomic
    def import_log_to_database(self, log_file_path, cu_type, cu_name=None):
        """Importe les données d'un fichier LOG vers la base de données"""
        
        # Parser le fichier LOG
        df = self.parse_log_file(log_file_path)
        if df is None:
            raise ValueError(f"Impossible de parser le fichier LOG: {log_file_path}")
        
        # Analyser les performances
        log_file_name = os.path.basename(log_file_path)
        results = self.analyze_machine_performance(df, log_file_name)
        if not results:
            raise ValueError(f"Impossible d'analyser les performances du fichier: {log_file_path}")
        
        # Déterminer le nom du centre d'usinage
        if not cu_name:
            cu_name = results["CU_ID"]
        
        # Ajouter le type de CU au nom pour éviter les conflits
        cu_name_with_type = f"{cu_name}_{cu_type}"
        
        # Créer ou récupérer le centre d'usinage en incluant le type dans la recherche
        centre_usinage, created = CentreUsinage.objects.get_or_create(
            nom=cu_name_with_type,
            type_cu=cu_type,
            defaults={
                'description': f'Centre d\'usinage {cu_type} - {cu_name}',
                'actif': True
            }
        )
        
        if created:
            print(f"Centre d'usinage créé: {centre_usinage}")
        else:
            print(f"Centre d'usinage existant utilisé: {centre_usinage}")
        
        # Créer ou mettre à jour la session de production
        session, created = SessionProduction.objects.update_or_create(
            centre_usinage=centre_usinage,
            date_production=results["Date"],
            defaults={
                'heure_premiere_piece': results["PremierePiece"],
                'heure_derniere_piece': results["DernierePiece"],
                'heure_premier_machine_start': results["PremierMachineStart"],
                'heure_dernier_machine_stop': results["DernierMachineStop"],
                'total_pieces': results["TotalPieces"],
                'duree_production_totale': Decimal(str(results["DureeProduction"] or 0)),
                'temps_attente': Decimal(str(results["TempsAttente"] or 0)),
                'temps_arret_volontaire': Decimal(str(results["TempsArretVolontaire"] or 0)),
                'temps_production_effectif': Decimal(str(results["TempsProductionEffectif"] or 0)),
                'taux_occupation': Decimal(str(results["TauxOccupation"] or 0)),
                'taux_attente': Decimal(str(results["TauxAttente"] or 0)),
                'taux_arret_volontaire': Decimal(str(results["TauxArretVolontaire"] or 0)),
                'fichier_log_source': log_file_name,
            }
        )
        
        if created:
            print(f"Session de production créée: {session}")
        else:
            print(f"Session de production mise à jour: {session}")
        
        # Supprimer les données existantes pour cette session (pour éviter les doublons)
        session.job_profils.all().delete()
        session.periodes_attente.all().delete()
        session.periodes_arret.all().delete()
        session.pieces_produites.all().delete()
        
        # Importer les profils de jobs
        for job in results["JobDetails"]:
            JobProfil.objects.create(
                session=session,
                reference=job["Reference"],
                longueur=Decimal(str(job["Length"])),
                couleur=job["Color"],
                timestamp_debut=job["Timestamp"]
            )
        
        # Importer les périodes d'attente
        for wait in results["WaitPeriods"]:
            PeriodeAttente.objects.create(
                session=session,
                timestamp_debut=wait["Start"],
                timestamp_fin=wait["End"],
                duree_secondes=int(wait["Duration"])
            )
        
        # Importer les périodes d'arrêt
        for stop in results["StopPeriods"]:
            PeriodeArret.objects.create(
                session=session,
                timestamp_debut=stop["Start"],
                timestamp_fin=stop["End"],
                duree_secondes=int(stop["Duration"])
            )
        
        # Importer les pièces produites
        for i, piece in enumerate(results["PieceEvents"], 1):
            PieceProduction.objects.create(
                session=session,
                numero_piece=i,
                timestamp_production=piece["Timestamp"]
            )
        
        print(f"Import terminé pour {session}")
        return session
    
    def import_directory(self, directory_path, cu_type):
        """Importe tous les fichiers LOG d'un répertoire"""
        imported_sessions = []
        
        if not os.path.exists(directory_path):
            raise ValueError(f"Le répertoire n'existe pas: {directory_path}")
        
        log_files = [f for f in os.listdir(directory_path) if f.endswith('.LOG')]
        
        if not log_files:
            print(f"Aucun fichier LOG trouvé dans {directory_path}")
            return imported_sessions
        
        for log_file in log_files:
            log_file_path = os.path.join(directory_path, log_file)
            try:
                session = self.import_log_to_database(log_file_path, cu_type)
                imported_sessions.append(session)
                print(f"✓ Importé: {log_file}")
            except Exception as e:
                print(f"✗ Erreur lors de l'import de {log_file}: {str(e)}")
        
        return imported_sessions


def get_cu_performance_from_db(cu_type=None, date_production=None, cu_name=None):
    """Récupère les données de performance depuis la base de données"""
    
    # Construire la requête
    queryset = SessionProduction.objects.select_related('centre_usinage')
    
    if cu_type:
        queryset = queryset.filter(centre_usinage__type_cu=cu_type)
    
    if date_production:
        queryset = queryset.filter(date_production=date_production)
    
    if cu_name:
        queryset = queryset.filter(centre_usinage__nom=cu_name)
    
    # Ordonner par date décroissante
    queryset = queryset.order_by('-date_production', 'centre_usinage__nom')
    
    return queryset


def get_available_dates_from_db(cu_type=None):
    """Récupère les dates disponibles depuis la base de données"""
    
    queryset = SessionProduction.objects.all()
    
    if cu_type:
        queryset = queryset.filter(centre_usinage__type_cu=cu_type)
    
    dates = queryset.values_list('date_production', flat=True).distinct().order_by('-date_production')
    
    return list(dates)


def get_available_cu_types_from_db():
    """Récupère les types de centres d'usinage disponibles depuis la base de données"""
    
    types = CentreUsinage.objects.values_list('type_cu', flat=True).distinct()
    
    return list(types)


def format_session_for_display(session):
    """Formate une session de production pour l'affichage dans les templates"""
    
    # Extraire le nom original du CU (enlever le suffixe _TYPE)
    cu_name = session.centre_usinage.nom
    if '_' in cu_name:
        # Enlever le suffixe du type (ex: "test_cu1_PVC" -> "test_cu1")
        cu_name_parts = cu_name.split('_')
        if cu_name_parts[-1] in ['PVC', 'ALU', 'HYBRIDE']:
            cu_name = '_'.join(cu_name_parts[:-1])
    
    return {
        "CU_ID": cu_name,
        "Date": session.date_production.strftime('%Y-%m-%d'),
        "PremierePiece": session.heure_premiere_piece,
        "DernierePiece": session.heure_derniere_piece,
        "PremierMachineStart": session.heure_premier_machine_start,
        "DernierMachineStop": session.heure_dernier_machine_stop,
        "TotalPieces": session.total_pieces,
        "DureeProduction": float(session.duree_production_totale),
        "DureeProduction_hhmm": session.duree_production_hhmm,
        "TempsAttente": float(session.temps_attente),
        "TempsAttente_hhmm": session.temps_attente_hhmm,
        "TempsArretVolontaire": float(session.temps_arret_volontaire),
        "TempsArretVolontaire_hhmm": session.temps_arret_volontaire_hhmm,
        "TempsProductionEffectif": float(session.temps_production_effectif),
        "TempsProductionEffectif_hhmm": session.temps_production_effectif_hhmm,
        "TauxOccupation": float(session.taux_occupation),
        "TauxAttente": float(session.taux_attente),
        "TauxArretVolontaire": float(session.taux_arret_volontaire),
        "JobDetails": [
            {
                "Reference": job.reference,
                "Length": float(job.longueur),
                "Color": job.couleur,
                "Timestamp": job.timestamp_debut
            }
            for job in session.job_profils.all()
        ],
        "WaitPeriods": [
            {
                "Start": periode.timestamp_debut,
                "End": periode.timestamp_fin,
                "Duration": periode.duree_secondes
            }
            for periode in session.periodes_attente.all()
        ],
        "StopPeriods": [
            {
                "Start": periode.timestamp_debut,
                "End": periode.timestamp_fin,
                "Duration": periode.duree_secondes
            }
            for periode in session.periodes_arret.all()
        ],
        "PieceEvents": [
            {
                "Timestamp": piece.timestamp_production,
                "Piece": str(piece.numero_piece)
            }
            for piece in session.pieces_produites.all()
        ]
    } 