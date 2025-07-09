-- Création de la base de données
CREATE DATABASE IF NOT EXISTS db_commandes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_commandes;

-- Table A_Kopf (Informations principales des commandes)
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

-- Table A_Logbuch (Logs des commandes)
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

-- Table A_Vorgang (Événements des commandes)
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

-- Table P_Artikel (Articles)
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

-- Table P_Zubeh (Accessoires des commandes)
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

-- Table A_KopfFreie (Informations additionnelles des commandes)
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

-- Table A_Adresse (Adresses des clients)
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

-- Création des index pour optimiser les recherches
CREATE INDEX idx_aufstatus ON a_kopf(aufstatus);
CREATE INDEX idx_aunummer ON a_kopf(aunummer);
CREATE INDEX idx_zcode ON p_zubeh(zcode);
CREATE INDEX idx_notiz ON a_logbuch(notiz(255));

-- Exemple de données de test
INSERT INTO a_kopf (id, auftragstyp, aunummer, aualpha, aufstatus) VALUES
('TEST1', 1, 123456, 'A', 'Planifiée'),
('TEST2', 1, 123457, 'B', 'En production');

INSERT INTO p_zubeh (id_a_kopf, position, kennung, znr, zcode, text) VALUES
('TEST1', 1, 1, 1, 'SOP123', 'Coffre standard'),
('TEST1', 2, 1, 1, 'VR001', 'Volet roulant');

INSERT INTO a_logbuch (id_a_kopf, code, notiz, datum) VALUES
('TEST1', 'LOG1', 'cde Planifiée', NOW()),
('TEST2', 'LOG2', 'cde Planifiée', NOW());
