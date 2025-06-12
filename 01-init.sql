-- Script d'initialisation de la base de données GMAO
-- Schéma basé sur les fichiers Excel de l'application Streamlit

-- =====================================================
-- TABLE PRINCIPALE: INVENTAIRE (PRODUITS)
-- =====================================================
CREATE TABLE IF NOT EXISTS inventaire (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    reference_fournisseur VARCHAR(100),
    produits VARCHAR(500) NOT NULL,
    unite_stockage VARCHAR(20),
    unite_commande VARCHAR(50),
    stock_min INTEGER DEFAULT 0,
    stock_max INTEGER DEFAULT 100,
    site VARCHAR(100),
    lieu VARCHAR(100),
    emplacement VARCHAR(100),
    fournisseur VARCHAR(200),
    prix_unitaire DECIMAL(10,2) DEFAULT 0,
    categorie VARCHAR(100),
    secteur VARCHAR(100),
    reference VARCHAR(20) UNIQUE NOT NULL, -- Référence QR unique de 10 chiffres
    quantite INTEGER DEFAULT 0,
    date_entree DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: FOURNISSEURS
-- =====================================================
CREATE TABLE IF NOT EXISTS fournisseurs (
    id SERIAL PRIMARY KEY,
    id_fournisseur VARCHAR(20) UNIQUE NOT NULL,
    nom_fournisseur VARCHAR(200) NOT NULL,
    adresse TEXT,
    
    -- Contact 1
    contact1_nom VARCHAR(100),
    contact1_prenom VARCHAR(100),
    contact1_fonction VARCHAR(100),
    contact1_tel_fixe VARCHAR(20),
    contact1_tel_mobile VARCHAR(20),
    contact1_email VARCHAR(200),
    
    -- Contact 2
    contact2_nom VARCHAR(100),
    contact2_prenom VARCHAR(100),
    contact2_fonction VARCHAR(100),
    contact2_tel_fixe VARCHAR(20),
    contact2_tel_mobile VARCHAR(20),
    contact2_email VARCHAR(200),
    
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    nb_produits INTEGER DEFAULT 0,
    valeur_stock_total DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- STRUCTURE HIÉRARCHIQUE: SITES > LIEUX > EMPLACEMENTS
-- =====================================================

-- TABLE: SITES (Niveau 1)
CREATE TABLE IF NOT EXISTS sites (
    id SERIAL PRIMARY KEY,
    code_site VARCHAR(20) UNIQUE NOT NULL,
    nom_site VARCHAR(200) NOT NULL,
    adresse TEXT,
    ville VARCHAR(100),
    code_postal VARCHAR(10),
    pays VARCHAR(100) DEFAULT 'France',
    responsable VARCHAR(200),
    telephone VARCHAR(50),
    email VARCHAR(200),
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: LIEUX (Niveau 2)
CREATE TABLE IF NOT EXISTS lieux (
    id SERIAL PRIMARY KEY,
    code_lieu VARCHAR(20) UNIQUE NOT NULL,
    nom_lieu VARCHAR(200) NOT NULL,
    site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    type_lieu VARCHAR(100),
    niveau VARCHAR(50),
    surface DECIMAL(10,2),
    responsable VARCHAR(200),
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: EMPLACEMENTS (Niveau 3)
CREATE TABLE IF NOT EXISTS emplacements (
    id SERIAL PRIMARY KEY,
    code_emplacement VARCHAR(20) UNIQUE NOT NULL,
    nom_emplacement VARCHAR(200) NOT NULL,
    lieu_id INTEGER NOT NULL REFERENCES lieux(id) ON DELETE CASCADE,
    type_emplacement VARCHAR(100),
    position VARCHAR(100),
    capacite_max INTEGER DEFAULT 100,
    temperature_min DECIMAL(5,2),
    temperature_max DECIMAL(5,2),
    humidite_max DECIMAL(5,2),
    conditions_speciales TEXT,
    responsable VARCHAR(200),
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    nb_produits INTEGER DEFAULT 0,
    taux_occupation DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: DEMANDES DE MATERIEL
-- =====================================================
CREATE TABLE IF NOT EXISTS demandes (
    id SERIAL PRIMARY KEY,
    id_demande VARCHAR(50) UNIQUE NOT NULL,
    date_demande TIMESTAMP NOT NULL,
    demandeur VARCHAR(200) NOT NULL,
    produits_demandes TEXT NOT NULL, -- JSON stocké comme texte
    motif TEXT,
    statut VARCHAR(50) DEFAULT 'En attente',
    date_traitement TIMESTAMP,
    traite_par VARCHAR(200),
    commentaires TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: HISTORIQUE DES MOUVEMENTS
-- =====================================================
CREATE TABLE IF NOT EXISTS historique (
    id SERIAL PRIMARY KEY,
    date_mouvement TIMESTAMP NOT NULL,
    reference VARCHAR(20), -- Référence du produit
    produit VARCHAR(500) NOT NULL,
    nature VARCHAR(50) NOT NULL, -- Entrée, Sortie, Ajustement
    quantite_mouvement INTEGER NOT NULL,
    quantite_avant INTEGER NOT NULL,
    quantite_apres INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: TABLES D'ATELIER
-- =====================================================
CREATE TABLE IF NOT EXISTS tables_atelier (
    id SERIAL PRIMARY KEY,
    id_table VARCHAR(20) UNIQUE NOT NULL,
    nom_table VARCHAR(200) NOT NULL,
    type_atelier VARCHAR(100) NOT NULL,
    emplacement VARCHAR(200) NOT NULL,
    responsable VARCHAR(200) NOT NULL,
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: LISTES D'INVENTAIRE
-- =====================================================
CREATE TABLE IF NOT EXISTS listes_inventaire (
    id SERIAL PRIMARY KEY,
    id_liste VARCHAR(20) UNIQUE NOT NULL,
    nom_liste VARCHAR(300) NOT NULL,
    date_creation TIMESTAMP NOT NULL,
    statut VARCHAR(50) DEFAULT 'En préparation',
    nb_produits INTEGER DEFAULT 0,
    cree_par VARCHAR(200) DEFAULT 'Utilisateur',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: PRODUITS DES LISTES D'INVENTAIRE
-- =====================================================
CREATE TABLE IF NOT EXISTS produits_listes_inventaire (
    id SERIAL PRIMARY KEY,
    id_liste VARCHAR(20) NOT NULL,
    reference_produit VARCHAR(20) NOT NULL,
    nom_produit VARCHAR(500) NOT NULL,
    emplacement VARCHAR(100),
    quantite_theorique INTEGER NOT NULL,
    quantite_comptee INTEGER,
    categorie VARCHAR(100),
    fournisseur VARCHAR(200),
    date_ajout TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_liste) REFERENCES listes_inventaire(id_liste) ON DELETE CASCADE
);

-- =====================================================
-- INDEX POUR AMÉLIORER LES PERFORMANCES
-- =====================================================

-- Index sur la table inventaire
CREATE INDEX IF NOT EXISTS idx_inventaire_code ON inventaire(code);
CREATE INDEX IF NOT EXISTS idx_inventaire_reference ON inventaire(reference);
CREATE INDEX IF NOT EXISTS idx_inventaire_fournisseur ON inventaire(fournisseur);
CREATE INDEX IF NOT EXISTS idx_inventaire_emplacement ON inventaire(emplacement);
CREATE INDEX IF NOT EXISTS idx_inventaire_categorie ON inventaire(categorie);

-- Index sur les fournisseurs
CREATE INDEX IF NOT EXISTS idx_fournisseurs_nom ON fournisseurs(nom_fournisseur);
CREATE INDEX IF NOT EXISTS idx_fournisseurs_id ON fournisseurs(id_fournisseur);

-- Index sur les sites
CREATE INDEX IF NOT EXISTS idx_sites_code ON sites(code_site);
CREATE INDEX IF NOT EXISTS idx_sites_nom ON sites(nom_site);

-- Index sur les lieux
CREATE INDEX IF NOT EXISTS idx_lieux_code ON lieux(code_lieu);
CREATE INDEX IF NOT EXISTS idx_lieux_nom ON lieux(nom_lieu);
CREATE INDEX IF NOT EXISTS idx_lieux_site ON lieux(site_id);

-- Index sur les emplacements
CREATE INDEX IF NOT EXISTS idx_emplacements_code ON emplacements(code_emplacement);
CREATE INDEX IF NOT EXISTS idx_emplacements_nom ON emplacements(nom_emplacement);
CREATE INDEX IF NOT EXISTS idx_emplacements_lieu ON emplacements(lieu_id);

-- Index sur les demandes
CREATE INDEX IF NOT EXISTS idx_demandes_statut ON demandes(statut);
CREATE INDEX IF NOT EXISTS idx_demandes_demandeur ON demandes(demandeur);
CREATE INDEX IF NOT EXISTS idx_demandes_date ON demandes(date_demande);

-- Index sur l'historique
CREATE INDEX IF NOT EXISTS idx_historique_reference ON historique(reference);
CREATE INDEX IF NOT EXISTS idx_historique_date ON historique(date_mouvement);
CREATE INDEX IF NOT EXISTS idx_historique_nature ON historique(nature);

-- Index sur les tables d'atelier
CREATE INDEX IF NOT EXISTS idx_tables_atelier_type ON tables_atelier(type_atelier);
CREATE INDEX IF NOT EXISTS idx_tables_atelier_responsable ON tables_atelier(responsable);

-- Index sur les listes d'inventaire
CREATE INDEX IF NOT EXISTS idx_listes_inventaire_statut ON listes_inventaire(statut);
CREATE INDEX IF NOT EXISTS idx_produits_listes_reference ON produits_listes_inventaire(reference_produit);

-- =====================================================
-- FONCTIONS ET TRIGGERS
-- =====================================================

-- Fonction pour mettre à jour les statistiques des fournisseurs
CREATE OR REPLACE FUNCTION update_fournisseur_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Mettre à jour le nombre de produits et la valeur totale du stock pour le fournisseur
    UPDATE fournisseurs 
    SET 
        nb_produits = (
            SELECT COUNT(*) 
            FROM inventaire 
            WHERE fournisseur = fournisseurs.nom_fournisseur
        ),
        valeur_stock_total = (
            SELECT COALESCE(SUM(quantite * prix_unitaire), 0)
            FROM inventaire 
            WHERE fournisseur = fournisseurs.nom_fournisseur
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE nom_fournisseur = COALESCE(NEW.fournisseur, OLD.fournisseur);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour les stats des fournisseurs
CREATE TRIGGER trigger_update_fournisseur_stats
    AFTER INSERT OR UPDATE OR DELETE ON inventaire
    FOR EACH ROW
    EXECUTE FUNCTION update_fournisseur_stats();

-- Fonction pour mettre à jour les statistiques des emplacements
CREATE OR REPLACE FUNCTION update_emplacement_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Mettre à jour le nombre de produits et le taux d'occupation pour l'emplacement
    UPDATE emplacements 
    SET 
        nb_produits = (
            SELECT COUNT(*) 
            FROM inventaire 
            WHERE emplacement = emplacements.nom_emplacement
        ),
        taux_occupation = (
            SELECT CASE 
                WHEN emplacements.capacite_max > 0 THEN 
                    ROUND((COUNT(*)::DECIMAL / emplacements.capacite_max * 100), 2)
                ELSE 0 
            END
            FROM inventaire 
            WHERE emplacement = emplacements.nom_emplacement
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE nom_emplacement = COALESCE(NEW.emplacement, OLD.emplacement);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour les stats des emplacements
CREATE TRIGGER trigger_update_emplacement_stats
    AFTER INSERT OR UPDATE OR DELETE ON inventaire
    FOR EACH ROW
    EXECUTE FUNCTION update_emplacement_stats();

-- Fonction pour mettre à jour le nombre de produits dans les listes d'inventaire
CREATE OR REPLACE FUNCTION update_liste_inventaire_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Mettre à jour le nombre de produits dans la liste
    UPDATE listes_inventaire 
    SET 
        nb_produits = (
            SELECT COUNT(*) 
            FROM produits_listes_inventaire 
            WHERE id_liste = listes_inventaire.id_liste
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id_liste = COALESCE(NEW.id_liste, OLD.id_liste);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour les stats des listes d'inventaire
CREATE TRIGGER trigger_update_liste_inventaire_stats
    AFTER INSERT OR UPDATE OR DELETE ON produits_listes_inventaire
    FOR EACH ROW
    EXECUTE FUNCTION update_liste_inventaire_stats();

-- =====================================================
-- TRIGGERS POUR LA HIÉRARCHIE
-- =====================================================

-- Fonction pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour updated_at
CREATE TRIGGER update_sites_updated_at BEFORE UPDATE ON sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lieux_updated_at BEFORE UPDATE ON lieux
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_emplacements_updated_at BEFORE UPDATE ON emplacements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- DONNÉES D'EXEMPLE - PRODUITS INVENTÉS BASÉS SUR L'IMAGE
-- =====================================================

-- Insertion des fournisseurs
INSERT INTO fournisseurs (id_fournisseur, nom_fournisseur, adresse, contact1_nom, contact1_prenom, contact1_email, contact1_tel_fixe) VALUES
('BOSCH01', 'BOSCHAT', '15 rue de la Menuiserie, 69000 Lyon', 'Martin', 'Pierre', 'pierre.martin@boschat.fr', '04.78.12.34.56'),
('FAIL01', 'FAILLE', '22 avenue des Artisans, 75011 Paris', 'Dubois', 'Marie', 'marie.dubois@faille.fr', '01.43.56.78.90'),
('SFS01', 'SFS', '8 boulevard Industriel, 13008 Marseille', 'Bernard', 'Jean', 'jean.bernard@sfs.fr', '04.91.23.45.67'),
('PRFER01', 'PROFORM', '45 rue de la Ferronnerie, 44000 Nantes', 'Lefebvre', 'Sophie', 'sophie.lefebvre@proform.fr', '02.40.11.22.33');

-- Insertion des sites
INSERT INTO sites (code_site, nom_site, adresse, ville, code_postal, responsable, telephone) VALUES
('SITE01', 'Entrepôt Principal Lyon', '150 rue de la Logistique', 'Lyon', '69007', 'Dupont Michel', '04.78.90.12.34'),
('SITE02', 'Magasin Paris Nord', '85 avenue de la République', 'Paris', '75019', 'Lambert Julie', '01.42.67.89.01');

-- Insertion des lieux
INSERT INTO lieux (code_lieu, nom_lieu, site_id, type_lieu, niveau, responsable) VALUES
('LIEU01', 'Zone de stockage A', 1, 'Entrepôt', 'Rez-de-chaussée', 'Martin Paul'),
('LIEU02', 'Zone de stockage B', 1, 'Entrepôt', 'Étage 1', 'Moreau Anne'),
('LIEU03', 'Magasin de vente', 2, 'Commercial', 'Rez-de-chaussée', 'Roux Thomas');

-- Insertion des emplacements
INSERT INTO emplacements (code_emplacement, nom_emplacement, lieu_id, type_emplacement, position, capacite_max, responsable) VALUES
('EMP01', 'Allée A1-Étagère 1', 1, 'Étagère métallique', 'A1-E1', 200, 'Martin Paul'),
('EMP02', 'Allée A2-Étagère 3', 1, 'Étagère métallique', 'A2-E3', 150, 'Martin Paul'),
('EMP03', 'Allée B1-Étagère 2', 2, 'Étagère haute', 'B1-E2', 300, 'Moreau Anne'),
('EMP04', 'Zone Vitrine 1', 3, 'Présentoir', 'V1', 50, 'Roux Thomas');

-- Insertion de produits d'exemple basés sur l'image
INSERT INTO inventaire (
    code, reference_fournisseur, produits, unite_stockage, unite_commande, 
    stock_min, stock_max, site, lieu, emplacement, fournisseur, 
    prix_unitaire, categorie, secteur, reference, quantite
) VALUES
-- Crémones et systèmes de fermeture
('R300001', '274200', 'Crémone OB FB 16mm P240 QU-0093015', 'PCE', 'BOITE 5', 50, 120, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A1-Étagère 1', 'BOSCHAT', 5.20, 'Fermeture', 'PVC', '1234567890', 85),
('R300002', '274201', 'Crémone semi-fixe 801-1200 (F10) avec RA', 'PCE', 'BOITE 3', 25, 60, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A1-Étagère 1', 'BOSCHAT', 8.75, 'Fermeture', 'PVC', '1234567891', 42),
('R300003', '274202', 'Crémone semi-fixe 901-1400 avec RA renforcée', 'PCE', 'BOITE 3', 20, 50, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A1-Étagère 1', 'BOSCHAT', 12.30, 'Fermeture', 'PVC', '1234567892', 28),

-- Verrouilleurs et mécanismes
('R255300', '273820', 'Verrouilleur 500mm 2E 255300', 'PCE', 'BOITE 15', 100, 400, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A2-Étagère 3', 'BOSCHAT', 1.45, 'Fermeture', 'PVC', '1234567893', 287),
('R255301', '273821', 'Verrouilleur 650mm 3E 255301', 'PCE', 'BOITE 12', 80, 300, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A2-Étagère 3', 'BOSCHAT', 1.85, 'Fermeture', 'PVC', '1234567894', 195),

-- Allonges et extensions
('R255400', '273822', 'Allonge de 750 2E 255400', 'PCE', 'BOITE 10', 120, 280, 'Entrepôt Principal Lyon', 'Zone de stockage B', 'Allée B1-Étagère 2', 'BOSCHAT', 2.10, 'Fermeture', 'PVC', '1234567895', 165),
('R255401', '273823', 'Allonge de 850 3E 255401', 'PCE', 'BOITE 8', 100, 250, 'Entrepôt Principal Lyon', 'Zone de stockage B', 'Allée B1-Étagère 2', 'BOSCHAT', 2.55, 'Fermeture', 'PVC', '1234567896', 142),

-- Crémones FB variables
('R259800', '2730600', 'Crémone FB Variable L800 480-720', 'PCE', 'BOITE 4', 8, 25, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A1-Étagère 1', 'BOSCHAT', 4.80, 'Fermeture', 'PVC', '1234567897', 15),
('R259801', '2730601', 'Crémone FB Variable L1000 580-820', 'PCE', 'BOITE 4', 6, 20, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A1-Étagère 1', 'BOSCHAT', 6.25, 'Fermeture', 'PVC', '1234567898', 12),
('R259802', '2730602', 'Crémone FB Variable L1200 680-920', 'PCE', 'BOITE 3', 4, 15, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A1-Étagère 1', 'BOSCHAT', 7.90, 'Fermeture', 'PVC', '1234567899', 8),

-- Renvois d'angle et mécanismes
('R260300', '2731820', 'Renvoi d''angle 120/140 2V 260300', 'PCE', 'BOITE 20', 1500, 4000, 'Entrepôt Principal Lyon', 'Zone de stockage B', 'Allée B1-Étagère 2', 'BOSCHAT', 1.65, 'Fermeture', 'PVC', '1234567900', 2850),
('R260301', '2731821', 'Renvoi d''angle 160/180 3V 260301', 'PCE', 'BOITE 15', 50, 150, 'Entrepôt Principal Lyon', 'Zone de stockage B', 'Allée B1-Étagère 2', 'BOSCHAT', 2.85, 'Fermeture', 'PVC', '1234567901', 89),

-- Équerres et accessoires
('R260400', '2731822', 'Équerre de compas avec galet 260400', 'PCE', 'BOITE 8', 3, 10, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A2-Étagère 3', 'BOSCHAT', 3.20, 'Fermeture', 'PVC', '1234567902', 6),
('R260401', '2731823', 'Équerre de compas renforcée 260401', 'PCE', 'BOITE 5', 2, 8, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A2-Étagère 3', 'BOSCHAT', 4.75, 'Fermeture', 'PVC', '1234567903', 4),

-- Cylindres et serrures
('C6000', '1382380N', 'CYLINDRE RX 70 35X35 NICK MAT VARIE', 'PCE', 'Unité', 8, 25, 'Magasin Paris Nord', 'Magasin de vente', 'Zone Vitrine 1', 'FAILLE', 28.50, 'Fermeture', 'ALU', '1234567904', 16),
('C6001', '1382381N', 'CYLINDRE RX 80 40X40 NICK MAT VARIE', 'PCE', 'Unité', 6, 20, 'Magasin Paris Nord', 'Magasin de vente', 'Zone Vitrine 1', 'FAILLE', 32.80, 'Fermeture', 'ALU', '1234567905', 11),

-- Poignées et accessoires
('P5510300', '2205320N', 'POIGNEE EXT REDUITE 5510 BLANC 9017 DTL', 'PCE', 'Unité', 2, 8, 'Magasin Paris Nord', 'Magasin de vente', 'Zone Vitrine 1', 'FAILLE', 18.90, 'Fermeture', 'ALU', '1234567906', 5),
('P5510301', '2205321N', 'POIGNEE EXT REDUITE 5510 NOIR 9005 DTL', 'PCE', 'Unité', 3, 10, 'Magasin Paris Nord', 'Magasin de vente', 'Zone Vitrine 1', 'FAILLE', 19.50, 'Fermeture', 'ALU', '1234567907', 7),

-- Vis et visserie
('SPT1600', '1523995', 'SPT/16-4,3X22-GS', 'PCE', 'Boite 1000', 5000, 15000, 'Entrepôt Principal Lyon', 'Zone de stockage B', 'Allée B1-Étagère 2', 'SFS', 0.65, 'VISSERIE', 'PVC', '1234567908', 8500),
('SPT1601', '1517493', 'SPT/19-4,3X25-H-GS', 'PCE', 'Boite 1000', 4000, 12000, 'Entrepôt Principal Lyon', 'Zone de stockage B', 'Allée B1-Étagère 2', 'SFS', 0.72, 'VISSERIE', 'PVC', '1234567909', 7200),

-- Nouveaux produits inventés
('R270000', '274300', 'Crémone haute sécurité 1200mm avec double RA', 'PCE', 'BOITE 2', 10, 30, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A1-Étagère 1', 'BOSCHAT', 25.80, 'Fermeture', 'PVC', '1234567910', 18),
('R270001', '274301', 'Kit de réparation crémone FB standard', 'PCE', 'KIT', 5, 20, 'Entrepôt Principal Lyon', 'Zone de stockage A', 'Allée A2-Étagère 3', 'BOSCHAT', 8.90, 'Fermeture', 'PVC', '1234567911', 12),
('V4000', '456789A', 'Verrous à bouton poussoir 40mm', 'PCE', 'BOITE 6', 15, 45, 'Magasin Paris Nord', 'Magasin de vente', 'Zone Vitrine 1', 'PROFORM', 12.75, 'Fermeture', 'ALU', '1234567912', 28),
('G3000', '789012B', 'Gâches ajustables universelles', 'PCE', 'BOITE 10', 25, 80, 'Entrepôt Principal Lyon', 'Zone de stockage B', 'Allée B1-Étagère 2', 'PROFORM', 3.40, 'Fermeture', 'ALU', '1234567913', 52),
('SPT2000', '1234567C', 'SPT/22-5,0X30-INOX-GS', 'PCE', 'Boite 500', 2000, 8000, 'Entrepôt Principal Lyon', 'Zone de stockage B', 'Allée B1-Étagère 2', 'SFS', 1.25, 'VISSERIE', 'INOX', '1234567914', 4500);
