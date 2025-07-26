import os
import logging
from datetime import datetime
import mysql.connector
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/sync_logs/mysql_sync.log'),
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
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
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
        CREATE TABLE IF NOT EXISTS commandes_volets_roulants (
            id SERIAL PRIMARY KEY,
            numero_commande VARCHAR(20) NOT NULL,
            extension VARCHAR(5),
            status VARCHAR(50),
            date_modification DATE,
            coffre VARCHAR(50),
            gestion_en_stock INTEGER DEFAULT 0,
            date_synchronisation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(numero_commande, extension)
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

    def debug_database_content(self):
        """Fonction de debug pour diagnostiquer le contenu de la base de données"""
        try:
            mysql_conn = self.connect_mysql()
            cursor = mysql_conn.cursor(dictionary=True)
            
            logger.info("=== DEBUG: Vérification du contenu de la base de données ===")
            
            # 1. Vérifier les commandes dans A_Kopf
            logger.info("--- Commandes dans A_Kopf ---")
            cursor.execute("SELECT AuNummer, AuAlpha, AufStatus FROM A_Kopf LIMIT 5")
            commandes = cursor.fetchall()
            for cmd in commandes:
                logger.info(f"Commande: {cmd['AuNummer']}-{cmd['AuAlpha']} | Status: '{cmd['AufStatus']}'")
            
            # 2. Vérifier les logs dans A_Logbuch
            logger.info("--- Logs dans A_Logbuch ---")
            cursor.execute("SELECT ID_A_Kopf, Notiz FROM A_Logbuch LIMIT 5")
            logs = cursor.fetchall()
            for log in logs:
                logger.info(f"Log pour {log['ID_A_Kopf']}: '{log['Notiz']}'")
            
            # 3. Vérifier les accessoires dans P_Zubeh
            logger.info("--- Accessoires dans P_Zubeh ---")
            cursor.execute("SELECT ID_A_Kopf, ZCode FROM P_Zubeh LIMIT 5")
            accessoires = cursor.fetchall()
            for acc in accessoires:
                logger.info(f"Accessoire pour {acc['ID_A_Kopf']}: '{acc['ZCode']}'")
            
            # 4. Test de la requête avec différents encodages
            logger.info("--- Test de la requête avec différents encodages ---")
            
            # Test 1: Requête originale
            cursor.execute("""
                SELECT COUNT(*) as count FROM A_Logbuch 
                WHERE Notiz LIKE '%cde Planifiee%'
            """)
            result1 = cursor.fetchone()
            logger.info(f"Résultats avec 'cde Planifiee': {result1['count']}")
            
            # Test 2: Requête avec encodage différent
            cursor.execute("""
                SELECT COUNT(*) as count FROM A_Logbuch 
                WHERE Notiz LIKE '%cde PlanifiÃ©e%'
            """)
            result2 = cursor.fetchone()
            logger.info(f"Résultats avec 'cde PlanifiÃ©e': {result2['count']}")
            
            # Test 3: Requête avec caractères spéciaux
            cursor.execute("""
                SELECT COUNT(*) as count FROM A_Logbuch 
                WHERE Notiz LIKE '%Planifi%'
            """)
            result3 = cursor.fetchone()
            logger.info(f"Résultats avec 'Planifi': {result3['count']}")
            
            # Test 4: Voir tous les logs uniques
            cursor.execute("""
                SELECT DISTINCT Notiz FROM A_Logbuch 
                WHERE Notiz IS NOT NULL
            """)
            logs_uniques = cursor.fetchall()
            logger.info("--- Tous les logs uniques ---")
            for log in logs_uniques:
                logger.info(f"Log unique: '{log['Notiz']}'")
            
            # Test 5: Vérifier les statuts uniques
            cursor.execute("""
                SELECT DISTINCT AufStatus FROM A_Kopf 
                WHERE AufStatus IS NOT NULL
            """)
            statuts = cursor.fetchall()
            logger.info("--- Tous les statuts uniques ---")
            for statut in statuts:
                logger.info(f"Statut unique: '{statut['AufStatus']}'")
            
            # Test 6: Vérifier les codes d'accessoires
            cursor.execute("""
                SELECT DISTINCT ZCode FROM P_Zubeh 
                WHERE ZCode IS NOT NULL
            """)
            codes = cursor.fetchall()
            logger.info("--- Tous les codes d'accessoires uniques ---")
            for code in codes:
                logger.info(f"Code unique: '{code['ZCode']}'")
            
        except Exception as e:
            logger.error(f"Erreur lors du debug: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'mysql_conn' in locals():
                mysql_conn.close()

    def get_commandes_volets_roulants(self):
        """
        Récupère les commandes de volets roulants depuis MySQL en utilisant la vraie requête
        Cette requête correspond exactement à celle utilisée dans l'entreprise
        """
        # Debug du contenu de la base de données
        self.debug_database_content()
        
        # Requête avec gestion d'encodage multiple
        query = """
        SELECT 
            Cde.AuNummer as numero_commande,
            Cde.AuAlpha as extension, 
            Cde.AufStatus as status,
            DATE(Logb.Datum) as date_modification,
            a.ZCode as coffre,
            CASE WHEN Vorgang.Nummer LIKE '%VR%' THEN 1 ELSE 0 END AS gestion_en_stock
        FROM A_Kopf AS Cde
        LEFT JOIN A_KopfFreie AS cf ON Cde.ID = cf.ID_A_Kopf
        LEFT JOIN A_Logbuch AS Logb ON Cde.ID = Logb.ID_A_Kopf
        LEFT JOIN P_Zubeh AS a ON Cde.ID = a.ID_A_Kopf
        LEFT JOIN P_Artikel AS Paramgen ON Cde.ID = Paramgen.ID_A_Kopf
        LEFT JOIN A_Vorgang AS Vorgang ON Cde.ID = Vorgang.ID_A_Kopf
        WHERE 
            Logb.Notiz LIKE '%cde Planifiee%'
            AND (Cde.AufStatus LIKE '%Planifiee%' OR Cde.AufStatus LIKE '%lancer en prod%' OR Cde.AufStatus LIKE '%vitrage%')
            AND (a.ZCode LIKE 'SOP%' OR a.ZCode LIKE 'S P %' OR a.ZCode LIKE 'S D %' OR a.ZCode LIKE 'S Q %' OR a.ZCode LIKE 'S T %' OR a.ZCode LIKE 'S TAB %' OR a.ZCode LIKE 'S TN %')
        GROUP BY Cde.AuNummer, Cde.AuAlpha, Cde.AufStatus, Logb.Datum, a.ZCode, Vorgang.Nummer
        ORDER BY Cde.AuNummer, Cde.AuAlpha
        """
        
        try:
            mysql_conn = self.connect_mysql()
            cursor = mysql_conn.cursor(dictionary=True)
            
            logger.info("Exécution de la requête pour récupérer les commandes de volets roulants...")
            logger.info(f"Requête: {query}")
            
            cursor.execute(query)
            commandes = cursor.fetchall()
            
            logger.info(f"Nombre total de lignes trouvées: {len(commandes)}")
            
            # Convertir en DataFrame pour traitement comme dans le code original
            if commandes:
                df = pd.DataFrame(commandes)
                
                # Convertir le numéro de commande en string
                df['numero_commande'] = df['numero_commande'].astype(str)
                
                # Supprimer les doublons exacts
                df.drop_duplicates(subset=['numero_commande','extension', 'gestion_en_stock'], inplace=True)
                
                # Trier d'abord pour mettre les lignes avec gestion_en_stock = 1 en premier
                df_sorted = df.sort_values(by='gestion_en_stock', ascending=False)
                
                # Puis supprimer les doublons en gardant la première occurrence (celle avec gestion_en_stock = 1 si elle existe)
                df_unique = df_sorted.drop_duplicates(subset=['numero_commande', 'extension'], keep='first').reset_index(drop=True)
                
                logger.info(f"Nombre de commandes uniques après traitement: {len(df_unique)}")
                
                # Log des résultats pour debug
                for _, row in df_unique.iterrows():
                    logger.info(f"Commande: {row['numero_commande']}-{row['extension']} | Status: {row['status']} | Coffre: {row['coffre']} | Gestion Stock: {row['gestion_en_stock']}")
                
                # Convertir le DataFrame en liste de dictionnaires
                return df_unique.to_dict('records')
            else:
                logger.warning("Aucune commande trouvée")
                return []
                
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
        if not commandes:
            logger.info("Aucune commande à synchroniser")
            return
            
        # Nettoyage de la table avant insertion
        truncate_query = "TRUNCATE TABLE commandes_volets_roulants RESTART IDENTITY;"
        
        insert_query = """
        INSERT INTO commandes_volets_roulants (
            numero_commande,
            extension,
            status,
            date_modification,
            coffre,
            gestion_en_stock,
            date_synchronisation
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        );
        """
        
        try:
            pg_conn = self.connect_postgres()
            cursor = pg_conn.cursor()
            
            # Exécution du nettoyage
            logger.info("Nettoyage de la table commandes_volets_roulants...")
            cursor.execute(truncate_query)
            
            # Insertion des nouvelles données
            logger.info(f"Insertion de {len(commandes)} nouvelles commandes...")
            for commande in commandes:
                values = (
                    commande['numero_commande'],
                    commande['extension'],
                    commande['status'],
                    commande['date_modification'],
                    commande['coffre'],
                    commande['gestion_en_stock'],
                    datetime.now()
                )
                cursor.execute(insert_query, values)
            
            pg_conn.commit()
            logger.info(f"Synchronisation de {len(commandes)} commandes de volets roulants terminée")
            
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
            logger.info("=== Démarrage de la synchronisation des commandes de volets roulants ===")
            
            # Récupération des commandes
            commandes = self.get_commandes_volets_roulants()
            
            if commandes:
                # Insertion en base PostgreSQL
                self.insert_into_postgres(commandes)
                
                logger.info(f"=== Synchronisation terminée avec succès - {len(commandes)} commandes traitées ===")
            else:
                logger.info("=== Aucune commande à synchroniser ===")
                
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