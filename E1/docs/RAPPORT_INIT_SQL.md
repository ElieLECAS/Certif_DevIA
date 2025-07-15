# Rapport Technique - Script d'Initialisation MySQL (init.sql)

## Vue d'ensemble

Le fichier `init.sql` est un script d'initialisation complet pour la base de données MySQL `db_commandes`. Il simule un système de gestion de commandes de volets roulants avec des données réalistes et une structure normalisée. Ce script est exécuté automatiquement lors du premier démarrage du conteneur MySQL.

## Structure de la Base de Données

### 1. Table `a_kopf` - Informations principales des commandes

**Structure**:

```sql
CREATE TABLE IF NOT EXISTS a_kopf (
    id VARCHAR(32) PRIMARY KEY,
    auftragstyp SMALLINT,           -- Type de commande
    aunummer INT,                   -- Numéro de commande
    aualpha VARCHAR(5),             -- Extension/alpha
    kundennr VARCHAR(15),           -- Numéro client
    kundenbez VARCHAR(15),          -- Nom client
    kommission VARCHAR(50),         -- Affaire/commission
    bauvorhaben VARCHAR(50),        -- Projet de construction
    auftragsart SMALLINT,           -- Type d'affaire
    fsystemgrp SMALLINT,            -- Groupe système
    aufstatus VARCHAR(15),          -- Statut de la commande
    techniker VARCHAR(15),          -- Technicien assigné
    a_vormwst DECIMAL(15,2),       -- Prix HT
    UNIQUE KEY unique_commande (auftragstyp, aunummer, aualpha)
)
```

**Données d'exemple**:

-   50 commandes avec des numéros séquentiels (230001-230050)
-   Statuts variés : "Planifiée", "En production", "Terminée", "En attente"
-   Prix HT entre 2500€ et 15000€
-   Clients divers (DUPONT, MARTIN, DUBOIS, etc.)

### 2. Table `a_logbuch` - Logs des commandes

**Structure**:

```sql
CREATE TABLE IF NOT EXISTS a_logbuch (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_a_kopf VARCHAR(32),         -- Référence vers a_kopf
    code VARCHAR(15),               -- Code de log
    bezeichnung VARCHAR(50),        -- Description
    datum DATETIME,                 -- Date
    zeit DATETIME,                  -- Heure
    benutzer VARCHAR(50),           -- Utilisateur
    notiz TEXT,                     -- Notes
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
)
```

**Fonctionnalités**:

-   Traçabilité complète des modifications
-   Historique des actions par utilisateur
-   Notes détaillées sur l'état des commandes

### 3. Table `a_vorgang` - Événements des commandes

**Structure**:

```sql
CREATE TABLE IF NOT EXISTS a_vorgang (
    id_a_kopf VARCHAR(32),         -- Référence vers a_kopf
    nummer VARCHAR(15),             -- Numéro d'événement
    bezeichnung VARCHAR(50),        -- Description
    datum DATETIME,                 -- Date
    zeit DATETIME,                  -- Heure
    benutzer VARCHAR(50),           -- Utilisateur
    notizcode VARCHAR(15),          -- Code de note
    notiztext TEXT,                 -- Texte de note
    codeintern VARCHAR(15),         -- Code interne
    nloesch SMALLINT,               -- Flag de suppression
    PRIMARY KEY (id_a_kopf, nummer),
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
)
```

**Utilisation**:

-   Suivi des étapes de production
-   Gestion des interventions techniques
-   Historique des modifications

### 4. Table `p_artikel` - Articles des commandes

**Structure**:

```sql
CREATE TABLE IF NOT EXISTS p_artikel (
    id VARCHAR(36) PRIMARY KEY,
    id_a_kopf VARCHAR(32),         -- Référence vers a_kopf
    position INT,                   -- Position dans la commande
    artikelid VARCHAR(255),         -- ID de l'article
    dim1 INT,                       -- Dimension 1
    dim2 INT,                       -- Dimension 2
    dim3 INT,                       -- Dimension 3
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
)
```

**Données**:

-   Articles de fenêtres et volets
-   Dimensions en millimètres
-   Références produits standardisées

### 5. Table `p_zubeh` - Accessoires des commandes

**Structure**:

```sql
CREATE TABLE IF NOT EXISTS p_zubeh (
    id_a_kopf VARCHAR(32),         -- Référence vers a_kopf
    position SMALLINT,              -- Position
    kennung SMALLINT,               -- Kennung
    znr SMALLINT,                   -- Numéro d'accessoire
    zcode VARCHAR(20),              -- Code accessoire
    text VARCHAR(50),               -- Description
    stueck FLOAT,                   -- Quantité
    PRIMARY KEY (id_a_kopf, position, kennung, znr),
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
)
```

**Codes d'accessoires importants**:

-   `VR%` : Volets roulants
-   `SOP%` : Coffres standard
-   `S P%` : Coffres sur mesure

### 6. Table `a_kopffreie` - Informations additionnelles

**Structure**:

```sql
CREATE TABLE IF NOT EXISTS a_kopffreie (
    id_a_kopf VARCHAR(32),         -- Référence vers a_kopf
    nummer SMALLINT,                -- Numéro de champ
    feldtyp INT,                    -- Type de champ
    feldinhalt VARCHAR(50),         -- Contenu du champ
    feld1 VARCHAR(50),              -- Champ libre 1
    feld2 VARCHAR(50),              -- Nombre de menuiseries
    feld3 VARCHAR(50),              -- Date d'entrée
    feld5 VARCHAR(50),              -- Date de livraison
    PRIMARY KEY (id_a_kopf, nummer),
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
)
```

### 7. Table `a_adresse` - Adresses des clients

**Structure**:

```sql
CREATE TABLE IF NOT EXISTS a_adresse (
    id_a_kopf VARCHAR(32),         -- Référence vers a_kopf
    nummer SMALLINT,                -- Numéro d'adresse
    adressnummer VARCHAR(15),       -- Numéro d'adresse
    adresscode VARCHAR(50),         -- Code d'adresse
    firma VARCHAR(50),              -- Nom de l'entreprise
    telefon VARCHAR(30),            -- Téléphone
    email VARCHAR(100),             -- Email
    PRIMARY KEY (id_a_kopf, nummer),
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
)
```

## Optimisations et Index

### Index créés pour optimiser les performances :

```sql
CREATE INDEX idx_aufstatus ON a_kopf(aufstatus);
CREATE INDEX idx_aunummer ON a_kopf(aunummer);
CREATE INDEX idx_zcode ON p_zubeh(zcode);
CREATE INDEX idx_notiz ON a_logbuch(notiz(255));
```

**Avantages**:

-   Recherche rapide par statut de commande
-   Tri efficace par numéro de commande
-   Recherche optimisée des accessoires
-   Index partiel sur les notes (255 caractères)

## Intégrité Référentielle

### Contraintes de clés étrangères :

-   `a_logbuch.id_a_kopf` → `a_kopf.id`
-   `a_vorgang.id_a_kopf` → `a_kopf.id`
-   `p_artikel.id_a_kopf` → `a_kopf.id`
-   `p_zubeh.id_a_kopf` → `a_kopf.id`
-   `a_kopffreie.id_a_kopf` → `a_kopf.id`
-   `a_adresse.id_a_kopf` → `a_kopf.id`

## Données de Test Réalistes

### Répartition des commandes :

-   **50 commandes** avec des numéros séquentiels
-   **Statuts variés** : Planifiée, En production, Terminée, En attente
-   **Prix diversifiés** : 2500€ à 15000€
-   **Clients multiples** : 40 clients différents
-   **Techniciens** : TECH1, TECH2, TECH3

### Accessoires représentatifs :

-   Volets roulants motorisés et manuels
-   Coffres standard et sur mesure
-   Fenêtres PVC et ALU
-   Stores divers

## Utilisation dans le Système

### Pour la synchronisation :

1. **Recherche des commandes planifiées** avec volets roulants
2. **Jointure complexe** entre `a_kopf`, `a_logbuch`, et `p_zubeh`
3. **Filtrage** par codes d'accessoires (`VR%`, `SOP%`, `S P%`)
4. **Extraction** des données métier pour PostgreSQL

### Requête de synchronisation :

```sql
SELECT DISTINCT
    k.id, k.aunummer, k.aualpha, k.aufstatus, k.kommission,
    l.datum, z.zcode, z.text, v.nummer, v.bezeichnung
FROM a_kopf k
JOIN a_logbuch l ON l.id_a_kopf = k.id
JOIN p_zubeh z ON z.id_a_kopf = k.id
LEFT JOIN a_vorgang v ON v.id_a_kopf = k.id
WHERE (z.zcode LIKE 'VR%' OR z.zcode LIKE 'SOP%' OR z.zcode LIKE 'S P%')
AND (l.notiz LIKE '%cde Planifiée%' OR l.notiz LIKE '%cde PlanifiÃ©e%')
```

## Avantages de cette Structure

1. **Normalisation** : Évite la redondance des données
2. **Traçabilité** : Historique complet des modifications
3. **Flexibilité** : Structure extensible pour de nouveaux types de données
4. **Performance** : Index optimisés pour les requêtes fréquentes
5. **Intégrité** : Contraintes référentielles garantissent la cohérence

Cette base de données simule parfaitement un système legacy complexe avec des données métier réalistes, permettant de tester la synchronisation et l'intégration avec le nouveau système PostgreSQL.
