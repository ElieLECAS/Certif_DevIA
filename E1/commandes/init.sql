-- Création de l'utilisateur et attribution des droits
CREATE USER IF NOT EXISTS 'fenetre_user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'fenetre_user'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

-- Création de la base de données
CREATE DATABASE IF NOT EXISTS db_commandes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Utilisation de la base de données
USE db_commandes;

-- Table a_kopf (Informations principales des commandes)
CREATE TABLE IF NOT EXISTS a_kopf (
    id VARCHAR(32) PRIMARY KEY,
    auftragstyp SMALLINT,
    aunummer INT,
    aualpha VARCHAR(5),
    kundennr VARCHAR(15),
    kundenbez VARCHAR(15),
    kommission VARCHAR(50) COMMENT 'Affaire',
    bauvorhaben VARCHAR(50),
    auftragsart SMALLINT,
    fsystemgrp SMALLINT,
    aufstatus VARCHAR(15) COMMENT 'Statut',
    techniker VARCHAR(15) COMMENT 'Technicien',
    a_vormwst DECIMAL(15,2) COMMENT 'Prix HT',
    UNIQUE KEY unique_commande (auftragstyp, aunummer, aualpha)
) COMMENT 'Table principale des commandes';

-- Données pour a_kopf
INSERT INTO a_kopf VALUES
('CMD001', 1, 230001, 'A', 'CLI001', 'DUPONT', 'Rénovation Maison', 'Projet Dupont', 1, 1, 'Planifiée', 'TECH1', 15000.50),
('CMD002', 1, 230002, 'B', 'CLI002', 'MARTIN', 'Construction Neuve', 'Villa Martin', 1, 2, 'En production', 'TECH2', 25000.75),
('CMD003', 1, 230003, 'A', 'CLI003', 'DUBOIS', 'Rénovation Appart', 'Appart Dubois', 1, 1, 'Terminée', 'TECH1', 8500.25),
('CMD004', 1, 230004, 'C', 'CLI004', 'PETIT', 'Extension', 'Extension Petit', 1, 3, 'En attente', 'TECH3', 12000.00),
('CMD005', 1, 230005, 'A', 'CLI005', 'BERNARD', 'Installation VR', 'Maison Bernard', 1, 1, 'Planifiée', 'TECH1', 3500.00),
('CMD006', 1, 230006, 'A', 'CLI006', 'THOMAS', 'Volets Roulants', 'Maison Thomas', 1, 1, 'Planifiée', 'TECH1', 4500.00),
('CMD007', 1, 230007, 'B', 'CLI007', 'RICHARD', 'Fenêtres', 'Appart Richard', 1, 1, 'En attente', 'TECH2', 6000.00),
('CMD008', 1, 230008, 'A', 'CLI008', 'DURAND', 'Volets', 'Villa Durand', 1, 1, 'Planifiée', 'TECH1', 5500.00),
('CMD009', 1, 230009, 'C', 'CLI009', 'MOREAU', 'Store', 'Maison Moreau', 1, 1, 'En production', 'TECH3', 2500.00),
('CMD010', 1, 230010, 'A', 'CLI010', 'LAURENT', 'Volets Auto', 'Appart Laurent', 1, 1, 'Planifiée', 'TECH1', 7500.00),
-- Nouvelles commandes (40 de plus)
('CMD011', 1, 230011, 'A', 'CLI011', 'SIMON', 'Fenêtres PVC', 'Maison Simon', 1, 1, 'En attente', 'TECH2', 9500.00),
('CMD012', 1, 230012, 'B', 'CLI012', 'MICHEL', 'Volets Solaires', 'Villa Michel', 1, 1, 'Planifiée', 'TECH1', 8500.00),
('CMD013', 1, 230013, 'A', 'CLI013', 'LEROY', 'Store Banne', 'Terrasse Leroy', 1, 2, 'En production', 'TECH3', 3000.00),
('CMD014', 1, 230014, 'C', 'CLI014', 'ROUX', 'Fenêtres ALU', 'Appart Roux', 1, 1, 'En attente', 'TECH2', 12000.00),
('CMD015', 1, 230015, 'A', 'CLI015', 'DAVID', 'Volets Auto', 'Maison David', 1, 1, 'Planifiée', 'TECH1', 6500.00),
('CMD016', 1, 230016, 'B', 'CLI016', 'BERTRAND', 'Stores Vénitiens', 'Bureau Bertrand', 1, 3, 'En production', 'TECH3', 4000.00),
('CMD017', 1, 230017, 'A', 'CLI017', 'MOREL', 'Volets Roulants', 'Villa Morel', 1, 1, 'Planifiée', 'TECH1', 7500.00),
('CMD018', 1, 230018, 'C', 'CLI018', 'FOURNIER', 'Fenêtres', 'Maison Fournier', 1, 2, 'En attente', 'TECH2', 15000.00),
('CMD019', 1, 230019, 'A', 'CLI019', 'GIRARD', 'Store Motorisé', 'Terrasse Girard', 1, 1, 'En production', 'TECH3', 2500.00),
('CMD020', 1, 230020, 'B', 'CLI020', 'BONNET', 'Volets Battants', 'Appart Bonnet', 1, 1, 'Terminée', 'TECH1', 4500.00),
('CMD021', 1, 230021, 'A', 'CLI021', 'BLANC', 'Stores Enrouleurs', 'Bureau Blanc', 1, 2, 'En attente', 'TECH2', 3500.00),
('CMD022', 1, 230022, 'C', 'CLI022', 'GUERIN', 'Volets Roulants', 'Villa Guerin', 1, 1, 'Planifiée', 'TECH1', 8500.00),
('CMD023', 1, 230023, 'A', 'CLI023', 'BOYER', 'Fenêtres PVC', 'Maison Boyer', 1, 3, 'En production', 'TECH3', 11000.00),
('CMD024', 1, 230024, 'B', 'CLI024', 'GARNIER', 'Store Banne', 'Terrasse Garnier', 1, 1, 'En attente', 'TECH2', 2800.00),
('CMD025', 1, 230025, 'A', 'CLI025', 'CHEVALIER', 'Volets Auto', 'Appart Chevalier', 1, 1, 'Planifiée', 'TECH1', 6500.00),
('CMD026', 1, 230026, 'C', 'CLI026', 'FRANCOIS', 'Stores Vénitiens', 'Bureau Francois', 1, 2, 'En production', 'TECH3', 3800.00),
('CMD027', 1, 230027, 'A', 'CLI027', 'LEGRAND', 'Volets Roulants', 'Maison Legrand', 1, 1, 'En attente', 'TECH2', 7200.00),
('CMD028', 1, 230028, 'B', 'CLI028', 'GAUTHIER', 'Fenêtres ALU', 'Villa Gauthier', 1, 1, 'Planifiée', 'TECH1', 13500.00),
('CMD029', 1, 230029, 'A', 'CLI029', 'GARCIA', 'Store Motorisé', 'Terrasse Garcia', 1, 3, 'En production', 'TECH3', 2900.00),
('CMD030', 1, 230030, 'C', 'CLI030', 'PERRIN', 'Volets Battants', 'Appart Perrin', 1, 1, 'Terminée', 'TECH1', 4800.00),
('CMD031', 1, 230031, 'A', 'CLI031', 'ROBIN', 'Stores Enrouleurs', 'Bureau Robin', 1, 2, 'En attente', 'TECH2', 3200.00),
('CMD032', 1, 230032, 'B', 'CLI032', 'CLEMENT', 'Volets Roulants', 'Villa Clement', 1, 1, 'Planifiée', 'TECH1', 8800.00),
('CMD033', 1, 230033, 'A', 'CLI033', 'MORIN', 'Fenêtres PVC', 'Maison Morin', 1, 1, 'En production', 'TECH3', 10500.00),
('CMD034', 1, 230034, 'C', 'CLI034', 'NICOLAS', 'Store Banne', 'Terrasse Nicolas', 1, 2, 'En attente', 'TECH2', 3100.00),
('CMD035', 1, 230035, 'A', 'CLI035', 'HENRY', 'Volets Auto', 'Appart Henry', 1, 1, 'Planifiée', 'TECH1', 6800.00),
('CMD036', 1, 230036, 'B', 'CLI036', 'ANDRE', 'Stores Vénitiens', 'Bureau Andre', 1, 3, 'En production', 'TECH3', 4200.00),
('CMD037', 1, 230037, 'A', 'CLI037', 'GAUTIER', 'Volets Roulants', 'Maison Gautier', 1, 1, 'En attente', 'TECH2', 7800.00),
('CMD038', 1, 230038, 'C', 'CLI038', 'ROCHE', 'Fenêtres ALU', 'Villa Roche', 1, 1, 'Planifiée', 'TECH1', 14000.00),
('CMD039', 1, 230039, 'A', 'CLI039', 'ARNAUD', 'Store Motorisé', 'Terrasse Arnaud', 1, 2, 'En production', 'TECH3', 2700.00),
('CMD040', 1, 230040, 'B', 'CLI040', 'VIDAL', 'Volets Battants', 'Appart Vidal', 1, 1, 'Terminée', 'TECH1', 5100.00),
('CMD041', 1, 230041, 'A', 'CLI041', 'BOUVIER', 'Stores Enrouleurs', 'Bureau Bouvier', 1, 3, 'En attente', 'TECH2', 3400.00),
('CMD042', 1, 230042, 'C', 'CLI042', 'RENAUD', 'Volets Roulants', 'Villa Renaud', 1, 1, 'Planifiée', 'TECH1', 9100.00),
('CMD043', 1, 230043, 'A', 'CLI043', 'SCHMITT', 'Fenêtres PVC', 'Maison Schmitt', 1, 1, 'En production', 'TECH3', 11500.00),
('CMD044', 1, 230044, 'B', 'CLI044', 'ROY', 'Store Banne', 'Terrasse Roy', 1, 2, 'En attente', 'TECH2', 3300.00),
('CMD045', 1, 230045, 'A', 'CLI045', 'LEROUX', 'Volets Auto', 'Appart Leroux', 1, 1, 'Planifiée', 'TECH1', 7100.00),
('CMD046', 1, 230046, 'C', 'CLI046', 'COLIN', 'Stores Vénitiens', 'Bureau Colin', 1, 3, 'En production', 'TECH3', 4400.00),
('CMD047', 1, 230047, 'A', 'CLI047', 'VIDAL', 'Volets Roulants', 'Maison Vidal', 1, 1, 'En attente', 'TECH2', 8100.00),
('CMD048', 1, 230048, 'B', 'CLI048', 'CARON', 'Fenêtres ALU', 'Villa Caron', 1, 1, 'Planifiée', 'TECH1', 14500.00),
('CMD049', 1, 230049, 'A', 'CLI049', 'PICARD', 'Store Motorisé', 'Terrasse Picard', 1, 2, 'En production', 'TECH3', 2600.00),
('CMD050', 1, 230050, 'C', 'CLI050', 'GERARD', 'Volets Battants', 'Appart Gerard', 1, 1, 'Terminée', 'TECH1', 5300.00);

-- Table a_logbuch (Logs des commandes)
CREATE TABLE IF NOT EXISTS a_logbuch (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_a_kopf VARCHAR(32),
    code VARCHAR(15),
    bezeichnung VARCHAR(50),
    datum DATETIME,
    zeit DATETIME,
    benutzer VARCHAR(50),
    notiz TEXT,
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
) COMMENT 'Logs des commandes';

-- Données pour a_logbuch
INSERT INTO a_logbuch (id_a_kopf, code, bezeichnung, datum, zeit, benutzer, notiz) VALUES
('CMD001', 'LOG1', 'Création', '2023-12-01 09:00:00', '2023-12-01 09:00:00', 'USER1', 'cde Planifiée'),
('CMD001', 'LOG2', 'Modification', '2023-12-02 10:30:00', '2023-12-02 10:30:00', 'USER2', 'cde Planifiée'),
('CMD002', 'LOG1', 'Création', '2023-12-03 14:15:00', '2023-12-03 14:15:00', 'USER1', 'cde Planifiée'),
('CMD003', 'LOG1', 'Création', '2023-12-04 11:20:00', '2023-12-04 11:20:00', 'USER3', 'cde Planifiée'),
('CMD005', 'LOG1', 'Création', '2023-12-05 15:30:00', '2023-12-05 15:30:00', 'USER1', 'cde Planifiée'),
('CMD006', 'LOG1', 'Création', '2023-12-06 09:00:00', '2023-12-06 09:00:00', 'USER1', 'cde Planifiée'),
('CMD007', 'LOG1', 'Création', '2023-12-07 10:00:00', '2023-12-07 10:00:00', 'USER2', 'En attente de validation'),
('CMD008', 'LOG1', 'Création', '2023-12-08 11:00:00', '2023-12-08 11:00:00', 'USER1', 'cde Planifiée'),
('CMD009', 'LOG1', 'Création', '2023-12-09 14:00:00', '2023-12-09 14:00:00', 'USER3', 'cde Planifiée'),
('CMD010', 'LOG1', 'Création', '2023-12-10 15:00:00', '2023-12-10 15:00:00', 'USER1', 'cde en attente'),
-- Nouvelles entrées de log
('CMD012', 'LOG1', 'Création', '2023-12-11 09:00:00', '2023-12-11 09:00:00', 'USER1', 'cde Planifiée'),
('CMD015', 'LOG1', 'Création', '2023-12-12 10:00:00', '2023-12-12 10:00:00', 'USER2', 'cde Planifiée'),
('CMD017', 'LOG1', 'Création', '2023-12-13 11:00:00', '2023-12-13 11:00:00', 'USER1', 'cde Planifiée'),
('CMD022', 'LOG1', 'Création', '2023-12-14 14:00:00', '2023-12-14 14:00:00', 'USER3', 'cde Planifiée'),
('CMD025', 'LOG1', 'Création', '2023-12-15 15:00:00', '2023-12-15 15:00:00', 'USER1', 'cde Planifiée'),
('CMD028', 'LOG1', 'Création', '2023-12-16 09:00:00', '2023-12-16 09:00:00', 'USER2', 'cde Planifiée'),
('CMD032', 'LOG1', 'Création', '2023-12-17 10:00:00', '2023-12-17 10:00:00', 'USER1', 'cde Planifiée'),
('CMD035', 'LOG1', 'Création', '2023-12-18 11:00:00', '2023-12-18 11:00:00', 'USER3', 'cde Planifiée'),
('CMD042', 'LOG1', 'Création', '2023-12-19 14:00:00', '2023-12-19 14:00:00', 'USER1', 'cde Planifiée'),
('CMD045', 'LOG1', 'Création', '2023-12-20 15:00:00', '2023-12-20 15:00:00', 'USER2', 'cde Planifiée'),
-- Autres commandes avec différents statuts
('CMD011', 'LOG1', 'Création', '2023-12-21 09:00:00', '2023-12-21 09:00:00', 'USER1', 'En attente de validation'),
('CMD013', 'LOG1', 'Création', '2023-12-22 10:00:00', '2023-12-22 10:00:00', 'USER2', 'En cours de traitement'),
('CMD014', 'LOG1', 'Création', '2023-12-23 11:00:00', '2023-12-23 11:00:00', 'USER3', 'En attente client'),
('CMD016', 'LOG1', 'Création', '2023-12-24 14:00:00', '2023-12-24 14:00:00', 'USER1', 'En production'),
('CMD018', 'LOG1', 'Création', '2023-12-25 15:00:00', '2023-12-25 15:00:00', 'USER2', 'En attente de validation'),
('CMD019', 'LOG1', 'Création', '2023-12-26 09:00:00', '2023-12-26 09:00:00', 'USER3', 'En cours de traitement'),
('CMD020', 'LOG1', 'Création', '2023-12-27 10:00:00', '2023-12-27 10:00:00', 'USER1', 'Terminée'),
('CMD021', 'LOG1', 'Création', '2023-12-28 11:00:00', '2023-12-28 11:00:00', 'USER2', 'En attente client'),
('CMD023', 'LOG1', 'Création', '2023-12-29 14:00:00', '2023-12-29 14:00:00', 'USER3', 'En production'),
('CMD024', 'LOG1', 'Création', '2023-12-30 15:00:00', '2023-12-30 15:00:00', 'USER1', 'En attente de validation');

-- Table a_vorgang (Événements des commandes)
CREATE TABLE IF NOT EXISTS a_vorgang (
    id_a_kopf VARCHAR(32),
    nummer VARCHAR(15),
    bezeichnung VARCHAR(50),
    datum DATETIME COMMENT 'Date',
    zeit DATETIME COMMENT 'Heure',
    benutzer VARCHAR(50),
    notizcode VARCHAR(15),
    notiztext TEXT,
    codeintern VARCHAR(15),
    nloesch SMALLINT,
    PRIMARY KEY (id_a_kopf, nummer),
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
) COMMENT 'Événements des commandes';

-- Données pour a_vorgang
INSERT INTO a_vorgang VALUES
('CMD001', 'VR001', 'Installation Volet', '2023-12-05 08:00:00', '2023-12-05 08:00:00', 'TECH1', 'NOTE1', 'Installation volet roulant chambre', 'INT1', 0),
('CMD001', 'VR002', 'Installation Volet', '2023-12-05 10:00:00', '2023-12-05 10:00:00', 'TECH1', 'NOTE2', 'Installation volet roulant salon', 'INT2', 0),
('CMD002', 'FEN001', 'Pose Fenêtre', '2023-12-06 09:00:00', '2023-12-06 09:00:00', 'TECH2', 'NOTE3', 'Installation fenêtre cuisine', 'INT3', 0),
('CMD003', 'VR003', 'Installation Volet', '2023-12-07 14:00:00', '2023-12-07 14:00:00', 'TECH1', 'NOTE4', 'Installation volet roulant bureau', 'INT4', 0),
('CMD005', 'VR004', 'Installation Volet', '2023-12-08 09:00:00', '2023-12-08 09:00:00', 'TECH1', 'NOTE5', 'Installation volet roulant salon', 'INT5', 0);

-- Table p_artikel (Articles)
CREATE TABLE IF NOT EXISTS p_artikel (
    id VARCHAR(36) PRIMARY KEY,
    id_a_kopf VARCHAR(32),
    position INT COMMENT 'Position',
    artikelid VARCHAR(255) COMMENT 'ID Article',
    dim1 INT COMMENT 'Dimension 1',
    dim2 INT COMMENT 'Dimension 2',
    dim3 INT COMMENT 'Dimension 3',
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
) COMMENT 'Articles des commandes';

-- Données pour p_artikel
INSERT INTO p_artikel VALUES
('ART001', 'CMD001', 1, 'FEN_PVC_001', 1200, 1000, 50),
('ART002', 'CMD001', 2, 'VR_ALU_001', 1200, 1000, 150),
('ART003', 'CMD002', 1, 'FEN_ALU_001', 1500, 1200, 50),
('ART004', 'CMD003', 1, 'VR_PVC_001', 900, 800, 150),
('ART005', 'CMD005', 1, 'VR_PVC_002', 1400, 1200, 150);

-- Table p_zubeh (Accessoires des commandes)
CREATE TABLE IF NOT EXISTS p_zubeh (
    id_a_kopf VARCHAR(32),
    position SMALLINT COMMENT 'Position',
    kennung SMALLINT COMMENT 'Kennung',
    znr SMALLINT COMMENT 'ZNr',
    zcode VARCHAR(20) COMMENT 'Code Accessoire',
    text VARCHAR(50) COMMENT 'Texte',
    stueck FLOAT COMMENT 'Quantité',
    PRIMARY KEY (id_a_kopf, position, kennung, znr),
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
) COMMENT 'Accessoires des commandes';

-- Données pour p_zubeh
INSERT INTO p_zubeh VALUES
('CMD001', 1, 1, 1, 'SOP123', 'Coffre standard PVC', 1),
('CMD001', 2, 1, 1, 'VR001', 'Volet roulant motorisé', 1),
('CMD002', 1, 1, 1, 'S P456', 'Coffre sur mesure ALU', 1),
('CMD003', 1, 1, 1, 'VR002', 'Volet roulant manuel', 1),
('CMD005', 1, 1, 1, 'VR003', 'Volet roulant motorisé solaire', 1),
('CMD006', 1, 1, 1, 'VR004', 'Volet roulant électrique', 1),
('CMD007', 1, 1, 1, 'FEN001', 'Fenêtre PVC', 1),
('CMD008', 1, 1, 1, 'STD123', 'Store standard', 1),
('CMD009', 1, 1, 1, 'S P789', 'Coffre sur mesure PVC', 1),
('CMD010', 1, 1, 1, 'SOP789', 'Coffre motorisé', 1),
-- Nouveaux accessoires
('CMD012', 1, 1, 1, 'VR005', 'Volet roulant solaire', 1),
('CMD015', 1, 1, 1, 'SOP234', 'Coffre motorisé design', 1),
('CMD017', 1, 1, 1, 'VR006', 'Volet roulant connecté', 1),
('CMD022', 1, 1, 1, 'S P567', 'Coffre sur mesure design', 1),
('CMD025', 1, 1, 1, 'VR007', 'Volet roulant automatique', 1),
('CMD028', 1, 1, 1, 'SOP345', 'Coffre intelligent', 1),
('CMD032', 1, 1, 1, 'VR008', 'Volet roulant premium', 1),
('CMD035', 1, 1, 1, 'S P678', 'Coffre sur mesure premium', 1),
('CMD042', 1, 1, 1, 'VR009', 'Volet roulant connecté plus', 1),
('CMD045', 1, 1, 1, 'SOP456', 'Coffre motorisé premium', 1),
-- Autres accessoires sans les codes spéciaux
('CMD011', 1, 1, 1, 'FEN002', 'Fenêtre ALU', 1),
('CMD013', 1, 1, 1, 'STR001', 'Store banne', 1),
('CMD014', 1, 1, 1, 'FEN003', 'Fenêtre PVC', 1),
('CMD016', 1, 1, 1, 'STR002', 'Store vénitien', 1),
('CMD018', 1, 1, 1, 'FEN004', 'Fenêtre mixte', 1),
('CMD019', 1, 1, 1, 'STR003', 'Store enrouleur', 1),
('CMD020', 1, 1, 1, 'FEN005', 'Fenêtre bois', 1),
('CMD021', 1, 1, 1, 'STR004', 'Store plissé', 1),
('CMD023', 1, 1, 1, 'FEN006', 'Fenêtre composite', 1),
('CMD024', 1, 1, 1, 'STR005', 'Store californien', 1);

-- Table a_kopffreie (Informations additionnelles des commandes)
CREATE TABLE IF NOT EXISTS a_kopffreie (
    id_a_kopf VARCHAR(32),
    nummer SMALLINT,
    feldtyp INT,
    feldinhalt VARCHAR(50),
    feld1 VARCHAR(50),
    feld2 VARCHAR(50) COMMENT 'Nombre de menuiseries',
    feld3 VARCHAR(50) COMMENT 'Date d''entrée',
    feld5 VARCHAR(50) COMMENT 'Date de livraison',
    PRIMARY KEY (id_a_kopf, nummer),
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
) COMMENT 'Informations additionnelles des commandes';

-- Données pour a_kopffreie
INSERT INTO a_kopffreie VALUES
('CMD001', 1, 1, 'Info1', 'Val1', '2', '2023-12-01', '2023-12-15'),
('CMD002', 1, 1, 'Info2', 'Val2', '1', '2023-12-03', '2023-12-20'),
('CMD003', 1, 1, 'Info3', 'Val3', '1', '2023-12-04', '2023-12-18'),
('CMD004', 1, 1, 'Info4', 'Val4', '3', '2023-12-05', '2023-12-22'),
('CMD005', 1, 1, 'Info5', 'Val5', '1', '2023-12-05', '2023-12-15');

-- Table a_adresse (Adresses des clients)
CREATE TABLE IF NOT EXISTS a_adresse (
    id_a_kopf VARCHAR(32),
    nummer SMALLINT,
    adressnummer VARCHAR(15),
    adresscode VARCHAR(50),
    firma VARCHAR(50) COMMENT 'Client',
    telefon VARCHAR(30),
    email VARCHAR(100),
    PRIMARY KEY (id_a_kopf, nummer),
    FOREIGN KEY (id_a_kopf) REFERENCES a_kopf(id)
) COMMENT 'Adresses des clients';

-- Données pour a_adresse
INSERT INTO a_adresse VALUES
('CMD001', 1, 'ADR001', 'LIVR', 'DUPONT Jean', '0123456789', 'dupont@email.com'),
('CMD002', 1, 'ADR002', 'LIVR', 'MARTIN Pierre', '0234567890', 'martin@email.com'),
('CMD003', 1, 'ADR003', 'LIVR', 'DUBOIS Marie', '0345678901', 'dubois@email.com'),
('CMD004', 1, 'ADR004', 'LIVR', 'PETIT Sophie', '0456789012', 'petit@email.com'),
('CMD005', 1, 'ADR005', 'LIVR', 'BERNARD Paul', '0567890123', 'bernard@email.com');

-- Création des index pour optimiser les recherches
CREATE INDEX idx_aufstatus ON a_kopf(aufstatus);
CREATE INDEX idx_aunummer ON a_kopf(aunummer);
CREATE INDEX idx_zcode ON p_zubeh(zcode);
CREATE INDEX idx_notiz ON a_logbuch(notiz(255));
