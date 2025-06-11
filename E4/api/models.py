from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Inventaire(Base):
    """Table principale des produits en stock"""
    __tablename__ = "inventaire"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False)
    reference_fournisseur = Column(String(100))
    produits = Column(String(500), nullable=False)
    unite_stockage = Column(String(20))
    unite_commande = Column(String(50))
    stock_min = Column(Integer, default=0)
    stock_max = Column(Integer, default=100)
    site = Column(String(100))
    lieu = Column(String(100))
    emplacement = Column(String(100))
    fournisseur = Column(String(200))
    prix_unitaire = Column(DECIMAL(10, 2), default=0)
    categorie = Column(String(100))
    secteur = Column(String(100))
    reference = Column(String(20), unique=True, nullable=False, index=True)  # Référence QR unique
    quantite = Column(Integer, default=0)
    date_entree = Column(Date, server_default=func.current_date())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Fournisseur(Base):
    """Table des fournisseurs"""
    __tablename__ = "fournisseurs"
    
    id = Column(Integer, primary_key=True, index=True)
    id_fournisseur = Column(String(20), unique=True, nullable=False, index=True)
    nom_fournisseur = Column(String(200), nullable=False, index=True)
    adresse = Column(Text)
    
    # Contact 1
    contact1_nom = Column(String(100))
    contact1_prenom = Column(String(100))
    contact1_fonction = Column(String(100))
    contact1_tel_fixe = Column(String(20))
    contact1_tel_mobile = Column(String(20))
    contact1_email = Column(String(200))
    
    # Contact 2
    contact2_nom = Column(String(100))
    contact2_prenom = Column(String(100))
    contact2_fonction = Column(String(100))
    contact2_tel_fixe = Column(String(20))
    contact2_tel_mobile = Column(String(20))
    contact2_email = Column(String(200))
    
    statut = Column(String(20), default='Actif')
    date_creation = Column(Date, server_default=func.current_date())
    nb_produits = Column(Integer, default=0)
    valeur_stock_total = Column(DECIMAL(12, 2), default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Site(Base):
    """Table des sites (niveau 1 de la hiérarchie)"""
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    code_site = Column(String(20), unique=True, nullable=False, index=True)
    nom_site = Column(String(200), nullable=False, index=True)
    adresse = Column(Text)
    ville = Column(String(100))
    code_postal = Column(String(10))
    pays = Column(String(100), default='France')
    responsable = Column(String(200))
    telephone = Column(String(50))
    email = Column(String(200))
    statut = Column(String(20), default='Actif')
    date_creation = Column(Date, server_default=func.current_date())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    lieux = relationship("Lieu", back_populates="site", cascade="all, delete-orphan")

class Lieu(Base):
    """Table des lieux (niveau 2 de la hiérarchie)"""
    __tablename__ = "lieux"
    
    id = Column(Integer, primary_key=True, index=True)
    code_lieu = Column(String(20), unique=True, nullable=False, index=True)
    nom_lieu = Column(String(200), nullable=False, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    type_lieu = Column(String(100))  # Bâtiment, Hangar, Atelier, etc.
    niveau = Column(String(50))  # RDC, 1er étage, etc.
    surface = Column(DECIMAL(10, 2))  # Surface en m²
    responsable = Column(String(200))
    statut = Column(String(20), default='Actif')
    date_creation = Column(Date, server_default=func.current_date())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    site = relationship("Site", back_populates="lieux")
    emplacements = relationship("Emplacement", back_populates="lieu", cascade="all, delete-orphan")

class Emplacement(Base):
    """Table des emplacements (niveau 3 de la hiérarchie)"""
    __tablename__ = "emplacements"
    
    id = Column(Integer, primary_key=True, index=True)
    code_emplacement = Column(String(20), unique=True, nullable=False, index=True)
    nom_emplacement = Column(String(200), nullable=False, index=True)
    lieu_id = Column(Integer, ForeignKey("lieux.id", ondelete="CASCADE"), nullable=False)
    type_emplacement = Column(String(100))  # Étagère, Casier, Zone, etc.
    position = Column(String(100))  # A1, B2, etc.
    capacite_max = Column(Integer, default=100)
    temperature_min = Column(DECIMAL(5, 2))  # Température minimale
    temperature_max = Column(DECIMAL(5, 2))  # Température maximale
    humidite_max = Column(DECIMAL(5, 2))  # Humidité maximale
    conditions_speciales = Column(Text)  # Conditions de stockage spéciales
    responsable = Column(String(200))
    statut = Column(String(20), default='Actif')
    date_creation = Column(Date, server_default=func.current_date())
    nb_produits = Column(Integer, default=0)
    taux_occupation = Column(DECIMAL(5, 2), default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    lieu = relationship("Lieu", back_populates="emplacements")

class Demande(Base):
    """Table des demandes de matériel"""
    __tablename__ = "demandes"
    
    id = Column(Integer, primary_key=True, index=True)
    id_demande = Column(String(50), unique=True, nullable=False, index=True)
    date_demande = Column(TIMESTAMP, nullable=False, index=True)
    demandeur = Column(String(200), nullable=False, index=True)
    produits_demandes = Column(Text, nullable=False)  # JSON stocké comme texte
    motif = Column(Text)
    statut = Column(String(50), default='En attente', index=True)
    date_traitement = Column(TIMESTAMP)
    traite_par = Column(String(200))
    commentaires = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Historique(Base):
    """Table de l'historique des mouvements de stock"""
    __tablename__ = "historique"
    
    id = Column(Integer, primary_key=True, index=True)
    date_mouvement = Column(TIMESTAMP, nullable=False, index=True)
    reference = Column(String(20), index=True)  # Référence du produit
    produit = Column(String(500), nullable=False)
    nature = Column(String(50), nullable=False, index=True)  # Entrée, Sortie, Ajustement
    quantite_mouvement = Column(Integer, nullable=False)
    quantite_avant = Column(Integer, nullable=False)
    quantite_apres = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class TableAtelier(Base):
    """Table des tables d'atelier"""
    __tablename__ = "tables_atelier"
    
    id = Column(Integer, primary_key=True, index=True)
    id_table = Column(String(20), unique=True, nullable=False, index=True)
    nom_table = Column(String(200), nullable=False)
    type_atelier = Column(String(100), nullable=False, index=True)
    emplacement = Column(String(200), nullable=False)
    responsable = Column(String(200), nullable=False, index=True)
    statut = Column(String(20), default='Actif')
    date_creation = Column(Date, server_default=func.current_date())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class ListeInventaire(Base):
    """Table des listes d'inventaire"""
    __tablename__ = "listes_inventaire"
    
    id = Column(Integer, primary_key=True, index=True)
    id_liste = Column(String(20), unique=True, nullable=False, index=True)
    nom_liste = Column(String(300), nullable=False)
    date_creation = Column(TIMESTAMP, nullable=False)
    statut = Column(String(50), default='En préparation', index=True)
    nb_produits = Column(Integer, default=0)
    cree_par = Column(String(200), default='Utilisateur')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    produits = relationship("ProduitListeInventaire", back_populates="liste", cascade="all, delete-orphan")

class ProduitListeInventaire(Base):
    """Table des produits dans les listes d'inventaire"""
    __tablename__ = "produits_listes_inventaire"
    
    id = Column(Integer, primary_key=True, index=True)
    id_liste = Column(String(20), ForeignKey("listes_inventaire.id_liste", ondelete="CASCADE"), nullable=False)
    reference_produit = Column(String(20), nullable=False, index=True)
    nom_produit = Column(String(500), nullable=False)
    emplacement = Column(String(100))
    quantite_theorique = Column(Integer, nullable=False)
    quantite_comptee = Column(Integer)
    categorie = Column(String(100))
    fournisseur = Column(String(200))
    date_ajout = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relations
    liste = relationship("ListeInventaire", back_populates="produits") 