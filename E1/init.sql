-- Création de l'utilisateur et attribution des droits
CREATE USER IF NOT EXISTS 'fenetre_user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'fenetre_user'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

-- Création de la base de données
CREATE DATABASE IF NOT EXISTS db_commandes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Utilisation de la base de données
USE db_commandes;

-- Table A_Kopf (Informations principales des commandes)
CREATE TABLE IF NOT EXISTS A_Kopf (
    ID VARCHAR(32) PRIMARY KEY,
    AuftragsTyp SMALLINT,
    AuNummer INT,
    AuAlpha VARCHAR(5),
    KundenNr VARCHAR(15),
    KundenBez VARCHAR(15),
    Kommission VARCHAR(50) COMMENT 'Affaire',
    Bauvorhaben VARCHAR(50),
    Auftragsart SMALLINT,
    FSystemGrp SMALLINT,
    AufStatus VARCHAR(50) COMMENT 'Statut de la commande',
    Techniker VARCHAR(15) COMMENT 'Technicien',
    A_VorMwSt DECIMAL(15,2) COMMENT 'Prix HT',
    UNIQUE KEY unique_commande (AuftragsTyp, AuNummer, AuAlpha)
) COMMENT 'Table principale des commandes';

-- Table A_Logbuch (Logs des commandes)
CREATE TABLE IF NOT EXISTS A_Logbuch (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ID_A_Kopf VARCHAR(32),
    Code VARCHAR(15),
    Bezeichnung VARCHAR(50),
    Datum DATETIME,
    Zeit DATETIME,
    Benutzer VARCHAR(50),
    Notiz TEXT,
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID)
) COMMENT 'Logs des commandes';

-- Table A_KopfFreie (Informations additionnelles des commandes)
CREATE TABLE IF NOT EXISTS A_KopfFreie (
    ID_A_Kopf VARCHAR(32),
    Nummer SMALLINT,
    FeldTyp INT,
    FeldInhalt VARCHAR(50),
    Feld1 VARCHAR(50),
    Feld2 VARCHAR(50) COMMENT 'Nombre de menuiseries',
    Feld3 VARCHAR(50) COMMENT 'Date d''entrée',
    Feld5 VARCHAR(50) COMMENT 'Date de livraison',
    PRIMARY KEY (ID_A_Kopf, Nummer),
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID)
) COMMENT 'Informations additionnelles des commandes';

-- Table A_Vorgang (Événements des commandes)
CREATE TABLE IF NOT EXISTS A_Vorgang (
    ID_A_Kopf VARCHAR(32),
    Nummer VARCHAR(15),
    Bezeichnung VARCHAR(50),
    Datum DATETIME COMMENT 'Date',
    Zeit DATETIME COMMENT 'Heure',
    Benutzer VARCHAR(50),
    NotizCode VARCHAR(15),
    NotizText TEXT,
    CodeIntern VARCHAR(15),
    NLoesch SMALLINT,
    PRIMARY KEY (ID_A_Kopf, Nummer),
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID)
) COMMENT 'Événements des commandes';

-- Table P_Artikel (Articles)
CREATE TABLE IF NOT EXISTS P_Artikel (
    ID VARCHAR(36) PRIMARY KEY,
    ID_A_Kopf VARCHAR(32),
    Position INT COMMENT 'Position',
    ArtikelID VARCHAR(255) COMMENT 'ID Article',
    Dim1 INT COMMENT 'Dimension 1',
    Dim2 INT COMMENT 'Dimension 2',
    Dim3 INT COMMENT 'Dimension 3',
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID)
) COMMENT 'Articles des commandes';

-- Table P_Zubeh (Accessoires des commandes) - Table cruciale pour les volets
CREATE TABLE IF NOT EXISTS P_Zubeh (
    ID_A_Kopf VARCHAR(32),
    Position SMALLINT COMMENT 'Position',
    Kennung SMALLINT COMMENT 'Kennung',
    ZNr SMALLINT COMMENT 'ZNr',
    ZCode VARCHAR(20) COMMENT 'Code Accessoire',
    Text VARCHAR(50) COMMENT 'Texte',
    Stueck FLOAT COMMENT 'Quantité',
    PRIMARY KEY (ID_A_Kopf, Position, Kennung, ZNr),
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID)
) COMMENT 'Accessoires des commandes - crucial pour identifier les volets';

-- ============================================================================
-- DONNÉES ADAPTÉES POUR LA REQUÊTE SQL FOURNIE - ENCODAGE UTF-8 CORRECT
-- ============================================================================

-- Commandes qui DOIVENT apparaître dans les résultats (correspondant aux critères)
INSERT INTO A_Kopf VALUES
-- Commandes avec "cde Planifiee" dans les logs ET statut "Planifiee"
('2507748-004', 1, 2507748, '004', 'CLI001', 'DUPONT', 'Villa Dupont', 'Volets Roulants', 1, 1, 'cde Planifiee', 'TECH1', 3500.00),
('2507648-H00', 1, 2507648, 'H00', 'CLI002', 'MARTIN', 'Maison Martin', 'Volets ALU', 1, 2, 'cde Planifiee', 'TECH2', 4500.00),
('2507298-Y00', 1, 2507298, 'Y00', 'CLI003', 'DUBOIS', 'Rénovation Dubois', 'Volets PVC', 1, 1, 'cde Planifiee', 'TECH1', 2800.00),
('2507837-YG0', 1, 2507837, 'YG0', 'CLI004', 'BERNARD', 'Extension Bernard', 'Volets Solaires', 1, 3, 'cde Planifiee', 'TECH3', 5200.00),
('2507732-H00', 1, 2507732, 'H00', 'CLI005', 'THOMAS', 'Villa Thomas', 'Volets Motorisés', 1, 1, 'cde Planifiee', 'TECH1', 6800.00),

-- Commandes avec "cde Planifiee" dans les logs ET statut "lancer en prod"
('2505417-X04', 1, 2505417, 'X04', 'CLI006', 'RICHARD', 'Appart Richard', 'Store Banne', 1, 2, 'lancer en prod', 'TECH2', 1500.00),
('2506535-ZP2', 1, 2506535, 'ZP2', 'CLI010', 'SIMON', 'Terrasse Simon', 'Store Motorisé', 1, 1, 'lancer en prod', 'TECH1', 2200.00),

-- Commandes avec "cde Planifiee" dans les logs ET statut "vitrage"
('2505304-U04', 1, 2505304, 'U04', 'CLI009', 'LAURENT', 'Bureau Laurent', 'Store Vénitien', 1, 2, 'vitrage', 'TECH2', 900.00),

-- Commandes supplémentaires pour enrichir les données
('2507816-YG0', 1, 2507816, 'YG0', 'CLI007', 'DURAND', 'Maison Durand', 'Volets Auto', 1, 1, 'cde Planifiee', 'TECH1', 7200.00),
('2507810-000', 1, 2507810, '000', 'CLI008', 'MOREAU', 'Villa Moreau', 'Volets Design', 1, 1, 'cde Planifiee', 'TECH3', 8500.00),

-- NOUVELLES COMMANDES SUPPLÉMENTAIRES
('2507901-A01', 1, 2507901, 'A01', 'CLI011', 'LEROY', 'Maison Leroy', 'Volets Roulants ALU', 1, 1, 'cde Planifiee', 'TECH1', 4200.00),
('2507902-B02', 1, 2507902, 'B02', 'CLI012', 'ROUX', 'Villa Roux', 'Volets Solaires', 1, 2, 'cde Planifiee', 'TECH2', 5800.00),
('2507903-C03', 1, 2507903, 'C03', 'CLI013', 'BLANC', 'Résidence Blanc', 'Volets PVC', 1, 1, 'lancer en prod', 'TECH1', 3200.00),
('2507904-D04', 1, 2507904, 'D04', 'CLI014', 'NOIR', 'Appart Noir', 'Volets Motorisés', 1, 3, 'cde Planifiee', 'TECH3', 6500.00),
('2507905-E05', 1, 2507905, 'E05', 'CLI015', 'VERT', 'Maison Vert', 'Volets Design', 1, 1, 'vitrage', 'TECH1', 7800.00),
('2507906-F06', 1, 2507906, 'F06', 'CLI016', 'ROUGE', 'Villa Rouge', 'Volets Premium', 1, 2, 'cde Planifiee', 'TECH2', 9200.00),
('2507907-G07', 1, 2507907, 'G07', 'CLI017', 'BLEU', 'Résidence Bleue', 'Volets Connectés', 1, 1, 'cde Planifiee', 'TECH1', 8900.00),
('2507908-H08', 1, 2507908, 'H08', 'CLI018', 'JAUNE', 'Maison Jaune', 'Volets Écologiques', 1, 3, 'lancer en prod', 'TECH3', 5500.00),
('2507909-I09', 1, 2507909, 'I09', 'CLI019', 'ORANGE', 'Villa Orange', 'Volets Sécurisés', 1, 1, 'cde Planifiee', 'TECH1', 7100.00),
('2507910-J10', 1, 2507910, 'J10', 'CLI020', 'VIOLET', 'Appart Violet', 'Volets Intelligents', 1, 2, 'vitrage', 'TECH2', 8300.00),
('2507911-K11', 1, 2507911, 'K11', 'CLI021', 'ROSE', 'Maison Rose', 'Volets Thermiques', 1, 1, 'cde Planifiee', 'TECH1', 6800.00),
('2507912-L12', 1, 2507912, 'L12', 'CLI022', 'GRIS', 'Villa Grise', 'Volets Anti-Effraction', 1, 3, 'cde Planifiee', 'TECH3', 9800.00),
('2507913-M13', 1, 2507913, 'M13', 'CLI023', 'BRUN', 'Résidence Brune', 'Volets Acoustiques', 1, 1, 'lancer en prod', 'TECH1', 7500.00),
('2507914-N14', 1, 2507914, 'N14', 'CLI024', 'BEIGE', 'Maison Beige', 'Volets Isolants', 1, 2, 'cde Planifiee', 'TECH2', 6200.00),
('2507915-O15', 1, 2507915, 'O15', 'CLI025', 'TURQUOISE', 'Villa Turquoise', 'Volets Haute Performance', 1, 1, 'vitrage', 'TECH1', 8700.00),
('2507916-P16', 1, 2507916, 'P16', 'CLI026', 'MAGENTA', 'Appart Magenta', 'Volets Résistants', 1, 3, 'cde Planifiee', 'TECH3', 5900.00),
('2507917-Q17', 1, 2507917, 'Q17', 'CLI027', 'CYAN', 'Maison Cyan', 'Volets Durables', 1, 1, 'cde Planifiee', 'TECH1', 7300.00),
('2507918-R18', 1, 2507918, 'R18', 'CLI028', 'INDIGO', 'Villa Indigo', 'Volets Luxe', 1, 2, 'lancer en prod', 'TECH2', 10500.00),
('2507919-S19', 1, 2507919, 'S19', 'CLI029', 'LIME', 'Résidence Lime', 'Volets Économiques', 1, 1, 'cde Planifiee', 'TECH1', 4800.00),
('2507920-T20', 1, 2507920, 'T20', 'CLI030', 'OLIVE', 'Maison Olive', 'Volets Modulaires', 1, 3, 'vitrage', 'TECH3', 6900.00),

-- NOUVELLES COMMANDES QUI PASSERONT LE FILTRE
('2508001-V01', 1, 2508001, 'V01', 'CLI031', 'AZURE', 'Villa Azure', 'Volets Connectés', 1, 1, 'cde Planifiee', 'TECH1', 8200.00),
('2508002-W02', 1, 2508002, 'W02', 'CLI032', 'CORAL', 'Maison Coral', 'Volets Solaires', 1, 2, 'lancer en prod', 'TECH2', 7400.00),
('2508003-X03', 1, 2508003, 'X03', 'CLI033', 'MINT', 'Résidence Mint', 'Volets Premium', 1, 1, 'vitrage', 'TECH1', 9100.00),
('2508004-Y04', 1, 2508004, 'Y04', 'CLI034', 'PEARL', 'Appart Pearl', 'Volets Intelligents', 1, 3, 'cde Planifiee', 'TECH3', 8800.00),
('2508005-Z05', 1, 2508005, 'Z05', 'CLI035', 'GOLD', 'Villa Gold', 'Volets Luxe', 1, 1, 'cde Planifiee', 'TECH1', 11200.00),

-- NOUVELLES COMMANDES QUI NE PASSERONT PAS LE FILTRE
-- Commandes avec mauvais statuts (même avec bons logs et accessoires)
('2508101-A01', 1, 2508101, 'A01', 'CLI101', 'STEEL', 'Maison Steel', 'Volets Standard', 1, 1, 'Terminée', 'TECH1', 4500.00),
('2508102-B02', 1, 2508102, 'B02', 'CLI102', 'BRONZE', 'Villa Bronze', 'Volets ALU', 1, 2, 'En cours', 'TECH2', 5200.00),
('2508103-C03', 1, 2508103, 'C03', 'CLI103', 'SILVER', 'Résidence Silver', 'Volets PVC', 1, 1, 'Annulée', 'TECH1', 3800.00),
('2508104-D04', 1, 2508104, 'D04', 'CLI104', 'COPPER', 'Appart Copper', 'Volets Design', 1, 3, 'Suspendue', 'TECH3', 6100.00),

-- Commandes avec bons statuts mais sans "cde Planifiee" dans les logs
('2508201-E01', 1, 2508201, 'E01', 'CLI201', 'RUBY', 'Maison Ruby', 'Volets Roulants', 1, 1, 'cde Planifiee', 'TECH1', 5500.00),
('2508202-F02', 1, 2508202, 'F02', 'CLI202', 'EMERALD', 'Villa Emerald', 'Volets Motorisés', 1, 2, 'lancer en prod', 'TECH2', 7300.00),
('2508203-G03', 1, 2508203, 'G03', 'CLI203', 'DIAMOND', 'Résidence Diamond', 'Volets Premium', 1, 1, 'vitrage', 'TECH1', 9500.00),

-- Commandes avec bons statuts et logs mais mauvais accessoires
('2508301-H01', 1, 2508301, 'H01', 'CLI301', 'TOPAZ', 'Maison Topaz', 'Fenêtres', 1, 1, 'cde Planifiee', 'TECH1', 4200.00),
('2508302-I02', 1, 2508302, 'I02', 'CLI302', 'ONYX', 'Villa Onyx', 'Portes', 1, 2, 'lancer en prod', 'TECH2', 5800.00),
('2508303-J03', 1, 2508303, 'J03', 'CLI303', 'JADE', 'Résidence Jade', 'Stores', 1, 1, 'vitrage', 'TECH1', 3900.00),

-- Commandes qui NE DOIVENT PAS apparaître (pour tester le filtrage)
('2507999-Z00', 1, 2507999, 'Z00', 'CLI016', 'GARCIA', 'Test Garcia', 'Volets Test', 1, 1, 'Terminée', 'TECH1', 4000.00),
('2508000-Z01', 1, 2508000, 'Z01', 'CLI017', 'PERRIN', 'Test Perrin', 'Volets Test', 1, 1, 'En cours', 'TECH2', 3500.00);

-- Logs CRUCIAUX - Doivent contenir "cde Planifiee" pour que les commandes apparaissent
INSERT INTO A_Logbuch (ID_A_Kopf, Code, Bezeichnung, Datum, Zeit, Benutzer, Notiz) VALUES
-- Logs pour commandes qui DOIVENT apparaître
('2507748-004', 'LOG1', 'Planification', '2025-06-27 09:00:00', '2025-06-27 09:00:00', 'USER1', 'cde Planifiee - Volets roulants PVC N30'),
('2507648-H00', 'LOG1', 'Planification', '2025-06-25 10:30:00', '2025-06-25 10:30:00', 'USER2', 'cde Planifiee - Volets ALU H30'),
('2507298-Y00', 'LOG1', 'Planification', '2025-06-19 14:15:00', '2025-06-19 14:15:00', 'USER1', 'cde Planifiee - Volets ALU A30-F21'),
('2507837-YG0', 'LOG1', 'Planification', '2025-06-26 11:20:00', '2025-06-26 11:20:00', 'USER3', 'cde Planifiee - Volets ALU GAL'),
('2507732-H00', 'LOG1', 'Planification', '2025-06-25 15:30:00', '2025-06-25 15:30:00', 'USER1', 'cde Planifiee - Volets ALU H30'),
('2505417-X04', 'LOG1', 'Production', '2025-05-14 09:00:00', '2025-05-14 09:00:00', 'USER2', 'cde Planifiee - SOP X 6104+T'),
('2506535-ZP2', 'LOG1', 'Production', '2025-06-16 14:30:00', '2025-06-16 14:30:00', 'USER1', 'cde Planifiee - Volets ALU H30'),
('2505304-U04', 'LOG1', 'Vitrage', '2025-06-06 12:00:00', '2025-06-06 12:00:00', 'USER2', 'cde Planifiee - SOP ALU ASK L F'),
('2507816-YG0', 'LOG1', 'Planification', '2025-06-27 08:00:00', '2025-06-27 08:00:00', 'USER1', 'cde Planifiee - Volets ALU GAL'),
('2507810-000', 'LOG1', 'Planification', '2025-06-27 16:00:00', '2025-06-27 16:00:00', 'USER3', 'cde Planifiee - Volets ALU N30'),

-- LOGS POUR LES NOUVELLES COMMANDES
('2507901-A01', 'LOG1', 'Planification', '2025-06-28 09:00:00', '2025-06-28 09:00:00', 'USER1', 'cde Planifiee - Volets ALU H30'),
('2507902-B02', 'LOG1', 'Planification', '2025-06-28 10:00:00', '2025-06-28 10:00:00', 'USER2', 'cde Planifiee - Volets Solaires Premium'),
('2507903-C03', 'LOG1', 'Production', '2025-06-28 11:00:00', '2025-06-28 11:00:00', 'USER1', 'cde Planifiee - Volets PVC Standard'),
('2507904-D04', 'LOG1', 'Planification', '2025-06-28 12:00:00', '2025-06-28 12:00:00', 'USER3', 'cde Planifiee - Volets Motorisés ALU'),
('2507905-E05', 'LOG1', 'Vitrage', '2025-06-28 13:00:00', '2025-06-28 13:00:00', 'USER1', 'cde Planifiee - Volets Design Premium'),
('2507906-F06', 'LOG1', 'Planification', '2025-06-28 14:00:00', '2025-06-28 14:00:00', 'USER2', 'cde Planifiee - Volets Premium ALU'),
('2507907-G07', 'LOG1', 'Planification', '2025-06-28 15:00:00', '2025-06-28 15:00:00', 'USER1', 'cde Planifiee - Volets Connectés IoT'),
('2507908-H08', 'LOG1', 'Production', '2025-06-28 16:00:00', '2025-06-28 16:00:00', 'USER3', 'cde Planifiee - Volets Écologiques'),
('2507909-I09', 'LOG1', 'Planification', '2025-06-29 08:00:00', '2025-06-29 08:00:00', 'USER1', 'cde Planifiee - Volets Sécurisés'),
('2507910-J10', 'LOG1', 'Vitrage', '2025-06-29 09:00:00', '2025-06-29 09:00:00', 'USER2', 'cde Planifiee - Volets Intelligents'),
('2507911-K11', 'LOG1', 'Planification', '2025-06-29 10:00:00', '2025-06-29 10:00:00', 'USER1', 'cde Planifiee - Volets Thermiques'),
('2507912-L12', 'LOG1', 'Planification', '2025-06-29 11:00:00', '2025-06-29 11:00:00', 'USER3', 'cde Planifiee - Volets Anti-Effraction'),
('2507913-M13', 'LOG1', 'Production', '2025-06-29 12:00:00', '2025-06-29 12:00:00', 'USER1', 'cde Planifiee - Volets Acoustiques'),
('2507914-N14', 'LOG1', 'Planification', '2025-06-29 13:00:00', '2025-06-29 13:00:00', 'USER2', 'cde Planifiee - Volets Isolants'),
('2507915-O15', 'LOG1', 'Vitrage', '2025-06-29 14:00:00', '2025-06-29 14:00:00', 'USER1', 'cde Planifiee - Volets Haute Performance'),
('2507916-P16', 'LOG1', 'Planification', '2025-06-29 15:00:00', '2025-06-29 15:00:00', 'USER3', 'cde Planifiee - Volets Résistants'),
('2507917-Q17', 'LOG1', 'Planification', '2025-06-29 16:00:00', '2025-06-29 16:00:00', 'USER1', 'cde Planifiee - Volets Durables'),
('2507918-R18', 'LOG1', 'Production', '2025-06-30 08:00:00', '2025-06-30 08:00:00', 'USER2', 'cde Planifiee - Volets Luxe Premium'),
('2507919-S19', 'LOG1', 'Planification', '2025-06-30 09:00:00', '2025-06-30 09:00:00', 'USER1', 'cde Planifiee - Volets Économiques'),
('2507920-T20', 'LOG1', 'Vitrage', '2025-06-30 10:00:00', '2025-06-30 10:00:00', 'USER3', 'cde Planifiee - Volets Modulaires'),

-- LOGS POUR LES NOUVELLES COMMANDES QUI PASSERONT LE FILTRE
('2508001-V01', 'LOG1', 'Planification', '2025-07-01 08:00:00', '2025-07-01 08:00:00', 'USER1', 'cde Planifiee - Volets Connectés Azure'),
('2508002-W02', 'LOG1', 'Production', '2025-07-01 09:00:00', '2025-07-01 09:00:00', 'USER2', 'cde Planifiee - Volets Solaires Coral'),
('2508003-X03', 'LOG1', 'Vitrage', '2025-07-01 10:00:00', '2025-07-01 10:00:00', 'USER1', 'cde Planifiee - Volets Premium Mint'),
('2508004-Y04', 'LOG1', 'Planification', '2025-07-01 11:00:00', '2025-07-01 11:00:00', 'USER3', 'cde Planifiee - Volets Intelligents Pearl'),
('2508005-Z05', 'LOG1', 'Planification', '2025-07-01 12:00:00', '2025-07-01 12:00:00', 'USER1', 'cde Planifiee - Volets Luxe Gold'),

-- LOGS POUR LES COMMANDES AVEC MAUVAIS STATUTS (mais avec "cde Planifiee")
('2508101-A01', 'LOG1', 'Terminée', '2025-06-15 16:00:00', '2025-06-15 16:00:00', 'USER1', 'cde Planifiee - Commande terminée Steel'),
('2508102-B02', 'LOG1', 'En cours', '2025-06-20 10:00:00', '2025-06-20 10:00:00', 'USER2', 'cde Planifiee - Commande en cours Bronze'),
('2508103-C03', 'LOG1', 'Annulée', '2025-06-18 14:00:00', '2025-06-18 14:00:00', 'USER1', 'cde Planifiee - Commande annulée Silver'),
('2508104-D04', 'LOG1', 'Suspendue', '2025-06-22 11:00:00', '2025-06-22 11:00:00', 'USER3', 'cde Planifiee - Commande suspendue Copper'),

-- LOGS POUR LES COMMANDES SANS "cde Planifiee" (mais avec bons statuts)
('2508201-E01', 'LOG1', 'Planification', '2025-07-02 08:00:00', '2025-07-02 08:00:00', 'USER1', 'cde Planifiee - en attente'),
('2508202-F02', 'LOG1', 'Production', '2025-07-02 09:00:00', '2025-07-02 09:00:00', 'USER2', 'Commande lancée Emerald - production'),
('2508203-G03', 'LOG1', 'Vitrage', '2025-07-02 10:00:00', '2025-07-02 10:00:00', 'USER1', 'Commande vitrage Diamond - en cours'),

-- LOGS POUR LES COMMANDES AVEC MAUVAIS ACCESSOIRES (mais avec "cde Planifiee")
('2508301-H01', 'LOG1', 'Planification', '2025-07-03 08:00:00', '2025-07-03 08:00:00', 'USER1', 'cde Planifiee - Fenêtres Topaz'),
('2508302-I02', 'LOG1', 'Production', '2025-07-03 09:00:00', '2025-07-03 09:00:00', 'USER2', 'cde Planifiee - Portes Onyx'),
('2508303-J03', 'LOG1', 'Vitrage', '2025-07-03 10:00:00', '2025-07-03 10:00:00', 'USER1', 'cde Planifiee - Stores Jade'),

-- Logs pour commandes qui NE DOIVENT PAS apparaître
('2507999-Z00', 'LOG1', 'Terminée', '2025-06-20 16:00:00', '2025-06-20 16:00:00', 'USER1', 'Commande terminée'),
('2508000-Z01', 'LOG1', 'En cours', '2025-06-21 10:00:00', '2025-06-21 10:00:00', 'USER2', 'Commande en cours');

-- Événements pour déterminer la gestion en stock (VR = 1, autres = 0)
INSERT INTO A_Vorgang VALUES
-- Commandes AVEC VR (Gestion en Stock = 1)
('2507748-004', 'VR001', 'Installation Volet', '2025-06-28 08:00:00', '2025-06-28 08:00:00', 'TECH1', 'NOTE1', 'Installation volet roulant PVC', 'INT1', 0),
('2507648-H00', 'VR002', 'Installation Volet', '2025-06-26 09:00:00', '2025-06-26 09:00:00', 'TECH2', 'NOTE2', 'Installation volet ALU motorisé', 'INT2', 0),
('2507837-YG0', 'VR003', 'Installation Volet', '2025-06-27 10:00:00', '2025-06-27 10:00:00', 'TECH3', 'NOTE3', 'Installation volet solaire', 'INT3', 0),
('2507732-H00', 'VR004', 'Installation Volet', '2025-06-26 11:00:00', '2025-06-26 11:00:00', 'TECH1', 'NOTE4', 'Installation motorisation premium', 'INT4', 0),
('2507816-YG0', 'VR005', 'Installation Volet', '2025-06-28 11:00:00', '2025-06-28 11:00:00', 'TECH1', 'NOTE5', 'Installation automatisation', 'INT5', 0),

-- Commandes SANS VR (Gestion en Stock = 0)
('2507298-Y00', 'OP001', 'Opération Standard', '2025-06-20 14:00:00', '2025-06-20 14:00:00', 'TECH1', 'NOTE8', 'Opération standard sans VR', 'INT8', 0),
('2505417-X04', 'ST001', 'Store Standard', '2025-05-15 10:00:00', '2025-05-15 10:00:00', 'TECH2', 'NOTE9', 'Installation store banne', 'INT9', 0),
('2506535-ZP2', 'ST003', 'Store Motorisé', '2025-06-17 14:30:00', '2025-06-17 14:30:00', 'TECH1', 'NOTE12', 'Store motorisé terrasse', 'INT12', 0),
('2505304-U04', 'ST002', 'Store Vénitien', '2025-06-07 12:00:00', '2025-06-07 12:00:00', 'TECH2', 'NOTE11', 'Installation store vénitien', 'INT11', 0),
('2507810-000', 'OP002', 'Opération Design', '2025-06-28 16:00:00', '2025-06-28 16:00:00', 'TECH3', 'NOTE10', 'Design sur mesure', 'INT10', 0);

-- ÉVÉNEMENTS POUR LES NOUVELLES COMMANDES
-- Commandes AVEC VR (Gestion en Stock = 1)
INSERT INTO A_Vorgang VALUES
('2507901-A01', 'VR006', 'Installation Volet', '2025-06-29 08:00:00', '2025-06-29 08:00:00', 'TECH1', 'NOTE6', 'Installation volet ALU premium', 'INT6', 0),
('2507902-B02', 'VR007', 'Installation Volet', '2025-06-29 10:00:00', '2025-06-29 10:00:00', 'TECH2', 'NOTE7', 'Installation volet solaire', 'INT7', 0),
('2507904-D04', 'VR008', 'Installation Volet', '2025-06-29 12:00:00', '2025-06-29 12:00:00', 'TECH3', 'NOTE8', 'Installation motorisation avancée', 'INT8', 0),
('2507906-F06', 'VR009', 'Installation Volet', '2025-06-29 14:00:00', '2025-06-29 14:00:00', 'TECH2', 'NOTE9', 'Installation volet premium', 'INT9', 0),
('2507907-G07', 'VR010', 'Installation Volet', '2025-06-29 15:00:00', '2025-06-29 15:00:00', 'TECH1', 'NOTE10', 'Installation volet connecté', 'INT10', 0),
('2507909-I09', 'VR011', 'Installation Volet', '2025-06-30 08:00:00', '2025-06-30 08:00:00', 'TECH1', 'NOTE11', 'Installation volet sécurisé', 'INT11', 0),
('2507911-K11', 'VR012', 'Installation Volet', '2025-06-30 10:00:00', '2025-06-30 10:00:00', 'TECH1', 'NOTE12', 'Installation volet thermique', 'INT12', 0),
('2507912-L12', 'VR013', 'Installation Volet', '2025-06-30 11:00:00', '2025-06-30 11:00:00', 'TECH3', 'NOTE13', 'Installation anti-effraction', 'INT13', 0),
('2507914-N14', 'VR014', 'Installation Volet', '2025-06-30 13:00:00', '2025-06-30 13:00:00', 'TECH2', 'NOTE14', 'Installation volet isolant', 'INT14', 0),
('2507916-P16', 'VR015', 'Installation Volet', '2025-06-30 15:00:00', '2025-06-30 15:00:00', 'TECH3', 'NOTE15', 'Installation volet résistant', 'INT15', 0),
('2507917-Q17', 'VR016', 'Installation Volet', '2025-06-30 16:00:00', '2025-06-30 16:00:00', 'TECH1', 'NOTE16', 'Installation volet durable', 'INT16', 0),
('2507919-S19', 'VR017', 'Installation Volet', '2025-07-01 09:00:00', '2025-07-01 09:00:00', 'TECH1', 'NOTE17', 'Installation volet économique', 'INT17', 0),

-- Commandes SANS VR (Gestion en Stock = 0)
('2507903-C03', 'OP003', 'Opération Standard', '2025-06-29 11:00:00', '2025-06-29 11:00:00', 'TECH1', 'NOTE18', 'Opération PVC standard', 'INT18', 0),
('2507905-E05', 'ST004', 'Store Design', '2025-06-29 13:00:00', '2025-06-29 13:00:00', 'TECH1', 'NOTE19', 'Installation design premium', 'INT19', 0),
('2507908-H08', 'OP004', 'Opération Écologique', '2025-06-29 16:00:00', '2025-06-29 16:00:00', 'TECH3', 'NOTE20', 'Installation écologique', 'INT20', 0),
('2507910-J10', 'ST005', 'Store Intelligent', '2025-06-30 09:00:00', '2025-06-30 09:00:00', 'TECH2', 'NOTE21', 'Installation intelligente', 'INT21', 0),
('2507913-M13', 'OP005', 'Opération Acoustique', '2025-06-30 12:00:00', '2025-06-30 12:00:00', 'TECH1', 'NOTE22', 'Installation acoustique', 'INT22', 0),
('2507915-O15', 'ST006', 'Store Performance', '2025-06-30 14:00:00', '2025-06-30 14:00:00', 'TECH1', 'NOTE23', 'Installation haute performance', 'INT23', 0),
('2507918-R18', 'OP006', 'Opération Luxe', '2025-07-01 08:00:00', '2025-07-01 08:00:00', 'TECH2', 'NOTE24', 'Installation luxe premium', 'INT24', 0),
('2507920-T20', 'ST007', 'Store Modulaire', '2025-07-01 10:00:00', '2025-07-01 10:00:00', 'TECH3', 'NOTE25', 'Installation modulaire', 'INT25', 0);

-- ÉVÉNEMENTS POUR LES NOUVELLES COMMANDES QUI PASSERONT LE FILTRE
INSERT INTO A_Vorgang VALUES
-- Commandes AVEC VR (Gestion en Stock = 1)
('2508001-V01', 'VR018', 'Installation Volet', '2025-07-02 08:00:00', '2025-07-02 08:00:00', 'TECH1', 'NOTE26', 'Installation volet connecté Azure', 'INT26', 0),
('2508004-Y04', 'VR019', 'Installation Volet', '2025-07-02 11:00:00', '2025-07-02 11:00:00', 'TECH3', 'NOTE27', 'Installation volet intelligent Pearl', 'INT27', 0),
('2508005-Z05', 'VR020', 'Installation Volet', '2025-07-02 12:00:00', '2025-07-02 12:00:00', 'TECH1', 'NOTE28', 'Installation volet luxe Gold', 'INT28', 0),

-- Commandes SANS VR (Gestion en Stock = 0)
('2508002-W02', 'ST008', 'Store Solaire', '2025-07-02 09:00:00', '2025-07-02 09:00:00', 'TECH2', 'NOTE29', 'Installation solaire Coral', 'INT29', 0),
('2508003-X03', 'OP007', 'Opération Premium', '2025-07-02 10:00:00', '2025-07-02 10:00:00', 'TECH1', 'NOTE30', 'Installation premium Mint', 'INT30', 0),

-- ÉVÉNEMENTS POUR LES COMMANDES AVEC MAUVAIS STATUTS
('2508101-A01', 'VR021', 'Installation Volet', '2025-06-16 08:00:00', '2025-06-16 08:00:00', 'TECH1', 'NOTE31', 'Installation terminée Steel', 'INT31', 0),
('2508102-B02', 'OP008', 'Opération Standard', '2025-06-21 10:00:00', '2025-06-21 10:00:00', 'TECH2', 'NOTE32', 'Opération en cours Bronze', 'INT32', 0),
('2508103-C03', 'ST009', 'Store Standard', '2025-06-19 14:00:00', '2025-06-19 14:00:00', 'TECH1', 'NOTE33', 'Installation annulée Silver', 'INT33', 0),
('2508104-D04', 'VR022', 'Installation Volet', '2025-06-23 11:00:00', '2025-06-23 11:00:00', 'TECH3', 'NOTE34', 'Installation suspendue Copper', 'INT34', 0),

-- ÉVÉNEMENTS POUR LES COMMANDES SANS "cde Planifiee"
('2508201-E01', 'VR023', 'Installation Volet', '2025-07-03 08:00:00', '2025-07-03 08:00:00', 'TECH1', 'NOTE35', 'Installation volet Ruby', 'INT35', 0),
('2508202-F02', 'VR024', 'Installation Volet', '2025-07-03 09:00:00', '2025-07-03 09:00:00', 'TECH2', 'NOTE36', 'Installation motorisée Emerald', 'INT36', 0),
('2508203-G03', 'OP009', 'Opération Premium', '2025-07-03 10:00:00', '2025-07-03 10:00:00', 'TECH1', 'NOTE37', 'Installation premium Diamond', 'INT37', 0),

-- ÉVÉNEMENTS POUR LES COMMANDES AVEC MAUVAIS ACCESSOIRES
('2508301-H01', 'FEN001', 'Installation Fenêtre', '2025-07-04 08:00:00', '2025-07-04 08:00:00', 'TECH1', 'NOTE38', 'Installation fenêtre Topaz', 'INT38', 0),
('2508302-I02', 'POR001', 'Installation Porte', '2025-07-04 09:00:00', '2025-07-04 09:00:00', 'TECH2', 'NOTE39', 'Installation porte Onyx', 'INT39', 0),
('2508303-J03', 'STO001', 'Installation Store', '2025-07-04 10:00:00', '2025-07-04 10:00:00', 'TECH1', 'NOTE40', 'Installation store Jade', 'INT40', 0);

-- Articles (optionnel pour la requête)
INSERT INTO P_Artikel VALUES
('ART001', '2507748-004', 1, 'VR_PVC_STANDARD', 1200, 1000, 50),
('ART002', '2507648-H00', 1, 'VR_ALU_MOTORISE', 1500, 1200, 60),
('ART003', '2507298-Y00', 1, 'VR_PVC_ECO', 900, 800, 45),
('ART004', '2507837-YG0', 1, 'VR_SOLAIRE_PREMIUM', 1400, 1100, 70),
('ART005', '2507732-H00', 1, 'VR_MOTORISE_PREMIUM', 1600, 1300, 65),

-- ARTICLES POUR LES NOUVELLES COMMANDES
('ART006', '2507901-A01', 1, 'VR_ALU_PREMIUM', 1400, 1200, 55),
('ART007', '2507902-B02', 1, 'VR_SOLAIRE_PREMIUM', 1500, 1100, 75),
('ART008', '2507903-C03', 1, 'VR_PVC_STANDARD', 1000, 900, 45),
('ART009', '2507904-D04', 1, 'VR_MOTORISE_ALU', 1600, 1400, 70),
('ART010', '2507905-E05', 1, 'VR_DESIGN_PREMIUM', 1700, 1500, 80),
('ART011', '2507906-F06', 1, 'VR_PREMIUM_ALU', 1800, 1600, 85),
('ART012', '2507907-G07', 1, 'VR_CONNECTE_IOT', 1900, 1700, 90),
('ART013', '2507908-H08', 1, 'VR_ECOLOGIQUE', 1300, 1100, 60),
('ART014', '2507909-I09', 1, 'VR_SECURISE', 1650, 1450, 75),
('ART015', '2507910-J10', 1, 'VR_INTELLIGENT', 1750, 1550, 85),
('ART016', '2507911-K11', 1, 'VR_THERMIQUE', 1550, 1350, 70),
('ART017', '2507912-L12', 1, 'VR_ANTI_EFFRACTION', 2000, 1800, 95),
('ART018', '2507913-M13', 1, 'VR_ACOUSTIQUE', 1650, 1450, 75),
('ART019', '2507914-N14', 1, 'VR_ISOLANT', 1450, 1250, 65),
('ART020', '2507915-O15', 1, 'VR_HAUTE_PERFORMANCE', 1850, 1650, 90),
('ART021', '2507916-P16', 1, 'VR_RESISTANT', 1400, 1200, 60),
('ART022', '2507917-Q17', 1, 'VR_DURABLE', 1500, 1300, 65),
('ART023', '2507918-R18', 1, 'VR_LUXE_PREMIUM', 2200, 2000, 100),
('ART024', '2507919-S19', 1, 'VR_ECONOMIQUE', 1100, 900, 50),
('ART025', '2507920-T20', 1, 'VR_MODULAIRE', 1600, 1400, 75);

-- ARTICLES POUR LES NOUVELLES COMMANDES QUI PASSERONT LE FILTRE
INSERT INTO P_Artikel VALUES
('ART026', '2508001-V01', 1, 'VR_CONNECTE_AZURE', 1900, 1700, 85),
('ART027', '2508002-W02', 1, 'VR_SOLAIRE_CORAL', 1550, 1350, 70),
('ART028', '2508003-X03', 1, 'VR_PREMIUM_MINT', 1950, 1750, 90),
('ART029', '2508004-Y04', 1, 'VR_INTELLIGENT_PEARL', 1850, 1650, 85),
('ART030', '2508005-Z05', 1, 'VR_LUXE_GOLD', 2300, 2100, 110),

-- ARTICLES POUR LES COMMANDES AVEC MAUVAIS STATUTS
('ART031', '2508101-A01', 1, 'VR_STANDARD_STEEL', 1200, 1000, 55),
('ART032', '2508102-B02', 1, 'VR_ALU_BRONZE', 1400, 1200, 60),
('ART033', '2508103-C03', 1, 'VR_PVC_SILVER', 1100, 900, 50),
('ART034', '2508104-D04', 1, 'VR_DESIGN_COPPER', 1650, 1450, 75),

-- ARTICLES POUR LES COMMANDES SANS "cde Planifiee"
('ART035', '2508201-E01', 1, 'VR_ROULANT_RUBY', 1350, 1150, 60),
('ART036', '2508202-F02', 1, 'VR_MOTORISE_EMERALD', 1700, 1500, 80),
('ART037', '2508203-G03', 1, 'VR_PREMIUM_DIAMOND', 2000, 1800, 95),

-- ARTICLES POUR LES COMMANDES AVEC MAUVAIS ACCESSOIRES
('ART038', '2508301-H01', 1, 'FENETRE_TOPAZ', 800, 600, 30),
('ART039', '2508302-I02', 1, 'PORTE_ONYX', 1200, 1000, 40),
('ART040', '2508303-J03', 1, 'STORE_JADE', 600, 400, 25);

-- Accessoires CRUCIAUX - Doivent correspondre aux critères
INSERT INTO P_Zubeh VALUES
-- Codes SOP (Coffres standards) - CORRESPONDANT AUX CRITÈRES
('2507748-004', 1, 1, 1, 'SOP PVC N30', 'Coffre standard PVC N30', 1),
('2507648-H00', 1, 1, 1, 'SOP ALU H30', 'Coffre standard ALU H30', 1),
('2507298-Y00', 1, 1, 1, 'SOP ALU A30-F21', 'Coffre ALU A30-F21', 1),
('2507837-YG0', 1, 1, 1, 'SOP ALU GAL', 'Coffre ALU galvanisé', 1),
('2507732-H00', 1, 1, 1, 'SOP ALU H30', 'Coffre ALU H30 motorisé', 1),
('2507816-YG0', 1, 1, 1, 'SOP ALU GAL', 'Coffre ALU GAL automatique', 1),
('2507810-000', 1, 1, 1, 'SOP ALU N30', 'Coffre ALU N30 design', 1),

-- Codes S P (Coffres sur mesure) - CORRESPONDANT AUX CRITÈRES
('2505417-X04', 1, 1, 1, 'S P 6104+T', 'Coffre sur mesure X 6104+T', 1),
('2505304-U04', 1, 1, 1, 'S P ALU ASK L F', 'Coffre sur mesure ALU ASK L F', 1),

-- Codes S D, S Q, S T, S TAB, S TN (autres types de coffres)
('2506535-ZP2', 1, 1, 1, 'S D ALU H30', 'Coffre design ALU H30', 1),

-- ACCESSOIRES POUR LES NOUVELLES COMMANDES
('2507901-A01', 1, 1, 1, 'SOP ALU H30', 'Coffre standard ALU H30 premium', 1),
('2507902-B02', 1, 1, 1, 'SOP SOLAIRE GAL', 'Coffre solaire galvanisé', 1),
('2507903-C03', 1, 1, 1, 'S P PVC C30', 'Coffre sur mesure PVC C30', 1),
('2507904-D04', 1, 1, 1, 'SOP ALU MOTOR', 'Coffre motorisé ALU', 1),
('2507905-E05', 1, 1, 1, 'S D DESIGN PRE', 'Coffre design premium', 1),
('2507906-F06', 1, 1, 1, 'SOP ALU PREM', 'Coffre premium ALU', 1),
('2507907-G07', 1, 1, 1, 'S Q CONNECT', 'Coffre connecté IoT', 1),
('2507908-H08', 1, 1, 1, 'S P ECO ALU', 'Coffre écologique sur mesure', 1),
('2507909-I09', 1, 1, 1, 'SOP SECURE', 'Coffre sécurisé standard', 1),
('2507910-J10', 1, 1, 1, 'S T INTELL', 'Coffre intelligent sur mesure', 1),
('2507911-K11', 1, 1, 1, 'SOP THERM', 'Coffre thermique standard', 1),
('2507912-L12', 1, 1, 1, 'S TAB ANTI-EFF', 'Coffre anti-effraction', 1),
('2507913-M13', 1, 1, 1, 'S P ACOUST', 'Coffre acoustique sur mesure', 1),
('2507914-N14', 1, 1, 1, 'SOP ISOLANT', 'Coffre isolant standard', 1),
('2507915-O15', 1, 1, 1, 'S TN PERFORM', 'Coffre haute performance', 1),
('2507916-P16', 1, 1, 1, 'SOP RESIST', 'Coffre résistant standard', 1),
('2507917-Q17', 1, 1, 1, 'SOP DURABLE', 'Coffre durable standard', 1),
('2507918-R18', 1, 1, 1, 'S P LUXE PREM', 'Coffre luxe premium sur mesure', 1),
('2507919-S19', 1, 1, 1, 'SOP ECO STAND', 'Coffre économique standard', 1),
('2507920-T20', 1, 1, 1, 'S D MODULAIRE', 'Coffre modulaire design', 1),

-- ACCESSOIRES POUR LES NOUVELLES COMMANDES QUI PASSERONT LE FILTRE
('2508001-V01', 1, 1, 1, 'SOP CONNECTE', 'Coffre connecté Azure', 1),
('2508002-W02', 1, 1, 1, 'S P SOLAIRE', 'Coffre solaire sur mesure Coral', 1),
('2508003-X03', 1, 1, 1, 'S Q PREMIUM', 'Coffre premium Mint', 1),
('2508004-Y04', 1, 1, 1, 'S T INTELL PEARL', 'Coffre intelligent Pearl', 1),
('2508005-Z05', 1, 1, 1, 'S TAB LUXE GOLD', 'Coffre luxe Gold', 1),

-- ACCESSOIRES POUR LES COMMANDES AVEC MAUVAIS STATUTS (mais bons codes)
('2508101-A01', 1, 1, 1, 'SOP STEEL', 'Coffre standard Steel', 1),
('2508102-B02', 1, 1, 1, 'S P BRONZE', 'Coffre sur mesure Bronze', 1),
('2508103-C03', 1, 1, 1, 'S D SILVER', 'Coffre design Silver', 1),
('2508104-D04', 1, 1, 1, 'S TN COPPER', 'Coffre spécial Copper', 1),

-- ACCESSOIRES POUR LES COMMANDES SANS "cde Planifiee" (mais bons codes)
('2508201-E01', 1, 1, 1, 'SOP RUBY', 'Coffre standard Ruby', 1),
('2508202-F02', 1, 1, 1, 'S P EMERALD', 'Coffre sur mesure Emerald', 1),
('2508203-G03', 1, 1, 1, 'S Q DIAMOND', 'Coffre premium Diamond', 1),

-- ACCESSOIRES POUR LES COMMANDES AVEC MAUVAIS ACCESSOIRES (codes qui ne passent pas le filtre)
('2508301-H01', 1, 1, 1, 'FEN TOPAZ', 'Fenêtre standard Topaz', 1),
('2508302-I02', 1, 1, 1, 'POR ONYX', 'Porte d''entrée Onyx', 1),
('2508303-J03', 1, 1, 1, 'STO JADE', 'Store vénitien Jade', 1),

-- Codes qui ne correspondent PAS aux critères (pour tester le filtrage)
('2507648-H00', 2, 1, 1, 'FEN001', 'Fenêtre standard', 1),
('2507298-Y00', 2, 1, 1, 'POR001', 'Porte d''entrée', 1),
('2507999-Z00', 1, 1, 1, 'VR_STANDARD', 'Volet standard', 1), -- Commande terminée, ne doit pas apparaître
('2508000-Z01', 1, 1, 1, 'SOP_TEST', 'Coffre test', 1); -- Commande en cours, ne doit pas apparaître

-- Informations additionnelles
INSERT INTO A_KopfFreie VALUES
('2507748-004', 1, 1, 'Info1', 'Val1', '1', '2025-06-27', '2025-07-15'),
('2507648-H00', 1, 1, 'Info2', 'Val2', '2', '2025-06-25', '2025-07-20'),
('2507298-Y00', 1, 1, 'Info3', 'Val3', '1', '2025-06-19', '2025-07-10'),
('2507837-YG0', 1, 1, 'Info4', 'Val4', '1', '2025-06-26', '2025-07-25'),
('2507732-H00', 1, 1, 'Info5', 'Val5', '2', '2025-06-25', '2025-07-30'),
('2505417-X04', 1, 1, 'Info6', 'Val6', '1', '2025-05-14', '2025-06-15'),
('2506535-ZP2', 1, 1, 'Info7', 'Val7', '2', '2025-06-16', '2025-07-20'),
('2505304-U04', 1, 1, 'Info8', 'Val8', '1', '2025-06-06', '2025-07-01'),
('2507816-YG0', 1, 1, 'Info9', 'Val9', '2', '2025-06-27', '2025-08-01'),
('2507810-000', 1, 1, 'Info10', 'Val10', '1', '2025-06-27', '2025-08-05');

-- INFORMATIONS ADDITIONNELLES POUR LES NOUVELLES COMMANDES
INSERT INTO A_KopfFreie VALUES
('2507901-A01', 1, 1, 'Info11', 'Val11', '1', '2025-06-28', '2025-08-10'),
('2507902-B02', 1, 1, 'Info12', 'Val12', '2', '2025-06-28', '2025-08-15'),
('2507903-C03', 1, 1, 'Info13', 'Val13', '1', '2025-06-28', '2025-07-25'),
('2507904-D04', 1, 1, 'Info14', 'Val14', '3', '2025-06-28', '2025-08-20'),
('2507905-E05', 1, 1, 'Info15', 'Val15', '1', '2025-06-28', '2025-08-25'),
('2507906-F06', 1, 1, 'Info16', 'Val16', '2', '2025-06-28', '2025-09-01'),
('2507907-G07', 1, 1, 'Info17', 'Val17', '1', '2025-06-28', '2025-09-05'),
('2507908-H08', 1, 1, 'Info18', 'Val18', '3', '2025-06-28', '2025-08-30'),
('2507909-I09', 1, 1, 'Info19', 'Val19', '1', '2025-06-29', '2025-09-10'),
('2507910-J10', 1, 1, 'Info20', 'Val20', '2', '2025-06-29', '2025-09-15'),
('2507911-K11', 1, 1, 'Info21', 'Val21', '1', '2025-06-29', '2025-09-20'),
('2507912-L12', 1, 1, 'Info22', 'Val22', '3', '2025-06-29', '2025-10-01'),
('2507913-M13', 1, 1, 'Info23', 'Val23', '1', '2025-06-29', '2025-09-25'),
('2507914-N14', 1, 1, 'Info24', 'Val24', '2', '2025-06-29', '2025-09-30'),
('2507915-O15', 1, 1, 'Info25', 'Val25', '1', '2025-06-29', '2025-10-05'),
('2507916-P16', 1, 1, 'Info26', 'Val26', '3', '2025-06-29', '2025-10-10'),
('2507917-Q17', 1, 1, 'Info27', 'Val27', '1', '2025-06-29', '2025-10-15'),
('2507918-R18', 1, 1, 'Info28', 'Val28', '2', '2025-06-30', '2025-10-20'),
('2507919-S19', 1, 1, 'Info29', 'Val29', '1', '2025-06-30', '2025-10-25'),
('2507920-T20', 1, 1, 'Info30', 'Val30', '3', '2025-06-30', '2025-11-01');

-- INFORMATIONS ADDITIONNELLES POUR LES NOUVELLES COMMANDES QUI PASSERONT LE FILTRE
INSERT INTO A_KopfFreie VALUES
('2508001-V01', 1, 1, 'Info31', 'Val31', '1', '2025-07-01', '2025-11-15'),
('2508002-W02', 1, 1, 'Info32', 'Val32', '2', '2025-07-01', '2025-11-20'),
('2508003-X03', 1, 1, 'Info33', 'Val33', '1', '2025-07-01', '2025-11-25'),
('2508004-Y04', 1, 1, 'Info34', 'Val34', '3', '2025-07-01', '2025-12-01'),
('2508005-Z05', 1, 1, 'Info35', 'Val35', '1', '2025-07-01', '2025-12-05');

-- INFORMATIONS POUR LES COMMANDES AVEC MAUVAIS STATUTS
('2508101-A01', 1, 1, 'Info36', 'Val36', '1', '2025-06-15', '2025-08-01'),
('2508102-B02', 1, 1, 'Info37', 'Val37', '2', '2025-06-20', '2025-08-15'),
('2508103-C03', 1, 1, 'Info38', 'Val38', '1', '2025-06-18', '2025-08-10'),
('2508104-D04', 1, 1, 'Info39', 'Val39', '3', '2025-06-22', '2025-09-01');

-- INFORMATIONS POUR LES COMMANDES SANS "cde Planifiee"
('2508201-E01', 1, 1, 'Info40', 'Val40', '1', '2025-07-02', '2025-12-10'),
('2508202-F02', 1, 1, 'Info41', 'Val41', '2', '2025-07-02', '2025-12-15'),
('2508203-G03', 1, 1, 'Info42', 'Val42', '1', '2025-07-02', '2025-12-20');

-- INFORMATIONS POUR LES COMMANDES AVEC MAUVAIS ACCESSOIRES
('2508301-H01', 1, 1, 'Info43', 'Val43', '1', '2025-07-03', '2025-12-25'),
('2508302-I02', 1, 1, 'Info44', 'Val44', '2', '2025-07-03', '2025-12-30'),
('2508303-J03', 1, 1, 'Info45', 'Val45', '1', '2025-07-03', '2026-01-05');

-- Création des index pour optimiser les performances
CREATE INDEX idx_aufstatus ON A_Kopf(AufStatus);
CREATE INDEX idx_aunummer ON A_Kopf(AuNummer);
CREATE INDEX idx_aualpha ON A_Kopf(AuAlpha);
CREATE INDEX idx_zcode ON P_Zubeh(ZCode);
CREATE INDEX idx_notiz ON A_Logbuch(Notiz(255));
CREATE INDEX idx_vorgang_nummer ON A_Vorgang(Nummer);
CREATE INDEX idx_logbuch_id_kopf ON A_Logbuch(ID_A_Kopf);
CREATE INDEX idx_zubeh_id_kopf ON P_Zubeh(ID_A_Kopf);
CREATE INDEX idx_vorgang_id_kopf ON A_Vorgang(ID_A_Kopf);
CREATE INDEX idx_kopf_id ON A_Kopf(ID);

-- Vue pour faciliter les requêtes de volets roulants
CREATE VIEW IF NOT EXISTS vue_commandes_volets AS
SELECT 
    Cde.AuNummer as numero_commande,
    Cde.AuAlpha as extension, 
    Cde.AufStatus as status,
    DATE(Logb.Datum) as date_modification,
    a.ZCode as coffre,
    CASE WHEN Vorgang.Nummer LIKE '%VR%' THEN 1 ELSE 0 END AS gestion_en_stock,
    Cde.Techniker as technicien,
    Cde.A_VorMwSt as prix_ht
FROM A_Kopf AS Cde
LEFT JOIN A_KopfFreie AS cf ON Cde.ID = cf.ID_A_Kopf
LEFT JOIN A_Logbuch AS Logb ON Cde.ID = Logb.ID_A_Kopf
LEFT JOIN P_Zubeh AS a ON Cde.ID = a.ID_A_Kopf
LEFT JOIN P_Artikel AS Paramgen ON Cde.ID = Paramgen.ID_A_Kopf
LEFT JOIN A_Vorgang AS Vorgang ON Cde.ID = Vorgang.ID_A_Kopf
WHERE 
    Logb.Notiz LIKE '%cde Planifiee%'
    AND (Cde.AufStatus LIKE '%Planifiee%' OR Cde.AufStatus LIKE '%lancer en prod%' OR Cde.AufStatus LIKE '%vitrage%')
    AND (a.ZCode LIKE 'SOP%' OR a.ZCode LIKE 'S P %' OR a.ZCode LIKE 'S D %' OR a.ZCode LIKE 'S Q %' OR a.ZCode LIKE 'S T %' OR a.ZCode LIKE 'S TAB %' OR a.ZCode LIKE 'S TN %');
