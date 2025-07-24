import os
import logging
from datetime import datetime
import mysql.connector
import psycopg2
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/mysql_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MySQLSyncService:
    def __init__(self):
        # Chargement des variables d'environnement
        load_dotenv()
        
        # Configuration MySQL
        self.mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'mysql_db'),
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DB'),
            'port': int(os.getenv('MYSQL_PORT', '3306'))
        }
        
        # Configuration PostgreSQL
        self.pg_config = {
            'dbname': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'host': os.getenv('POSTGRES_HOST')
        }
        
        # Création de la table PostgreSQL si elle n'existe pas
        self.create_postgres_table()

    def create_postgres_table(self):
        """Crée la table PostgreSQL si elle n'existe pas"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS commandes_volets (
            id_commande VARCHAR(32) PRIMARY KEY,
            numero_commande INTEGER NOT NULL,
            extension VARCHAR(5),
            statut VARCHAR(50),
            affaire VARCHAR(100),
            date_modification TIMESTAMP,
            code_accessoire VARCHAR(20),
            description_accessoire TEXT,
            numero_operation VARCHAR(20),
            description_operation TEXT,
            date_synchronisation TIMESTAMP
        );
        """
        
        try:
            pg_conn = self.connect_postgres()
            cursor = pg_conn.cursor()
            cursor.execute(create_table_query)
            pg_conn.commit()
            logger.info("Table PostgreSQL créée ou déjà existante")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la table PostgreSQL: {e}")
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'pg_conn' in locals():
                pg_conn.close()

    def connect_mysql(self):
        """Établit la connexion à MySQL"""
        try:
            return mysql.connector.connect(**self.mysql_config)
        except mysql.connector.Error as e:
            logger.error(f"Erreur de connexion MySQL: {e}")
            raise

    def connect_postgres(self):
        """Établit la connexion à PostgreSQL"""
        try:
            return psycopg2.connect(**self.pg_config)
        except psycopg2.Error as e:
            logger.error(f"Erreur de connexion PostgreSQL: {e}")
            raise

    def debug_tables(self):
        """Affiche le contenu des tables pour le debug"""
        try:
            mysql_conn = self.connect_mysql()
            cursor = mysql_conn.cursor(dictionary=True)
            
            # Vérifier p_zubeh
            logger.info("=== Contenu de p_zubeh ===")
            cursor.execute("SELECT * FROM p_zubeh WHERE zcode LIKE 'VR%' OR zcode LIKE 'SOP%' OR zcode LIKE 'S P%'")
            zubeh = cursor.fetchall()
            for z in zubeh:
                logger.info(f"p_zubeh: id={z.get('id')}, id_a_kopf={z.get('id_a_kopf')}, zcode={z.get('zcode')}")
            
            # Vérifier a_logbuch avec les deux variantes d'encodage
            logger.info("=== Recherche des commandes planifiées ===")
            cursor.execute("SELECT * FROM a_logbuch WHERE notiz LIKE '%cde Planifiée%' OR notiz LIKE '%cde PlanifiÃ©e%'")
            planifiees = cursor.fetchall()
            for p in planifiees:
                logger.info(f"Commande planifiée: id={p.get('id')}, id_a_kopf={p.get('id_a_kopf')}, notiz={p.get('notiz')}")

            # Vérifier les jointures
            logger.info("=== Test de la jointure complète ===")
            cursor.execute("""
                SELECT k.id, k.aunummer, l.notiz, z.zcode 
                FROM a_kopf k 
                JOIN a_logbuch l ON l.id_a_kopf = k.id 
                JOIN p_zubeh z ON z.id_a_kopf = k.id 
                WHERE (z.zcode LIKE 'VR%' OR z.zcode LIKE 'SOP%' OR z.zcode LIKE 'S P%')
                AND (l.notiz LIKE '%cde Planifiée%' OR l.notiz LIKE '%cde PlanifiÃ©e%')
            """)
            jointures = cursor.fetchall()
            for j in jointures:
                logger.info(f"Jointure: id={j.get('id')}, aunummer={j.get('aunummer')}, notiz={j.get('notiz')}, zcode={j.get('zcode')}")

        except Exception as e:
            logger.error(f"Erreur lors du debug: {e}")
            logger.error(f"Exception détaillée: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'mysql_conn' in locals():
                mysql_conn.close()

    def get_commandes_with_volets(self):
        """Récupère les commandes avec volets depuis MySQL"""
        # Debug des tables avant la requête principale
        self.debug_tables()
        
        query = """
        SELECT DISTINCT
            k.id,
            k.aunummer as numero_commande,
            k.aualpha as extension,
            k.aufstatus as statut,
            k.kommission as affaire,
            l.datum as date_modification,
            z.zcode as code_accessoire,
            z.text as description_accessoire,
            v.nummer as numero_operation,
            v.bezeichnung as description_operation,
            l.notiz as notiz
        FROM a_kopf k
        JOIN a_logbuch l ON l.id_a_kopf = k.id
        JOIN p_zubeh z ON z.id_a_kopf = k.id
        LEFT JOIN a_vorgang v ON v.id_a_kopf = k.id
        WHERE (z.zcode LIKE 'VR%' OR z.zcode LIKE 'SOP%' OR z.zcode LIKE 'S P%')
        AND (l.notiz LIKE '%cde Planifiée%' OR l.notiz LIKE '%cde PlanifiÃ©e%')
        ORDER BY k.aunummer;
        """
        
        try:
            mysql_conn = self.connect_mysql()
            cursor = mysql_conn.cursor(dictionary=True)
            
            # Log de la requête
            logger.info(f"Exécution de la requête: {query}")
            
            cursor.execute(query)
            commandes = cursor.fetchall()
            
            # Log détaillé des résultats
            logger.info(f"Nombre total de commandes trouvées: {len(commandes)}")
            for commande in commandes:
                logger.info(f"Commande trouvée:")
                logger.info(f"  - ID: {commande['id']}")
                logger.info(f"  - Numéro: {commande['numero_commande']}")
                logger.info(f"  - Extension: {commande['extension']}")
                logger.info(f"  - Code accessoire: {commande['code_accessoire']}")
                logger.info(f"  - Notiz: {commande['notiz']}")
            
            return commandes
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des commandes: {e}")
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'mysql_conn' in locals():
                mysql_conn.close()

    def insert_into_postgres(self, commandes):
        """Insère les commandes dans PostgreSQL"""
        insert_query = """
        INSERT INTO commandes_volets (
            id_commande,
            numero_commande,
            extension,
            statut,
            affaire,
            date_modification,
            code_accessoire,
            description_accessoire,
            numero_operation,
            description_operation,
            date_synchronisation
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id_commande) 
        DO UPDATE SET
            statut = EXCLUDED.statut,
            date_modification = EXCLUDED.date_modification,
            date_synchronisation = EXCLUDED.date_synchronisation;
        """
        
        try:
            pg_conn = self.connect_postgres()
            cursor = pg_conn.cursor()
            
            for commande in commandes:
                values = (
                    commande['id'],
                    commande['numero_commande'],
                    commande['extension'],
                    commande['statut'],
                    commande['affaire'],
                    commande['date_modification'],
                    commande['code_accessoire'],
                    commande['description_accessoire'],
                    commande['numero_operation'],
                    commande['description_operation'],
                    datetime.now()
                )
                cursor.execute(insert_query, values)
            
            pg_conn.commit()
            logger.info(f"Synchronisation de {len(commandes)} commandes terminée")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion dans PostgreSQL: {e}")
            if 'pg_conn' in locals():
                pg_conn.rollback()
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'pg_conn' in locals():
                pg_conn.close()

    def sync(self):
        """Processus principal de synchronisation"""
        try:
            logger.info("Démarrage de la synchronisation des commandes")
            commandes = self.get_commandes_with_volets()
            if commandes:
                self.insert_into_postgres(commandes)
            logger.info("Synchronisation terminée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation: {e}")
            raise

def main():
    try:
        sync_service = MySQLSyncService()
        sync_service.sync()
    except Exception as e:
        logger.error(f"Erreur dans le processus principal: {e}")
        raise

if __name__ == "__main__":
    main() 