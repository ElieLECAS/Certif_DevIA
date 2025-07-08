from sqlalchemy import create_engine, text, Table, Column, Integer, String, DateTime, Float, SmallInteger, ForeignKey, MetaData, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la base de données
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql_db')

# Création de la connexion
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

# Création des modèles SQLAlchemy
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

def get_commandes_fenetres():
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Requête avec SQLAlchemy ORM
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
        
        # Conversion en dictionnaires
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
        
        # Déduplication en gardant la première occurrence (avec VR si existe)
        seen = set()
        deduplicated = []
        for commande in commandes:
            key = (commande['numero_commande'], commande['extension'])
            if key not in seen:
                seen.add(key)
                deduplicated.append(commande)
        
        logger.info(f"Récupération réussie de {len(deduplicated)} commandes")
        return deduplicated
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des commandes: {str(e)}")
        return []
    finally:
        session.close()

def job_sync_commandes():
    logger.info(f"Début de la synchronisation - {datetime.now()}")
    commandes = get_commandes_fenetres()
    # Ici vous pouvez ajouter le code pour traiter les commandes
    # Par exemple, les envoyer à une API, les sauvegarder dans un fichier, etc.
    logger.info(f"Fin de la synchronisation - {len(commandes)} commandes traitées")

def main():
    scheduler = BlockingScheduler()
    # Exécution toutes les 5 minutes
    scheduler.add_job(job_sync_commandes, 'cron', minute='*/5')
    
    logger.info("Démarrage du planificateur de synchronisation")
    scheduler.start()

if __name__ == "__main__":
    main() 