# Système de Traitement des Logs FTP vers PostgreSQL

Ce projet implémente un système automatisé pour récupérer des fichiers LOG depuis un serveur FTP, les parser et stocker les données analysées dans une base de données PostgreSQL.

## Architecture

Le système est composé de 3 services Docker :

1. **FTP Server** (`ftp`) - Serveur FTP pour recevoir les fichiers LOG
2. **PostgreSQL** (`db`) - Base de données pour stocker les données analysées
3. **Parser** (`parser`) - Service qui traite les fichiers LOG

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SERVEUR FTP   │    │     PARSER      │    │   POSTGRESQL    │
│                 │    │                 │    │                 │
│ Reçoit les      │───▶│ Traite les      │───▶│ Stocke les      │
│ fichiers LOG    │    │ logs et calcule │    │ résultats       │
│ des machines    │    │ les métriques   │    │ d'analyse       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Structure des Dossiers FTP

Le système explore automatiquement les sous-dossiers du FTP pour traiter les fichiers LOG par type de centre d'usinage :

```
/home/vsftpd/
├── DEM12 (PVC)/          # Fichiers LOG pour centres PVC
│   ├── 20250528.LOG
│   ├── 20250527.LOG
│   └── ...
├── DEMALU (ALU)/         # Fichiers LOG pour centres ALU
│   ├── 20250528.LOG
│   ├── 20250527.LOG
│   └── ...
└── SU12 (HYBRIDE)/       # Fichiers LOG pour centres HYBRIDE
    ├── 20250528.LOG
    ├── 20250527.LOG
    └── ...
```

## Fichiers Principaux

-   `ftp_log_service.py` - Service principal qui gère la récupération FTP, le parsing et le stockage
-   `script.py` - Script d'entrée exécuté par cron
-   `service.py` - Service Django original (pour référence)
-   `parser.py` - Parser original (pour référence)
-   `test_service.py` - Script de test pour vérifier le fonctionnement

## Configuration

### Variables d'Environnement

Le système utilise les variables d'environnement suivantes :

```bash
# Configuration FTP
FTP_HOST=ftp
FTP_USER=monuser
FTP_PASS=motdepasse

# Configuration PostgreSQL
DB_HOST=db
DB_NAME=logsdb
DB_USER=user
DB_PASS=password
```

### Mapping des Dossiers CU

Le service est configuré pour reconnaître automatiquement les types de centres d'usinage :

```python
cu_directories = {
    'DEM12 (PVC)': 'PVC',
    'DEMALU (ALU)': 'ALU',
    'SU12 (HYBRIDE)': 'HYBRIDE'
}
```

### Structure de la Base de Données

Le système crée automatiquement les tables suivantes :

-   `centre_usinage` - Informations sur les centres d'usinage
-   `session_production` - Sessions de production avec métriques
-   `job_profil` - Profils des jobs traités
-   `periode_attente` - Périodes d'attente machine
-   `periode_arret` - Périodes d'arrêt volontaire
-   `piece_production` - Pièces produites

## Utilisation

### Démarrage avec Docker Compose

```bash
# Construire et démarrer tous les services
docker-compose up -d

# Voir les logs du parser
docker-compose logs -f parser

# Arrêter les services
docker-compose down
```

### Test Manuel

```bash
# Tester la connexion et le fonctionnement
docker-compose exec parser python3 /app/script/test_service.py

# Exécuter le traitement manuellement
docker-compose exec parser python3 /app/script/script.py
```

### Planification Automatique

Le script est configuré pour s'exécuter automatiquement tous les jours à 8h00 via cron.
La tâche cron est définie directement dans le Dockerfile.

## Format des Fichiers LOG

Le système attend des fichiers avec l'extension `.LOG` contenant des lignes au format :

```
YYYYMMDD HH:MM:SS|@EventType: Details
```

Exemples d'événements supportés :

-   `StukUitgevoerd` - Pièce produite
-   `MachineWait` - Attente machine
-   `MachineStop` / `MachineStart` - Arrêt/Démarrage machine
-   `JobProfiel` - Profil de job (R:ref L:longueur C:couleur)

## Traitement par Type de Centre d'Usinage

Le système traite automatiquement chaque dossier selon son type :

-   **DEM12 (PVC)** → Type `PVC`
-   **DEMALU (ALU)** → Type `ALU`
-   **SU12 (HYBRIDE)** → Type `HYBRIDE`

Chaque fichier LOG est traité avec le contexte de son type de centre d'usinage, permettant une analyse spécialisée.

## Métriques Calculées

Pour chaque session de production, le système calcule :

-   **Temps de production** - Durée entre première et dernière pièce
-   **Temps d'attente** - Temps cumulé des attentes machine
-   **Temps d'arrêt volontaire** - Temps entre MachineStop et MachineStart
-   **Taux d'occupation** - Pourcentage de temps productif
-   **Taux d'attente** - Pourcentage de temps en attente
-   **Taux d'arrêt** - Pourcentage de temps d'arrêt volontaire

## Logs et Monitoring

-   Les logs du cron sont stockés dans `/app/cron.log`
-   Les logs du service sont affichés sur stdout/stderr
-   Utiliser `docker-compose logs parser` pour voir les logs en temps réel

### Exemple de Logs de Traitement

```
=== Traitement du dossier DEM12 (PVC) (Type: PVC) ===
Trouvé 45 fichiers LOG dans DEM12 (PVC)
Traitement de DEM12 (PVC)/20250528.LOG...
✅ DEM12 (PVC)/20250528.LOG traité avec succès
...
Dossier DEM12 (PVC) terminé: 45 fichiers traités, 0 erreurs

=== Traitement du dossier DEMALU (ALU) (Type: ALU) ===
Trouvé 38 fichiers LOG dans DEMALU (ALU)
...

=== TRAITEMENT GLOBAL TERMINÉ ===
Total: 125 fichiers traités, 2 erreurs
```

## Dépannage

### Problèmes de Connexion FTP

```bash
# Vérifier que le serveur FTP est accessible
docker-compose exec parser ping ftp

# Lister les dossiers disponibles
docker-compose exec parser python3 -c "
import ftplib
ftp = ftplib.FTP('ftp')
ftp.login('monuser', 'motdepasse')
print('Dossiers:', ftp.nlst())
ftp.quit()
"
```

### Problèmes de Base de Données

```bash
# Vérifier la connexion PostgreSQL
docker-compose exec parser python3 -c "from ftp_log_service import FTPLogService; s=FTPLogService(); s.connect_db(); print('OK')"
```

### Fichiers LOG Non Traités

-   Vérifier que les dossiers sont nommés exactement : `DEM12 (PVC)`, `DEMALU (ALU)`, `SU12 (HYBRIDE)`
-   Vérifier le format des fichiers LOG
-   Vérifier les permissions FTP
-   Consulter les logs pour les erreurs de parsing

### Ajouter un Nouveau Type de Centre d'Usinage

1. Modifier le dictionnaire `cu_directories` dans `ftp_log_service.py`
2. Créer le dossier correspondant sur le serveur FTP
3. Reconstruire l'image Docker

## Développement

### Tests Complets

Le script de test vérifie maintenant :

```bash
python3 test_service.py
```

-   Connexion base de données
-   Connexion FTP
-   Exploration des dossiers CU
-   Traitement d'un fichier unique
-   Processus complet

### Ajouter de Nouveaux Types d'Événements

Modifier la méthode `analyze_machine_performance` dans `ftp_log_service.py` pour supporter de nouveaux types d'événements.

### Modifier la Planification

La tâche cron est définie directement dans le Dockerfile :

```dockerfile
RUN echo "0 8 * * * root python3 /app/script.py >> /app/cron.log 2>&1" > /etc/cron.d/log-parser
```

Pour modifier l'horaire, éditer cette ligne et reconstruire l'image.

# 🐛 Résolution du Bug PostgreSQL ON CONFLICT

## 📋 Résumé du Problème

Le service FTP Log générait l'erreur suivante lors de la sauvegarde en base de données :

```
❌ Erreur lors de la sauvegarde: there is no unique or exclusion constraint matching the ON CONFLICT specification
```

Cette erreur empêchait complètement la sauvegarde des données analysées depuis les fichiers LOG du serveur FTP.

---

## 🔍 Analyse Détaillée du Bug

### **Symptômes observés :**
- ✅ Connexion FTP réussie
- ✅ Téléchargement des fichiers LOG réussi
- ✅ Analyse du contenu des fichiers réussie
- ✅ Calcul des performances réussi
- ❌ **ÉCHEC** lors de la sauvegarde en base de données

### **Message d'erreur complet :**
```bash
2025-06-12 10:31:14,393 - ERROR - ❌ Erreur lors de la sauvegarde: there is no unique or exclusion constraint matching the ON CONFLICT specification
2025-06-12 10:31:14,393 - ERROR - ❌ Échec de la sauvegarde pour 20250405.LOG
```

---

## 🔧 Cause Racine du Problème

### **Le problème technique :**

PostgreSQL exige qu'une **contrainte UNIQUE ou EXCLUSION** existe sur les colonnes spécifiées dans une clause `ON CONFLICT`. 

### **Code problématique :**

```python
# ❌ PROBLÉMATIQUE - Ligne 703-708
self.cur.execute("""
    INSERT INTO centre_usinage (nom, type_cu, description, actif)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (nom) DO UPDATE SET
        type_cu = EXCLUDED.type_cu,
        description = EXCLUDED.description
    RETURNING id;
""", (...))

# ❌ PROBLÉMATIQUE - Ligne 717-735  
self.cur.execute("""
    INSERT INTO session_production (...)
    VALUES (...)
    ON CONFLICT (centre_usinage_id, date_production) DO UPDATE SET
        ...
    RETURNING id;
""", (...))
```

### **Pourquoi ça ne fonctionnait pas :**

1. **Définition des tables :** Les tables étaient bien définies avec les contraintes UNIQUE :
   ```sql
   -- Dans create_tables() - Ligne 118
   nom VARCHAR(100) UNIQUE NOT NULL,
   
   -- Dans create_tables() - Ligne 145  
   UNIQUE(centre_usinage_id, date_production)
   ```

2. **Le problème :** Les tables existaient déjà dans la base de données **SANS** ces contraintes
   - Les tables avaient été créées précédemment avec une version différente du code
   - Les contraintes UNIQUE n'avaient pas été ajoutées rétroactivement
   - PostgreSQL ne peut pas utiliser `ON CONFLICT` sans contrainte correspondante

3. **Scénario typique :**
   ```sql
   -- Ce qui existait réellement dans la DB :
   CREATE TABLE centre_usinage (
       id SERIAL PRIMARY KEY,
       nom VARCHAR(100) NOT NULL,  -- ❌ PAS DE UNIQUE !
       ...
   );
   
   -- Ce que le code attendait :
   CREATE TABLE centre_usinage (
       id SERIAL PRIMARY KEY, 
       nom VARCHAR(100) UNIQUE NOT NULL,  -- ✅ AVEC UNIQUE
       ...
   );
   ```

---

## ⚡ Solution Implémentée

### **Approche choisie : Abandon des clauses ON CONFLICT**

Au lieu de corriger les contraintes manquantes, nous avons opté pour une approche plus robuste et portable.

### **Ancien code (problématique) :**
```python
# ❌ Approche avec ON CONFLICT
self.cur.execute("""
    INSERT INTO centre_usinage (nom, type_cu, description, actif)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (nom) DO UPDATE SET
        type_cu = EXCLUDED.type_cu,
        description = EXCLUDED.description
    RETURNING id;
""", (...))
```

### **Nouveau code (solution) :**
```python
# ✅ Approche SELECT puis INSERT/UPDATE
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
    """, (cu_type, description, centre_usinage_id))
else:
    # Créer un nouveau centre
    self.cur.execute("""
        INSERT INTO centre_usinage (nom, type_cu, description, actif)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, (cu_name, cu_type, description, True))
    centre_usinage_id = self.cur.fetchone()[0]
```

---

## 🎯 Avantages de la Solution

| Aspect | Ancien Code | Nouveau Code |
|--------|-------------|--------------|
| **Dépendance aux contraintes** | ❌ Requiert contraintes UNIQUE | ✅ Fonctionne sans contraintes |
| **Robustesse** | ❌ Échoue si contrainte manquante | ✅ Toujours fonctionnel |
| **Lisibilité** | ❌ Logic cachée dans ON CONFLICT | ✅ Logic explicite et claire |
| **Portabilité** | ❌ Spécifique à PostgreSQL | ✅ Compatible autres SGBD |
| **Débogage** | ❌ Erreur cryptique | ✅ Erreurs SQL standard |

---

## 🚀 Tests et Validation

### **Tests effectués après correction :**

1. **Test de connexion base de données** : ✅ RÉUSSI
2. **Test de connexion FTP** : ✅ RÉUSSI  
3. **Test d'exploration des dossiers** : ✅ RÉUSSI
4. **Test de traitement d'un fichier** : ✅ RÉUSSI
5. **Test du processus complet** : ✅ RÉUSSI

### **Résultat attendu :**
```bash
✅ Données sauvegardées avec succès pour SU12_20250405
✅ SU12 (HYBRIDE)/20250405.LOG traité avec succès
```

---

## 📚 Leçons Apprises

### **Pour éviter ce type de problème à l'avenir :**

1. **Vérification des contraintes** :
   ```sql
   -- Toujours vérifier les contraintes existantes
   SELECT conname, contype, conrelid::regclass 
   FROM pg_constraint 
   WHERE conrelid = 'ma_table'::regclass;
   ```

2. **Migration de schéma** :
   - Toujours créer des scripts de migration pour les changements de schéma
   - Tester sur une copie de la base de données de production

3. **Code défensif** :
   - Privilégier les approches qui fonctionnent même sans contraintes
   - Ajouter des vérifications d'existence avant les opérations critiques

4. **Tests d'intégration** :
   - Tester avec des bases de données dans différents états
   - Inclure des tests avec des données existantes

---

## 🔄 Migration Future (Optionnelle)

Si vous souhaitez restaurer les contraintes UNIQUE pour optimiser les performances :

```sql
-- Script de migration (à appliquer avec précaution)
ALTER TABLE centre_usinage 
ADD CONSTRAINT centre_usinage_nom_unique UNIQUE (nom);

ALTER TABLE session_production 
ADD CONSTRAINT session_production_cu_date_unique 
UNIQUE (centre_usinage_id, date_production);
```

**⚠️ ATTENTION :** Vérifiez qu'il n'y a pas de doublons avant d'ajouter ces contraintes !

---

## 📞 Support

En cas de problème similaire :
1. Vérifiez les logs pour identifier la table et contrainte concernées
2. Contrôlez l'existence des contraintes dans la base de données
3. Appliquez la même approche SELECT/INSERT-UPDATE si nécessaire

---

*Problème résolu le 12 juin 2025 - Service FTP Log opérationnel* ✅
