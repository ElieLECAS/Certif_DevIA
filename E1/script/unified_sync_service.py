from sqlalchemy import create_engine, text, Table, Column, Integer, String, DateTime, Float, SmallInteger, ForeignKey, MetaData, Numeric, case
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import logging
import ftplib
import pandas as pd
import re
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration des bases de données
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql_db')

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

# Configuration FTP
FTP_HOST = os.getenv('FTP_HOST', 'ftp')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

# Récupération des horaires de synchronisation depuis les variables d'environnement
SYNC_HOUR = os.getenv('SYNC_HOUR', '8')  # Par défaut à 8h
SYNC_MINUTE = os.getenv('SYNC_MINUTE', '0')  # Par défaut à 0 minute
SYNC_INTERVAL = os.getenv('SYNC_INTERVAL', None)  # Intervalle en minutes (optionnel)

# URLs des bases de données
MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

# Création des modèles SQLAlchemy pour MySQL
Base = declarative_base()

class AKopf(Base):
    __tablename__ = 'A_Kopf'
    
    id = Column('ID', String(32), primary_key=True)
    auftragstyp = Column('AuftragsTyp', SmallInteger)
    aunummer = Column('AuNummer', Integer)
    aualpha = Column('AuAlpha', String(5))
    aufstatus = Column('AufStatus', String(15))
    
    # Relations
    alogbuch = relationship("ALogbuch", back_populates="kopf")
    pzubeh = relationship("PZubeh", back_populates="kopf")
    vorgangen = relationship("AVorgang", back_populates="kopf")

class ALogbuch(Base):
    __tablename__ = 'A_Logbuch'
    
    id = Column('ID', Integer, primary_key=True, autoincrement=True)
    id_a_kopf = Column('ID_A_Kopf', String(32), ForeignKey('A_Kopf.ID'))
    datum = Column('Datum', DateTime)
    notiz = Column('Notiz', String)
    
    # Relations
    kopf = relationship("AKopf", back_populates="alogbuch")

class PZubeh(Base):
    __tablename__ = 'P_Zubeh'
    
    id = Column('ID', Integer, primary_key=True, autoincrement=True)
    id_a_kopf = Column('ID_A_Kopf', String(32), ForeignKey('A_Kopf.ID'))
    position = Column('Position', SmallInteger)
    kennung = Column('Kennung', SmallInteger)
    znr = Column('ZNr', SmallInteger)
    zcode = Column('ZCode', String(20))
    
    # Relations
    kopf = relationship("AKopf", back_populates="pzubeh")

class AVorgang(Base):
    __tablename__ = 'A_Vorgang'
    
    id = Column('ID', Integer, primary_key=True, autoincrement=True)
    id_a_kopf = Column('ID_A_Kopf', String(32), ForeignKey('A_Kopf.ID'))
    nummer = Column('Nummer', String(15))
    
    # Relations
    kopf = relationship("AKopf", back_populates="vorgangen")

def get_commandes_fenetres(session):
    """Récupère les commandes avec fenêtres et volets roulants"""
    try:
        results = (
            session.query(
                AKopf.aunummer.label('numero_commande'),
                AKopf.aualpha.label('extension'),
                AKopf.aufstatus.label('status'),
                ALogbuch.datum.label('date_modification'),
                PZubeh.zcode.label('coffre'),
                case([(AVorgang.nummer.like('%VR%'), 1)], else_=0).label('gestion_en_stock')
            )
            .join(ALogbuch)
            .join(PZubeh)
            .outerjoin(AVorgang)
            .filter(ALogbuch.notiz.like('%cde Planifiée%'))
            .filter(
                (AKopf.aufstatus.like('%Planifiée%')) |
                (AKopf.aufstatus.like('%lancer en prod%')) |
                (AKopf.aufstatus.like('%vitrage%'))
            )
            .filter(
                (PZubeh.zcode.like('SOP%')) |
                (PZubeh.zcode.like('S P %')) |
                (PZubeh.zcode.like('S D %')) |
                (PZubeh.zcode.like('S Q %')) |
                (PZubeh.zcode.like('S T %')) |
                (PZubeh.zcode.like('S TAB %')) |
                (PZubeh.zcode.like('S TN %'))
            )
            .distinct()
        ).all()
        
        commandes = []
        for result in results:
            commande = {
                'numero_commande': str(result.numero_commande),
                'extension': result.extension,
                'status': result.status,
                'date_modification': result.date_modification.strftime('%d/%m/%Y') if result.date_modification else None,
                'coffre': result.coffre,
                'gestion_en_stock': result.gestion_en_stock
            }
            commandes.append(commande)
        
        # Tri et déduplication
        commandes.sort(key=lambda x: (-x['gestion_en_stock'], int(x['numero_commande']) if x['numero_commande'].isdigit() else 0))
        
        seen = set()
        deduplicated = []
        for commande in commandes:
            key = (commande['numero_commande'], commande['extension'])
            if key not in seen:
                seen.add(key)
                deduplicated.append(commande)
        
        return deduplicated
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des commandes: {str(e)}")
        return []

def process_cu_file(file_path):
    """Traite un fichier de données CU"""
    try:
        # Lecture du fichier avec pandas
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        
        # Traitement des données selon vos besoins
        # Exemple : nettoyage, transformation, etc.
        
        return df
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du fichier {file_path}: {str(e)}")
        return None

def sync_ftp_files():
    """Synchronise les fichiers depuis le serveur FTP"""
    try:
        # Connexion au serveur FTP
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        
        # Liste des répertoires à parcourir
        directories = ['DEM12 (PVC)', 'DEMALU (ALU)', 'SU12 (HYBRIDE)']
        
        for directory in directories:
            try:
                ftp.cwd(f'/{directory}')
                files = ftp.nlst()
                
                for file in files:
                    if file.endswith('.csv'):  # ou tout autre extension pertinente
                        local_path = f'./logs/{directory}/{file}'
                        
                        # Téléchargement du fichier
                        with open(local_path, 'wb') as f:
                            ftp.retrbinary(f'RETR {file}', f.write)
                        
                        # Traitement du fichier
                        df = process_cu_file(local_path)
                        if df is not None:
                            # Sauvegarde dans PostgreSQL
                            engine = create_engine(POSTGRES_URL)
                            df.to_sql('cu_data', engine, if_exists='append', index=False)
                            
                        # Suppression du fichier local après traitement
                        os.remove(local_path)
                        
            except Exception as e:
                logger.error(f"Erreur lors du traitement du répertoire {directory}: {str(e)}")
                continue
                
        ftp.quit()
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation FTP: {str(e)}")

def job_sync_all():
    """Tâche principale de synchronisation"""
    logger.info(f"Début de la synchronisation complète - {datetime.now()}")
    
    try:
        # Synchronisation des fichiers FTP
        sync_ftp_files()
        
        # Synchronisation des commandes
        engine = create_engine(MYSQL_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            commandes = get_commandes_fenetres(session)
            logger.info(f"Récupération de {len(commandes)} commandes")
            
            # Ici vous pouvez ajouter le code pour sauvegarder les commandes
            # Par exemple dans PostgreSQL ou dans un fichier
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation: {str(e)}")
    
    logger.info(f"Fin de la synchronisation - {datetime.now()}")

def main():
    scheduler = BlockingScheduler()
    
    # Configuration des jobs de synchronisation
    if SYNC_INTERVAL:
        # Si un intervalle est défini, on l'utilise
        scheduler.add_job(
            job_sync_all,
            trigger=CronTrigger(minute=f'*/{SYNC_INTERVAL}'),
            id='sync_interval_job',
            name=f'Synchronisation toutes les {SYNC_INTERVAL} minutes'
        )
        logger.info(f"Synchronisation configurée pour s'exécuter toutes les {SYNC_INTERVAL} minutes")
    else:
        # Sinon, on utilise l'heure fixe
        scheduler.add_job(
            job_sync_all,
            trigger=CronTrigger(hour=SYNC_HOUR, minute=SYNC_MINUTE),
            id='sync_daily_job',
            name=f'Synchronisation quotidienne à {SYNC_HOUR}:{SYNC_MINUTE}'
        )
        logger.info(f"Synchronisation configurée pour s'exécuter tous les jours à {SYNC_HOUR}:{SYNC_MINUTE}")
    
    # Exécuter une première synchronisation au démarrage
    logger.info("Exécution de la première synchronisation au démarrage...")
    job_sync_all()
    
    logger.info("Démarrage du planificateur de synchronisation")
    scheduler.start()

if __name__ == "__main__":
    main() 