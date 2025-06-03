import os
import ftplib
import psycopg2
from io import BytesIO
from datetime import datetime

# Configuration FTP
FTP_HOST = os.getenv("FTP_HOST", "ftp")
FTP_USER = os.getenv("FTP_USER", "monuser")
FTP_PASS = os.getenv("FTP_PASS", "motdepasse")

# Configuration PostgreSQL
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "logsdb")
DB_USER = os.getenv("DB_USER", "user")
DB_PASS = os.getenv("DB_PASS", "password")

# Connexion PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS
)
cur = conn.cursor()

# Création table si elle n'existe pas
cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP,
        level TEXT,
        message TEXT
    );
""")
conn.commit()

# Connexion au FTP
ftp = ftplib.FTP(FTP_HOST)
ftp.login(FTP_USER, FTP_PASS)

# Liste des fichiers .LOG
for filename in ftp.nlst():
    if not filename.endswith(".LOG"):
        continue

    print(f"📥 Téléchargement de {filename}...")

    # Lire le fichier depuis le FTP en mémoire
    bio = BytesIO()
    ftp.retrbinary(f"RETR {filename}", bio.write)
    bio.seek(0)

    lignes = bio.read().decode("utf-8").splitlines()
    for line in lignes:
        if not line.strip():
            continue
        try:
            # Exemple de ligne : 2024-06-01T08:00:00 INFO Démarrage du système
            timestamp_str, level, message = line.strip().split(" ", 2)
            timestamp = datetime.fromisoformat(timestamp_str)
            cur.execute(
                "INSERT INTO logs (timestamp, level, message) VALUES (%s, %s, %s)",
                (timestamp, level, message)
            )
        except Exception as e:
            print(f"❌ Erreur sur la ligne : {line} → {e}")

    # Supprimer le fichier du FTP (optionnel)
    ftp.delete(filename)
    print(f"✅ {filename} traité et supprimé.")

# Nettoyage
conn.commit()
cur.close()
conn.close()
ftp.quit()

print("✅ Script terminé.")
