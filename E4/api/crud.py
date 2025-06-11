from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional
from datetime import datetime
import models
import schemas

# =====================================================
# CRUD POUR INVENTAIRE (PRODUITS)
# =====================================================

def get_inventaire(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les produits de l'inventaire"""
    return db.query(models.Inventaire).offset(skip).limit(limit).all()

def get_inventaire_by_id(db: Session, inventaire_id: int):
    """Récupérer un produit par son ID"""
    return db.query(models.Inventaire).filter(models.Inventaire.id == inventaire_id).first()

def get_inventaire_by_reference(db: Session, reference: str):
    """Récupérer un produit par sa référence QR"""
    return db.query(models.Inventaire).filter(models.Inventaire.reference == reference).first()

def get_inventaire_by_code(db: Session, code: str):
    """Récupérer un produit par son code"""
    return db.query(models.Inventaire).filter(models.Inventaire.code == code).first()

def search_inventaire(db: Session, search_term: str, skip: int = 0, limit: int = 100):
    """Rechercher des produits par terme de recherche"""
    return db.query(models.Inventaire).filter(
        or_(
            models.Inventaire.code.ilike(f"%{search_term}%"),
            models.Inventaire.produits.ilike(f"%{search_term}%"),
            models.Inventaire.reference.ilike(f"%{search_term}%"),
            models.Inventaire.fournisseur.ilike(f"%{search_term}%"),
            models.Inventaire.categorie.ilike(f"%{search_term}%")
        )
    ).offset(skip).limit(limit).all()

def create_inventaire(db: Session, inventaire: schemas.InventaireCreate):
    """Créer un nouveau produit dans l'inventaire"""
    db_inventaire = models.Inventaire(**inventaire.model_dump())
    db.add(db_inventaire)
    db.commit()
    db.refresh(db_inventaire)
    return db_inventaire

def update_inventaire(db: Session, inventaire_id: int, inventaire: schemas.InventaireUpdate):
    """Mettre à jour un produit de l'inventaire"""
    db_inventaire = db.query(models.Inventaire).filter(models.Inventaire.id == inventaire_id).first()
    if db_inventaire:
        update_data = inventaire.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_inventaire, field, value)
        db.commit()
        db.refresh(db_inventaire)
    return db_inventaire

def delete_inventaire(db: Session, inventaire_id: int):
    """Supprimer un produit de l'inventaire"""
    db_inventaire = db.query(models.Inventaire).filter(models.Inventaire.id == inventaire_id).first()
    if db_inventaire:
        db.delete(db_inventaire)
        db.commit()
    return db_inventaire

def get_inventaire_by_emplacement(db: Session, emplacement: str):
    """Récupérer tous les produits d'un emplacement"""
    return db.query(models.Inventaire).filter(models.Inventaire.emplacement == emplacement).all()

def get_inventaire_by_fournisseur(db: Session, fournisseur: str):
    """Récupérer tous les produits d'un fournisseur"""
    return db.query(models.Inventaire).filter(models.Inventaire.fournisseur == fournisseur).all()

def get_inventaire_stock_faible(db: Session):
    """Récupérer les produits avec un stock faible (quantité <= stock_min)"""
    return db.query(models.Inventaire).filter(
        models.Inventaire.quantite <= models.Inventaire.stock_min
    ).all()

# =====================================================
# CRUD POUR FOURNISSEURS
# =====================================================

def get_fournisseurs(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les fournisseurs"""
    return db.query(models.Fournisseur).offset(skip).limit(limit).all()

def get_fournisseur_by_id(db: Session, fournisseur_id: int):
    """Récupérer un fournisseur par son ID"""
    return db.query(models.Fournisseur).filter(models.Fournisseur.id == fournisseur_id).first()

def get_fournisseur_by_id_fournisseur(db: Session, id_fournisseur: str):
    """Récupérer un fournisseur par son ID fournisseur"""
    return db.query(models.Fournisseur).filter(models.Fournisseur.id_fournisseur == id_fournisseur).first()

def create_fournisseur(db: Session, fournisseur: schemas.FournisseurCreate):
    """Créer un nouveau fournisseur"""
    db_fournisseur = models.Fournisseur(**fournisseur.model_dump())
    db.add(db_fournisseur)
    db.commit()
    db.refresh(db_fournisseur)
    return db_fournisseur

def update_fournisseur(db: Session, fournisseur_id: int, fournisseur: schemas.FournisseurUpdate):
    """Mettre à jour un fournisseur"""
    db_fournisseur = db.query(models.Fournisseur).filter(models.Fournisseur.id == fournisseur_id).first()
    if db_fournisseur:
        update_data = fournisseur.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_fournisseur, field, value)
        db.commit()
        db.refresh(db_fournisseur)
    return db_fournisseur

def delete_fournisseur(db: Session, fournisseur_id: int):
    """Supprimer un fournisseur"""
    db_fournisseur = db.query(models.Fournisseur).filter(models.Fournisseur.id == fournisseur_id).first()
    if db_fournisseur:
        db.delete(db_fournisseur)
        db.commit()
    return db_fournisseur

# =====================================================
# CRUD POUR LA HIÉRARCHIE SITE > LIEU > EMPLACEMENT
# =====================================================

# SITES
def get_sites(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les sites"""
    return db.query(models.Site).offset(skip).limit(limit).all()

def get_site_by_id(db: Session, site_id: int):
    """Récupérer un site par son ID"""
    return db.query(models.Site).filter(models.Site.id == site_id).first()

def get_site_by_code(db: Session, code_site: str):
    """Récupérer un site par son code"""
    return db.query(models.Site).filter(models.Site.code_site == code_site).first()

def create_site(db: Session, site: schemas.SiteCreate):
    """Créer un nouveau site"""
    db_site = models.Site(**site.model_dump())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

def update_site(db: Session, site_id: int, site: schemas.SiteUpdate):
    """Mettre à jour un site"""
    db_site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if db_site:
        update_data = site.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_site, field, value)
        db.commit()
        db.refresh(db_site)
    return db_site

def delete_site(db: Session, site_id: int):
    """Supprimer un site"""
    db_site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if db_site:
        db.delete(db_site)
        db.commit()
    return db_site

# LIEUX
def get_lieux(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les lieux"""
    return db.query(models.Lieu).offset(skip).limit(limit).all()

def get_lieux_by_site(db: Session, site_id: int):
    """Récupérer tous les lieux d'un site"""
    return db.query(models.Lieu).filter(models.Lieu.site_id == site_id).all()

def get_lieu_by_id(db: Session, lieu_id: int):
    """Récupérer un lieu par son ID"""
    return db.query(models.Lieu).filter(models.Lieu.id == lieu_id).first()

def get_lieu_by_code(db: Session, code_lieu: str):
    """Récupérer un lieu par son code"""
    return db.query(models.Lieu).filter(models.Lieu.code_lieu == code_lieu).first()

def create_lieu(db: Session, lieu: schemas.LieuCreate):
    """Créer un nouveau lieu"""
    db_lieu = models.Lieu(**lieu.model_dump())
    db.add(db_lieu)
    db.commit()
    db.refresh(db_lieu)
    return db_lieu

def update_lieu(db: Session, lieu_id: int, lieu: schemas.LieuUpdate):
    """Mettre à jour un lieu"""
    db_lieu = db.query(models.Lieu).filter(models.Lieu.id == lieu_id).first()
    if db_lieu:
        update_data = lieu.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_lieu, field, value)
        db.commit()
        db.refresh(db_lieu)
    return db_lieu

def delete_lieu(db: Session, lieu_id: int):
    """Supprimer un lieu"""
    db_lieu = db.query(models.Lieu).filter(models.Lieu.id == lieu_id).first()
    if db_lieu:
        db.delete(db_lieu)
        db.commit()
    return db_lieu

# EMPLACEMENTS
def get_emplacements(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les emplacements"""
    return db.query(models.Emplacement).offset(skip).limit(limit).all()

def get_emplacements_by_lieu(db: Session, lieu_id: int):
    """Récupérer tous les emplacements d'un lieu"""
    return db.query(models.Emplacement).filter(models.Emplacement.lieu_id == lieu_id).all()

def get_emplacement_by_id(db: Session, emplacement_id: int):
    """Récupérer un emplacement par son ID"""
    return db.query(models.Emplacement).filter(models.Emplacement.id == emplacement_id).first()

def get_emplacement_by_code(db: Session, code_emplacement: str):
    """Récupérer un emplacement par son code"""
    return db.query(models.Emplacement).filter(models.Emplacement.code_emplacement == code_emplacement).first()

def create_emplacement(db: Session, emplacement: schemas.EmplacementCreate):
    """Créer un nouveau emplacement"""
    # Générer un code emplacement automatique (max 20 caractères)
    from datetime import datetime
    import random
    import string
    timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
    code_emplacement = f"E{timestamp}{random_suffix}"  # E + 12 + 4 = 17 caractères max
    
    # Créer le dictionnaire avec le code généré
    emplacement_data = emplacement.model_dump()
    emplacement_data['code_emplacement'] = code_emplacement
    
    db_emplacement = models.Emplacement(**emplacement_data)
    db.add(db_emplacement)
    db.commit()
    db.refresh(db_emplacement)
    return db_emplacement

def update_emplacement(db: Session, emplacement_id: int, emplacement: schemas.EmplacementUpdate):
    """Mettre à jour un emplacement"""
    db_emplacement = db.query(models.Emplacement).filter(models.Emplacement.id == emplacement_id).first()
    if db_emplacement:
        update_data = emplacement.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_emplacement, field, value)
        db.commit()
        db.refresh(db_emplacement)
    return db_emplacement

def delete_emplacement(db: Session, emplacement_id: int):
    """Supprimer un emplacement"""
    db_emplacement = db.query(models.Emplacement).filter(models.Emplacement.id == emplacement_id).first()
    if db_emplacement:
        db.delete(db_emplacement)
        db.commit()
    return db_emplacement

# FONCTIONS UTILITAIRES POUR LA HIÉRARCHIE
def get_emplacements_with_hierarchy(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les emplacements avec leur hiérarchie complète"""
    return db.query(
        models.Emplacement,
        models.Lieu.nom_lieu,
        models.Site.nom_site
    ).join(
        models.Lieu, models.Emplacement.lieu_id == models.Lieu.id
    ).join(
        models.Site, models.Lieu.site_id == models.Site.id
    ).offset(skip).limit(limit).all()

def get_lieux_with_site(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les lieux avec leur site"""
    return db.query(
        models.Lieu,
        models.Site.nom_site
    ).join(
        models.Site, models.Lieu.site_id == models.Site.id
    ).offset(skip).limit(limit).all()

def get_sites_with_stats(db: Session):
    """Récupérer tous les sites avec leurs statistiques"""
    from sqlalchemy import func
    
    return db.query(
        models.Site,
        func.count(models.Lieu.id).label('nb_lieux'),
        func.count(models.Emplacement.id).label('nb_emplacements')
    ).outerjoin(
        models.Lieu, models.Site.id == models.Lieu.site_id
    ).outerjoin(
        models.Emplacement, models.Lieu.id == models.Emplacement.lieu_id
    ).group_by(models.Site.id).all()

# =====================================================
# CRUD POUR DEMANDES
# =====================================================

def get_demandes(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer toutes les demandes"""
    return db.query(models.Demande).order_by(desc(models.Demande.date_demande)).offset(skip).limit(limit).all()

def get_demande_by_id(db: Session, demande_id: int):
    """Récupérer une demande par son ID"""
    return db.query(models.Demande).filter(models.Demande.id == demande_id).first()

def get_demande_by_id_demande(db: Session, id_demande: str):
    """Récupérer une demande par son ID demande"""
    return db.query(models.Demande).filter(models.Demande.id_demande == id_demande).first()

def get_demandes_by_statut(db: Session, statut: str):
    """Récupérer les demandes par statut"""
    return db.query(models.Demande).filter(models.Demande.statut == statut).order_by(desc(models.Demande.date_demande)).all()

def get_demandes_by_demandeur(db: Session, demandeur: str):
    """Récupérer les demandes par demandeur"""
    return db.query(models.Demande).filter(models.Demande.demandeur == demandeur).order_by(desc(models.Demande.date_demande)).all()

def create_demande(db: Session, demande: schemas.DemandeCreate):
    """Créer une nouvelle demande"""
    db_demande = models.Demande(**demande.model_dump())
    db.add(db_demande)
    db.commit()
    db.refresh(db_demande)
    return db_demande

def update_demande(db: Session, demande_id: int, demande: schemas.DemandeUpdate):
    """Mettre à jour une demande"""
    db_demande = db.query(models.Demande).filter(models.Demande.id == demande_id).first()
    if db_demande:
        update_data = demande.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_demande, field, value)
        db.commit()
        db.refresh(db_demande)
    return db_demande

# =====================================================
# CRUD POUR HISTORIQUE
# =====================================================

def get_historique(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer l'historique des mouvements"""
    return db.query(models.Historique).order_by(desc(models.Historique.date_mouvement)).offset(skip).limit(limit).all()

def get_historique_by_reference(db: Session, reference: str):
    """Récupérer l'historique d'un produit par sa référence"""
    return db.query(models.Historique).filter(models.Historique.reference == reference).order_by(desc(models.Historique.date_mouvement)).all()

def get_historique_by_nature(db: Session, nature: str):
    """Récupérer l'historique par type de mouvement"""
    return db.query(models.Historique).filter(models.Historique.nature == nature).order_by(desc(models.Historique.date_mouvement)).all()

def create_historique(db: Session, historique: schemas.HistoriqueCreate):
    """Créer un nouvel enregistrement d'historique"""
    db_historique = models.Historique(**historique.model_dump())
    db.add(db_historique)
    db.commit()
    db.refresh(db_historique)
    return db_historique

# =====================================================
# CRUD POUR TABLES D'ATELIER
# =====================================================

def get_tables_atelier(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer toutes les tables d'atelier"""
    return db.query(models.TableAtelier).offset(skip).limit(limit).all()

def get_table_atelier_by_id(db: Session, table_id: int):
    """Récupérer une table d'atelier par son ID"""
    return db.query(models.TableAtelier).filter(models.TableAtelier.id == table_id).first()

def get_table_atelier_by_id_table(db: Session, id_table: str):
    """Récupérer une table d'atelier par son ID table"""
    return db.query(models.TableAtelier).filter(models.TableAtelier.id_table == id_table).first()

def get_tables_atelier_by_type(db: Session, type_atelier: str):
    """Récupérer les tables d'atelier par type"""
    return db.query(models.TableAtelier).filter(models.TableAtelier.type_atelier == type_atelier).all()

def create_table_atelier(db: Session, table: schemas.TableAtelierCreate):
    """Créer une nouvelle table d'atelier"""
    db_table = models.TableAtelier(**table.model_dump())
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    return db_table

def update_table_atelier(db: Session, table_id: int, table: schemas.TableAtelierUpdate):
    """Mettre à jour une table d'atelier"""
    db_table = db.query(models.TableAtelier).filter(models.TableAtelier.id == table_id).first()
    if db_table:
        update_data = table.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_table, field, value)
        db.commit()
        db.refresh(db_table)
    return db_table

def delete_table_atelier(db: Session, table_id: int):
    """Supprimer une table d'atelier"""
    db_table = db.query(models.TableAtelier).filter(models.TableAtelier.id == table_id).first()
    if db_table:
        db.delete(db_table)
        db.commit()
    return db_table

# =====================================================
# CRUD POUR LISTES D'INVENTAIRE
# =====================================================

def get_listes_inventaire(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer toutes les listes d'inventaire"""
    return db.query(models.ListeInventaire).order_by(desc(models.ListeInventaire.date_creation)).offset(skip).limit(limit).all()

def get_liste_inventaire_by_id(db: Session, liste_id: int):
    """Récupérer une liste d'inventaire par son ID"""
    return db.query(models.ListeInventaire).filter(models.ListeInventaire.id == liste_id).first()

def get_liste_inventaire_by_id_liste(db: Session, id_liste: str):
    """Récupérer une liste d'inventaire par son ID liste"""
    return db.query(models.ListeInventaire).filter(models.ListeInventaire.id_liste == id_liste).first()

def create_liste_inventaire(db: Session, liste: schemas.ListeInventaireCreate):
    """Créer une nouvelle liste d'inventaire"""
    db_liste = models.ListeInventaire(**liste.model_dump())
    db.add(db_liste)
    db.commit()
    db.refresh(db_liste)
    return db_liste

def update_liste_inventaire(db: Session, liste_id: int, liste: schemas.ListeInventaireUpdate):
    """Mettre à jour une liste d'inventaire"""
    db_liste = db.query(models.ListeInventaire).filter(models.ListeInventaire.id == liste_id).first()
    if db_liste:
        update_data = liste.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_liste, field, value)
        db.commit()
        db.refresh(db_liste)
    return db_liste

def delete_liste_inventaire(db: Session, liste_id: int):
    """Supprimer une liste d'inventaire"""
    db_liste = db.query(models.ListeInventaire).filter(models.ListeInventaire.id == liste_id).first()
    if db_liste:
        db.delete(db_liste)
        db.commit()
    return db_liste

# =====================================================
# CRUD POUR PRODUITS DES LISTES D'INVENTAIRE
# =====================================================

def get_produits_liste_inventaire(db: Session, id_liste: str):
    """Récupérer tous les produits d'une liste d'inventaire"""
    return db.query(models.ProduitListeInventaire).filter(models.ProduitListeInventaire.id_liste == id_liste).all()

def create_produit_liste_inventaire(db: Session, produit: schemas.ProduitListeInventaireCreate):
    """Ajouter un produit à une liste d'inventaire"""
    db_produit = models.ProduitListeInventaire(**produit.model_dump())
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit

def update_produit_liste_inventaire(db: Session, produit_id: int, produit: schemas.ProduitListeInventaireUpdate):
    """Mettre à jour un produit dans une liste d'inventaire"""
    db_produit = db.query(models.ProduitListeInventaire).filter(models.ProduitListeInventaire.id == produit_id).first()
    if db_produit:
        update_data = produit.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_produit, field, value)
        db.commit()
        db.refresh(db_produit)
    return db_produit

# =====================================================
# FONCTIONS UTILITAIRES POUR LES MOUVEMENTS DE STOCK
# =====================================================

def effectuer_mouvement_stock(db: Session, mouvement: schemas.MouvementStockCreate):
    """Effectuer un mouvement de stock et mettre à jour l'inventaire"""
    # Récupérer le produit
    produit = get_inventaire_by_reference(db, mouvement.reference_produit)
    if not produit:
        return {"success": False, "message": "Produit non trouvé"}
    
    # Calculer les nouvelles quantités
    quantite_avant = produit.quantite
    
    if mouvement.nature.lower() == "entrée":
        quantite_apres = quantite_avant + mouvement.quantite
    elif mouvement.nature.lower() == "sortie":
        if quantite_avant < mouvement.quantite:
            return {"success": False, "message": "Stock insuffisant"}
        quantite_apres = quantite_avant - mouvement.quantite
    elif mouvement.nature.lower() == "ajustement":
        # Pour un ajustement, mouvement.quantite est la nouvelle quantité totale
        quantite_apres = mouvement.quantite
    else:
        return {"success": False, "message": "Type de mouvement invalide"}
    
    # Calculer la quantité de mouvement pour l'historique
    if mouvement.nature.lower() == "ajustement":
        # Pour un ajustement, la quantité de mouvement est la différence
        quantite_mouvement_historique = abs(quantite_apres - quantite_avant)
    else:
        # Pour entrée/sortie, c'est la quantité du mouvement
        quantite_mouvement_historique = mouvement.quantite
    
    # Créer l'enregistrement d'historique
    historique_data = schemas.HistoriqueCreate(
        date_mouvement=datetime.now(),
        reference=mouvement.reference_produit,
        produit=produit.produits,
        nature=mouvement.nature,
        quantite_mouvement=quantite_mouvement_historique,
        quantite_avant=quantite_avant,
        quantite_apres=quantite_apres
    )
    create_historique(db, historique_data)
    
    # Mettre à jour la quantité dans l'inventaire
    update_data = schemas.InventaireUpdate(quantite=quantite_apres)
    update_inventaire(db, produit.id, update_data)
    
    return {
        "success": True, 
        "message": f"Mouvement de stock effectué avec succès",
        "nouveau_stock": quantite_apres
    } 