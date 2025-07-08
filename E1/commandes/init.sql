-- Création des tables
CREATE TABLE A_Kopf (
    ID VARCHAR(32) PRIMARY KEY,
    AuftragsTyp SMALLINT,
    AuNummer INT,
    AuAlpha VARCHAR(5),
    KundenNr VARCHAR(15),
    KundenBez VARCHAR(15),
    Kommission VARCHAR(50),
    Bauvorhaben VARCHAR(50),
    Auftragsart SMALLINT,
    FSystemGrp SMALLINT,
    AufStatus VARCHAR(15),
    Techniker VARCHAR(15),
    A_VorMwSt DECIMAL(15,2),
    UNIQUE KEY unique_commande (AuftragsTyp, AuNummer, AuAlpha)
) COLLATE='utf8mb4_general_ci';

CREATE TABLE A_Logbuch (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ID_A_Kopf VARCHAR(32),
    Code VARCHAR(15),
    Bezeichnung VARCHAR(50),
    Datum DATETIME,
    Zeit DATETIME,
    Benutzer VARCHAR(50),
    Notiz TEXT,
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID)
) COLLATE='utf8mb4_general_ci';

CREATE TABLE A_KopfFreie (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ID_A_Kopf VARCHAR(32),
    Nummer SMALLINT,
    FeldTyp INT,
    FeldInhalt VARCHAR(50),
    Feld1 VARCHAR(50),
    Feld2 VARCHAR(50),
    Feld3 VARCHAR(50),
    Feld5 VARCHAR(50),
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID),
    UNIQUE KEY unique_kopffreie (ID_A_Kopf, Nummer)
) COLLATE='utf8mb4_general_ci';

CREATE TABLE P_Artikel (
    ID VARCHAR(36) PRIMARY KEY,
    ID_A_Kopf VARCHAR(32),
    Position INT,
    ArtikelID VARCHAR(255),
    Dim1 INT,
    Dim2 INT,
    Dim3 INT,
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID)
) COLLATE='utf8mb4_general_ci';

CREATE TABLE P_Zubeh (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ID_A_Kopf VARCHAR(32),
    Position SMALLINT,
    Kennung SMALLINT,
    ZNr SMALLINT,
    ZCode VARCHAR(20),
    Text VARCHAR(50),
    Stueck FLOAT,
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID),
    UNIQUE KEY unique_zubeh (ID_A_Kopf, Position, Kennung, ZNr)
) COLLATE='utf8mb4_general_ci';

CREATE TABLE A_Vorgang (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ID_A_Kopf VARCHAR(32),
    Nummer VARCHAR(15),
    Bezeichnung VARCHAR(50),
    Datum DATETIME,
    Zeit DATETIME,
    Benutzer VARCHAR(50),
    NotizCode VARCHAR(15),
    NotizText TEXT,
    CodeIntern VARCHAR(15),
    NLoesch SMALLINT,
    FOREIGN KEY (ID_A_Kopf) REFERENCES A_Kopf(ID),
    UNIQUE KEY unique_vorgang (ID_A_Kopf, Nummer)
) COLLATE='utf8mb4_general_ci';

-- Ajout d'index pour optimiser les performances
CREATE INDEX idx_akopf_status ON A_Kopf(AufStatus);
CREATE INDEX idx_alogbuch_notiz ON A_Logbuch(Notiz(255));
CREATE INDEX idx_pzubeh_zcode ON P_Zubeh(ZCode);
CREATE INDEX idx_avorgang_nummer ON A_Vorgang(Nummer);

-- Exemple de données pour tester
INSERT INTO A_Kopf (ID, AuNummer, AuAlpha, AufStatus) VALUES
('1', 12345, 'A', 'Planifiée'),
('2', 12346, 'B', 'lancer en prod');

INSERT INTO A_Logbuch (ID_A_Kopf, Notiz, Datum) VALUES
('1', 'cde Planifiée', NOW()),
('2', 'cde Planifiée', NOW());

INSERT INTO P_Zubeh (ID_A_Kopf, Position, Kennung, ZNr, ZCode) VALUES
('1', 1, 1, 1, 'SOP123'),
('2', 1, 1, 1, 'S P 456');

INSERT INTO A_Vorgang (ID_A_Kopf, Nummer) VALUES
('1', 'VR123'),
('2', 'NORMAL456'); 