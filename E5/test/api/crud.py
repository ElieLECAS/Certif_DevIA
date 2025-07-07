from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
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

def search_inventaire(db: Session, search_term: str):
    """Rechercher des produits dans l'inventaire"""
    return db.query(models.Inventaire).filter(
        or_(
            models.Inventaire.produits.ilike(f"%{search_term}%"),
            models.Inventaire.reference.ilike(f"%{search_term}%"),
            models.Inventaire.code.ilike(f"%{search_term}%"),
            models.Inventaire.categorie.ilike(f"%{search_term}%"),
            # Recherche dans les noms des entités liées via les relations
            models.Inventaire.site_obj.has(models.Site.nom_site.ilike(f"%{search_term}%")),
            models.Inventaire.lieu_obj.has(models.Lieu.nom_lieu.ilike(f"%{search_term}%")),
            models.Inventaire.emplacement_obj.has(models.Emplacement.nom_emplacement.ilike(f"%{search_term}%")),
            models.Inventaire.fournisseur_obj.has(models.Fournisseur.nom_fournisseur.ilike(f"%{search_term}%")),
            models.Inventaire.unite_stockage_obj.has(models.UniteStockage.nom_unite.ilike(f"%{search_term}%")),
            models.Inventaire.unite_commande_obj.has(models.UniteCommande.nom_unite.ilike(f"%{search_term}%"))
        )
    ).all()

def create_inventaire(db: Session, inventaire: schemas.InventaireCreate):
    """Créer un nouveau produit dans l'inventaire avec gestion automatique des relations"""
    inventaire_data = inventaire.model_dump()
    
    # Gérer la relation avec le fournisseur
    fournisseur_nom = inventaire_data.get('fournisseur')
    if fournisseur_nom:
        fournisseur_obj = db.query(models.Fournisseur).filter(
            models.Fournisseur.nom_fournisseur == fournisseur_nom
        ).first()
        
        if fournisseur_obj:
            inventaire_data['fournisseur_id'] = fournisseur_obj.id
            print(f"Produit lié au fournisseur ID {fournisseur_obj.id}: {fournisseur_nom}")
        else:
            print(f"Fournisseur '{fournisseur_nom}' non trouvé, produit créé sans liaison")
    
    # Supprimer le champ fournisseur du dictionnaire (plus de colonne texte)
    inventaire_data.pop('fournisseur', None)
    
    # Gérer les relations hiérarchiques Site > Lieu > Emplacement
    site_nom = inventaire_data.get('site')
    lieu_nom = inventaire_data.get('lieu')
    emplacement_nom = inventaire_data.get('emplacement')
    
    # Lier le site
    if site_nom:
        site_obj = db.query(models.Site).filter(
            models.Site.nom_site == site_nom
        ).first()
        if site_obj:
            inventaire_data['site_id'] = site_obj.id
            print(f"Produit lié au site ID {site_obj.id}: {site_nom}")
    
    # Lier le lieu
    if lieu_nom:
        lieu_obj = db.query(models.Lieu).filter(
            models.Lieu.nom_lieu == lieu_nom
        ).first()
        if lieu_obj:
            inventaire_data['lieu_id'] = lieu_obj.id
            print(f"Produit lié au lieu ID {lieu_obj.id}: {lieu_nom}")
    
    # Lier l'emplacement
    if emplacement_nom:
        emplacement_obj = db.query(models.Emplacement).filter(
            models.Emplacement.nom_emplacement == emplacement_nom
        ).first()
        if emplacement_obj:
            inventaire_data['emplacement_id'] = emplacement_obj.id
            print(f"Produit lié à l'emplacement ID {emplacement_obj.id}: {emplacement_nom}")
    
    # Supprimer les champs texte du dictionnaire (plus de colonnes texte)
    inventaire_data.pop('site', None)
    inventaire_data.pop('lieu', None)
    inventaire_data.pop('emplacement', None)
    
    # Gérer les relations avec les unités de stockage et de commande
    unite_stockage_nom = inventaire_data.get('unite_stockage')
    if unite_stockage_nom:
        unite_stockage_obj = db.query(models.UniteStockage).filter(
            models.UniteStockage.nom_unite == unite_stockage_nom
        ).first()
        if unite_stockage_obj:
            inventaire_data['unite_stockage_id'] = unite_stockage_obj.id
            print(f"Produit lié à l'unité de stockage ID {unite_stockage_obj.id}: {unite_stockage_nom}")
        else:
            print(f"Unité de stockage '{unite_stockage_nom}' non trouvée, produit créé sans liaison")
    
    unite_commande_nom = inventaire_data.get('unite_commande')
    if unite_commande_nom:
        unite_commande_obj = db.query(models.UniteCommande).filter(
            models.UniteCommande.nom_unite == unite_commande_nom
        ).first()
        if unite_commande_obj:
            inventaire_data['unite_commande_id'] = unite_commande_obj.id
            print(f"Produit lié à l'unité de commande ID {unite_commande_obj.id}: {unite_commande_nom}")
        else:
            print(f"Unité de commande '{unite_commande_nom}' non trouvée, produit créé sans liaison")
    
    # Supprimer les champs texte des unités du dictionnaire
    inventaire_data.pop('unite_stockage', None)
    inventaire_data.pop('unite_commande', None)
    
    db_inventaire = models.Inventaire(**inventaire_data)
    db.add(db_inventaire)
    db.commit()
    db.refresh(db_inventaire)
    return db_inventaire

def update_inventaire(db: Session, inventaire_id: int, inventaire: schemas.InventaireUpdate):
    """Mettre à jour un produit de l'inventaire avec gestion automatique des relations"""
    db_inventaire = db.query(models.Inventaire).filter(models.Inventaire.id == inventaire_id).first()
    if db_inventaire:
        update_data = inventaire.model_dump(exclude_unset=True)
        
        # Gérer la relation avec le fournisseur si le nom change
        nouveau_fournisseur_nom = update_data.get('fournisseur')
        if nouveau_fournisseur_nom:
            fournisseur_obj = db.query(models.Fournisseur).filter(
                models.Fournisseur.nom_fournisseur == nouveau_fournisseur_nom
            ).first()
            
            if fournisseur_obj:
                update_data['fournisseur_id'] = fournisseur_obj.id
                print(f"Produit relié au fournisseur ID {fournisseur_obj.id}: {nouveau_fournisseur_nom}")
            else:
                update_data['fournisseur_id'] = None
                print(f"Fournisseur '{nouveau_fournisseur_nom}' non trouvé, liaison supprimée")
        
        # Supprimer le champ fournisseur du dictionnaire (plus de colonne texte)
        update_data.pop('fournisseur', None)
        
        # Gérer les relations hiérarchiques
        nouveau_site_nom = update_data.get('site')
        if nouveau_site_nom:
            site_obj = db.query(models.Site).filter(
                models.Site.nom_site == nouveau_site_nom
            ).first()
            if site_obj:
                update_data['site_id'] = site_obj.id
                print(f"Produit relié au site ID {site_obj.id}: {nouveau_site_nom}")
            else:
                update_data['site_id'] = None
        
        nouveau_lieu_nom = update_data.get('lieu')
        if nouveau_lieu_nom:
            lieu_obj = db.query(models.Lieu).filter(
                models.Lieu.nom_lieu == nouveau_lieu_nom
            ).first()
            if lieu_obj:
                update_data['lieu_id'] = lieu_obj.id
                print(f"Produit relié au lieu ID {lieu_obj.id}: {nouveau_lieu_nom}")
            else:
                update_data['lieu_id'] = None
        
        nouveau_emplacement_nom = update_data.get('emplacement')
        if nouveau_emplacement_nom:
            emplacement_obj = db.query(models.Emplacement).filter(
                models.Emplacement.nom_emplacement == nouveau_emplacement_nom
            ).first()
            if emplacement_obj:
                update_data['emplacement_id'] = emplacement_obj.id
                print(f"Produit relié à l'emplacement ID {emplacement_obj.id}: {nouveau_emplacement_nom}")
            else:
                update_data['emplacement_id'] = None
        
        # Supprimer les champs texte du dictionnaire (plus de colonnes texte)
        update_data.pop('site', None)
        update_data.pop('lieu', None)
        update_data.pop('emplacement', None)
        
        # Gérer les relations avec les unités de stockage et de commande
        nouvelle_unite_stockage_nom = update_data.get('unite_stockage')
        if nouvelle_unite_stockage_nom:
            unite_stockage_obj = db.query(models.UniteStockage).filter(
                models.UniteStockage.nom_unite == nouvelle_unite_stockage_nom
            ).first()
            if unite_stockage_obj:
                update_data['unite_stockage_id'] = unite_stockage_obj.id
                print(f"Produit relié à l'unité de stockage ID {unite_stockage_obj.id}: {nouvelle_unite_stockage_nom}")
            else:
                update_data['unite_stockage_id'] = None
                print(f"Unité de stockage '{nouvelle_unite_stockage_nom}' non trouvée, liaison supprimée")
        
        nouvelle_unite_commande_nom = update_data.get('unite_commande')
        if nouvelle_unite_commande_nom:
            unite_commande_obj = db.query(models.UniteCommande).filter(
                models.UniteCommande.nom_unite == nouvelle_unite_commande_nom
            ).first()
            if unite_commande_obj:
                update_data['unite_commande_id'] = unite_commande_obj.id
                print(f"Produit relié à l'unité de commande ID {unite_commande_obj.id}: {nouvelle_unite_commande_nom}")
            else:
                update_data['unite_commande_id'] = None
                print(f"Unité de commande '{nouvelle_unite_commande_nom}' non trouvée, liaison supprimée")
        
        # Supprimer les champs texte des unités du dictionnaire
        update_data.pop('unite_stockage', None)
        update_data.pop('unite_commande', None)
        
        # Appliquer les mises à jour
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

def get_inventaire_by_fournisseur(db: Session, fournisseur: str):
    """Récupérer les produits d'un fournisseur spécifique"""
    # Rechercher par nom de fournisseur via la relation
    return db.query(models.Inventaire).join(
        models.Fournisseur, models.Inventaire.fournisseur_id == models.Fournisseur.id
    ).filter(models.Fournisseur.nom_fournisseur == fournisseur).all()

def get_inventaire_by_emplacement(db: Session, emplacement: str):
    """Récupérer les produits d'un emplacement spécifique"""
    # Rechercher par nom d'emplacement via la relation
    return db.query(models.Inventaire).join(
        models.Emplacement, models.Inventaire.emplacement_id == models.Emplacement.id
    ).filter(models.Emplacement.nom_emplacement == emplacement).all()

def get_inventaire_stock_faible(db: Session):
    """Récupérer les produits avec un stock faible (quantité <= stock_min)"""
    return db.query(models.Inventaire).filter(
        models.Inventaire.quantite <= models.Inventaire.stock_min
    ).all()

def get_fournisseurs_actifs(db: Session):
    """Récupérer les fournisseurs qui ont des produits en stock"""
    # Utiliser les relations au lieu des colonnes texte
    fournisseurs_avec_produits = db.query(models.Fournisseur).join(
        models.Inventaire, models.Fournisseur.id == models.Inventaire.fournisseur_id
    ).filter(models.Inventaire.quantite > 0).distinct().all()
    
    return fournisseurs_avec_produits

def get_emplacements_actifs(db: Session):
    """Récupérer les emplacements qui ont des produits en stock"""
    # Utiliser les relations au lieu des colonnes texte
    emplacements_avec_produits = db.query(models.Emplacement).join(
        models.Inventaire, models.Emplacement.id == models.Inventaire.emplacement_id
    ).filter(models.Inventaire.quantite > 0).distinct().all()
    
    return emplacements_avec_produits

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

def get_fournisseur_by_nom(db: Session, nom_fournisseur: str):
    """Récupérer un fournisseur par son nom"""
    return db.query(models.Fournisseur).filter(models.Fournisseur.nom_fournisseur == nom_fournisseur).first()

def create_fournisseur(db: Session, fournisseur: schemas.FournisseurCreate):
    """Créer un nouveau fournisseur"""
    db_fournisseur = models.Fournisseur(**fournisseur.model_dump())
    db.add(db_fournisseur)
    db.commit()
    db.refresh(db_fournisseur)
    return db_fournisseur

def update_fournisseur(db: Session, fournisseur_id: int, fournisseur: schemas.FournisseurUpdate):
    """Mettre à jour un fournisseur avec propagation des changements aux produits liés"""
    db_fournisseur = db.query(models.Fournisseur).filter(models.Fournisseur.id == fournisseur_id).first()
    if db_fournisseur:
        update_data = fournisseur.model_dump(exclude_unset=True)
        
        # Si le nom du fournisseur change, mettre à jour tous les produits liés
        nouveau_nom = update_data.get('nom_fournisseur')
        if nouveau_nom and nouveau_nom != db_fournisseur.nom_fournisseur:
            # Mettre à jour tous les produits liés par relation (plus besoin de mettre à jour les champs texte)
            produits_lies = db.query(models.Inventaire).filter(
                models.Inventaire.fournisseur_id == fournisseur_id
            ).all()
            
            print(f"Nom du fournisseur mis à jour: {db_fournisseur.nom_fournisseur} → {nouveau_nom}")
            print(f"Produits mis à jour automatiquement via les relations: {len(produits_lies)}")
        
        # Appliquer les mises à jour au fournisseur
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
    """Mettre à jour un site avec propagation des changements aux produits liés"""
    db_site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if db_site:
        update_data = site.model_dump(exclude_unset=True)
        
        # Si le nom du site change, les produits liés seront automatiquement mis à jour via les relations
        nouveau_nom = update_data.get('nom_site')
        if nouveau_nom and nouveau_nom != db_site.nom_site:
            produits_lies = db.query(models.Inventaire).filter(
                models.Inventaire.site_id == site_id
            ).all()
            
            print(f"Nom du site mis à jour: {db_site.nom_site} → {nouveau_nom}")
            print(f"Produits mis à jour automatiquement via les relations: {len(produits_lies)}")
        
        # Appliquer les mises à jour au site
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
    """Mettre à jour un lieu avec propagation des changements aux produits liés"""
    db_lieu = db.query(models.Lieu).filter(models.Lieu.id == lieu_id).first()
    if db_lieu:
        update_data = lieu.model_dump(exclude_unset=True)
        
        # Si le nom du lieu change, les produits liés seront automatiquement mis à jour via les relations
        nouveau_nom = update_data.get('nom_lieu')
        if nouveau_nom and nouveau_nom != db_lieu.nom_lieu:
            produits_lies = db.query(models.Inventaire).filter(
                models.Inventaire.lieu_id == lieu_id
            ).all()
            
            print(f"Nom du lieu mis à jour: {db_lieu.nom_lieu} → {nouveau_nom}")
            print(f"Produits mis à jour automatiquement via les relations: {len(produits_lies)}")
        
        # Appliquer les mises à jour au lieu
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
    """Mettre à jour un emplacement avec propagation des changements aux produits liés"""
    db_emplacement = db.query(models.Emplacement).filter(models.Emplacement.id == emplacement_id).first()
    if db_emplacement:
        update_data = emplacement.model_dump(exclude_unset=True)
        
        # Si le nom de l'emplacement change, les produits liés seront automatiquement mis à jour via les relations
        nouveau_nom = update_data.get('nom_emplacement')
        if nouveau_nom and nouveau_nom != db_emplacement.nom_emplacement:
            produits_lies = db.query(models.Inventaire).filter(
                models.Inventaire.emplacement_id == emplacement_id
            ).all()
            
            print(f"Nom de l'emplacement mis à jour: {db_emplacement.nom_emplacement} → {nouveau_nom}")
            print(f"Produits mis à jour automatiquement via les relations: {len(produits_lies)}")
        
        # Appliquer les mises à jour à l'emplacement
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

def get_demandes_by_id_table(db: Session, id_table: str):
    """Récupérer les demandes par id_table"""
    return db.query(models.Demande).filter(models.Demande.id_table == id_table).order_by(desc(models.Demande.date_demande)).all()

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
        quantite_apres=quantite_apres,
        motif=mouvement.motif
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

def synchroniser_relations_fournisseurs(db: Session):
    """Synchroniser les relations fournisseur_id pour tous les produits existants (fonction legacy - plus nécessaire)"""
    # Cette fonction n'est plus nécessaire car nous n'avons plus de colonnes texte
    # Tous les produits sont créés directement avec les bonnes relations
    print("Synchronisation des fournisseurs: Plus nécessaire avec le nouveau modèle de données")
    return 0

def get_fournisseurs_avec_stats(db: Session):
    """Récupérer tous les fournisseurs avec leurs statistiques de produits"""
    fournisseurs_stats = db.query(
        models.Fournisseur,
        func.count(models.Inventaire.id).label('nb_produits_lies'),
        func.coalesce(func.sum(models.Inventaire.prix_unitaire * models.Inventaire.quantite), 0).label('valeur_stock_total')
    ).outerjoin(
        models.Inventaire, models.Fournisseur.id == models.Inventaire.fournisseur_id
    ).group_by(models.Fournisseur.id).all()
    
    return fournisseurs_stats

def synchroniser_relations_hierarchiques(db: Session):
    """Synchroniser les relations hiérarchiques Site > Lieu > Emplacement (fonction legacy - plus nécessaire)"""
    # Cette fonction n'est plus nécessaire car nous n'avons plus de colonnes texte
    # Tous les produits sont créés directement avec les bonnes relations
    print("Synchronisation hiérarchique: Plus nécessaire avec le nouveau modèle de données")
    return {
        "sites_lies": 0,
        "lieux_lies": 0,
        "emplacements_lies": 0,
        "total_produits": db.query(models.Inventaire).count(),
        "message": "Synchronisation non nécessaire - tous les produits utilisent déjà les relations par ID"
    }

def get_sites_avec_stats(db: Session):
    """Récupérer tous les sites avec leurs statistiques de produits"""
    sites = db.query(models.Site).all()
    
    sites_avec_stats = []
    for site in sites:
        # Compter les produits liés par relation
        nb_produits_lies = db.query(models.Inventaire).filter(
            models.Inventaire.site_id == site.id
        ).count()
        
        site_dict = {
            "id": site.id,
            "code_site": site.code_site,
            "nom_site": site.nom_site,
            "adresse": site.adresse,
            "ville": site.ville,
            "responsable": site.responsable,
            "statut": site.statut,
            "nb_produits_lies": nb_produits_lies,
            "date_creation": site.date_creation.isoformat() if site.date_creation else None
        }
        sites_avec_stats.append(site_dict)
    
    return sites_avec_stats

def get_lieux_avec_stats(db: Session):
    """Récupérer tous les lieux avec leurs statistiques de produits"""
    lieux = db.query(models.Lieu).all()
    
    lieux_avec_stats = []
    for lieu in lieux:
        # Compter les produits liés par relation
        nb_produits_lies = db.query(models.Inventaire).filter(
            models.Inventaire.lieu_id == lieu.id
        ).count()
        
        lieu_dict = {
            "id": lieu.id,
            "code_lieu": lieu.code_lieu,
            "nom_lieu": lieu.nom_lieu,
            "site_id": lieu.site_id,
            "type_lieu": lieu.type_lieu,
            "niveau": lieu.niveau,
            "responsable": lieu.responsable,
            "statut": lieu.statut,
            "nb_produits_lies": nb_produits_lies,
            "date_creation": lieu.date_creation.isoformat() if lieu.date_creation else None
        }
        lieux_avec_stats.append(lieu_dict)
    
    return lieux_avec_stats

def get_emplacements_avec_stats(db: Session):
    """Récupérer tous les emplacements avec leurs statistiques de produits"""
    emplacements = db.query(models.Emplacement).all()
    
    emplacements_avec_stats = []
    for emplacement in emplacements:
        # Compter les produits liés par relation
        nb_produits_lies = db.query(models.Inventaire).filter(
            models.Inventaire.emplacement_id == emplacement.id
        ).count()
        
        emplacement_dict = {
            "id": emplacement.id,
            "code_emplacement": emplacement.code_emplacement,
            "nom_emplacement": emplacement.nom_emplacement,
            "lieu_id": emplacement.lieu_id,
            "type_emplacement": emplacement.type_emplacement,
            "position": emplacement.position,
            "capacite_max": emplacement.capacite_max,
            "responsable": emplacement.responsable,
            "statut": emplacement.statut,
            "nb_produits_lies": nb_produits_lies,
            "taux_occupation": float(emplacement.taux_occupation) if emplacement.taux_occupation else 0,
            "date_creation": emplacement.date_creation.isoformat() if emplacement.date_creation else None
        }
        emplacements_avec_stats.append(emplacement_dict)
    
    return emplacements_avec_stats

def enrichir_produit_avec_noms(db: Session, produit):
    """Enrichir un produit avec les noms des entités liées via les relations"""
    produit_dict = {
        'id': produit.id,
        'code': produit.code,
        'reference_fournisseur': produit.reference_fournisseur,
        'produits': produit.produits,
        'stock_min': produit.stock_min,
        'stock_max': produit.stock_max,
        'prix_unitaire': float(produit.prix_unitaire) if produit.prix_unitaire else 0,
        'categorie': produit.categorie,
        'secteur': produit.secteur,
        'reference': produit.reference,
        'quantite': produit.quantite,
        'date_entree': produit.date_entree.isoformat() if produit.date_entree else None,
        'created_at': produit.created_at.isoformat() if produit.created_at else None,
        'updated_at': produit.updated_at.isoformat() if produit.updated_at else None,
        
        # IDs des relations
        'site_id': produit.site_id,
        'lieu_id': produit.lieu_id,
        'emplacement_id': produit.emplacement_id,
        'fournisseur_id': produit.fournisseur_id,
        'unite_stockage_id': produit.unite_stockage_id,
        'unite_commande_id': produit.unite_commande_id,
        
        # Noms des entités liées (pour compatibilité avec les templates)
        'site': produit.site_obj.nom_site if produit.site_obj else None,
        'lieu': produit.lieu_obj.nom_lieu if produit.lieu_obj else None,
        'emplacement': produit.emplacement_obj.nom_emplacement if produit.emplacement_obj else None,
        'fournisseur': produit.fournisseur_obj.nom_fournisseur if produit.fournisseur_obj else None,
        'unite_stockage': produit.unite_stockage_obj.nom_unite if produit.unite_stockage_obj else None,
        'unite_commande': produit.unite_commande_obj.nom_unite if produit.unite_commande_obj else None,
    }
    
    return produit_dict

def get_inventaire_enrichi(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer l'inventaire avec les noms des entités liées"""
    from sqlalchemy.orm import joinedload
    
    produits = db.query(models.Inventaire).options(
        joinedload(models.Inventaire.site_obj),
        joinedload(models.Inventaire.lieu_obj),
        joinedload(models.Inventaire.emplacement_obj),
        joinedload(models.Inventaire.fournisseur_obj),
        joinedload(models.Inventaire.unite_stockage_obj),
        joinedload(models.Inventaire.unite_commande_obj)
    ).offset(skip).limit(limit).all()
    
    return [enrichir_produit_avec_noms(db, produit) for produit in produits]

def get_inventaire_by_reference_enrichi(db: Session, reference: str):
    """Récupérer un produit par référence avec les noms des entités liées"""
    from sqlalchemy.orm import joinedload
    
    produit = db.query(models.Inventaire).options(
        joinedload(models.Inventaire.site_obj),
        joinedload(models.Inventaire.lieu_obj),
        joinedload(models.Inventaire.emplacement_obj),
        joinedload(models.Inventaire.fournisseur_obj),
        joinedload(models.Inventaire.unite_stockage_obj),
        joinedload(models.Inventaire.unite_commande_obj)
    ).filter(models.Inventaire.reference == reference).first()
    
    if produit:
        return enrichir_produit_avec_noms(db, produit)
    return None

def get_inventaire_by_fournisseur_enrichi(db: Session, fournisseur: str, skip: int = 0, limit: int = None):
    """Récupérer les produits d'un fournisseur avec noms des entités liées"""
    from sqlalchemy.orm import joinedload
    
    # Récupérer les produits de base via la relation avec toutes les relations chargées
    query = db.query(models.Inventaire).options(
        joinedload(models.Inventaire.site_obj),
        joinedload(models.Inventaire.lieu_obj),
        joinedload(models.Inventaire.emplacement_obj),
        joinedload(models.Inventaire.fournisseur_obj),
        joinedload(models.Inventaire.unite_stockage_obj),
        joinedload(models.Inventaire.unite_commande_obj)
    ).join(
        models.Fournisseur, models.Inventaire.fournisseur_id == models.Fournisseur.id
    ).filter(models.Fournisseur.nom_fournisseur == fournisseur)
    
    # Appliquer la pagination si demandée
    if limit is not None:
        query = query.offset(skip).limit(limit)
    
    produits = query.all()
    
    # Enrichir chaque produit avec les noms des entités liées
    return [enrichir_produit_avec_noms(db, produit) for produit in produits]

def search_inventaire_enrichi(db: Session, search: str, skip: int = 0, limit: int = 100):
    """Rechercher des produits enrichis dans l'inventaire"""
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_
    
    # Faire la recherche avec les relations chargées
    produits = db.query(models.Inventaire).options(
        joinedload(models.Inventaire.site_obj),
        joinedload(models.Inventaire.lieu_obj),
        joinedload(models.Inventaire.emplacement_obj),
        joinedload(models.Inventaire.fournisseur_obj),
        joinedload(models.Inventaire.unite_stockage_obj),
        joinedload(models.Inventaire.unite_commande_obj)
    ).filter(
        or_(
            models.Inventaire.produits.ilike(f"%{search}%"),
            models.Inventaire.reference.ilike(f"%{search}%"),
            models.Inventaire.code.ilike(f"%{search}%"),
            models.Inventaire.categorie.ilike(f"%{search}%"),
            # Recherche dans les noms des entités liées via les relations
            models.Inventaire.site_obj.has(models.Site.nom_site.ilike(f"%{search}%")),
            models.Inventaire.lieu_obj.has(models.Lieu.nom_lieu.ilike(f"%{search}%")),
            models.Inventaire.emplacement_obj.has(models.Emplacement.nom_emplacement.ilike(f"%{search}%")),
            models.Inventaire.fournisseur_obj.has(models.Fournisseur.nom_fournisseur.ilike(f"%{search}%")),
            models.Inventaire.unite_stockage_obj.has(models.UniteStockage.nom_unite.ilike(f"%{search}%")),
            models.Inventaire.unite_commande_obj.has(models.UniteCommande.nom_unite.ilike(f"%{search}%"))
        )
    ).offset(skip).limit(limit).all()
    
    return [enrichir_produit_avec_noms(db, produit) for produit in produits]

def calculate_stock_stats_db(db: Session, fournisseur: str = None):
    """Calculer les statistiques de stock directement en base de données"""
    from sqlalchemy import func, case
    
    # Base query
    query = db.query(models.Inventaire)
    
    # Filtrer par fournisseur si spécifié
    if fournisseur:
        query = query.join(
            models.Fournisseur, models.Inventaire.fournisseur_id == models.Fournisseur.id
        ).filter(models.Fournisseur.nom_fournisseur == fournisseur)
    
    # Calculer les statistiques avec des requêtes SQL optimisées
    stats_query = query.with_entities(
        func.count(models.Inventaire.id).label('total_produits'),
        func.sum(
            case(
                (models.Inventaire.quantite < models.Inventaire.stock_min, 1),
                else_=0
            )
        ).label('stock_critique'),
        func.sum(
            case(
                (
                    (models.Inventaire.quantite >= models.Inventaire.stock_min) &
                    (models.Inventaire.quantite <= (models.Inventaire.stock_min + (models.Inventaire.stock_max - models.Inventaire.stock_min) * 0.3)), 1
                ),
                else_=0
            )
        ).label('stock_faible'),
        func.sum(
            case(
                (models.Inventaire.quantite > models.Inventaire.stock_max, 1),
                else_=0
            )
        ).label('surstock'),
        func.sum(
            case(
                (
                    (models.Inventaire.quantite >= models.Inventaire.stock_min) &
                    (models.Inventaire.quantite <= models.Inventaire.stock_max) &
                    (models.Inventaire.quantite > (models.Inventaire.stock_min + (models.Inventaire.stock_max - models.Inventaire.stock_min) * 0.3)), 1
                ),
                else_=0
            )
        ).label('stock_normal'),
        func.sum(models.Inventaire.prix_unitaire * models.Inventaire.quantite).label('valeur_totale')
    ).first()
    
    return {
        'total_produits': stats_query.total_produits or 0,
        'stock_critique': stats_query.stock_critique or 0,
        'stock_faible': stats_query.stock_faible or 0,
        'surstock': stats_query.surstock or 0,
        'stock_normal': stats_query.stock_normal or 0,
        'valeur_totale': float(stats_query.valeur_totale or 0)
    }

# =====================================================
# CRUD POUR UTILISATEURS (AUTHENTIFICATION)
# =====================================================

def get_utilisateur_by_username(db: Session, username: str):
    """Récupérer un utilisateur par son nom d'utilisateur"""
    return db.query(models.Utilisateur).filter(models.Utilisateur.username == username).first()

def get_utilisateur_by_email(db: Session, email: str):
    """Récupérer un utilisateur par son email"""
    return db.query(models.Utilisateur).filter(models.Utilisateur.email == email).first()

def get_utilisateur_by_id(db: Session, user_id: int):
    """Récupérer un utilisateur par son ID"""
    return db.query(models.Utilisateur).filter(models.Utilisateur.id == user_id).first()

def get_utilisateurs(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les utilisateurs"""
    return db.query(models.Utilisateur).offset(skip).limit(limit).all()

def create_utilisateur(db: Session, utilisateur: schemas.UtilisateurCreate):
    """Créer un nouvel utilisateur avec mot de passe hashé"""
    from auth import get_password_hash
    
    # Vérifier si l'username existe déjà
    if get_utilisateur_by_username(db, utilisateur.username):
        raise ValueError("Nom d'utilisateur déjà utilisé")
    
    # Vérifier si l'email existe déjà
    if get_utilisateur_by_email(db, utilisateur.email):
        raise ValueError("Email déjà utilisé")
    
    # Créer l'utilisateur avec le mot de passe hashé
    utilisateur_data = utilisateur.model_dump()
    hashed_password = get_password_hash(utilisateur_data.pop('password'))
    
    db_utilisateur = models.Utilisateur(
        **utilisateur_data,
        hashed_password=hashed_password
    )
    
    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur

def update_utilisateur(db: Session, user_id: int, utilisateur: schemas.UtilisateurUpdate):
    """Mettre à jour un utilisateur"""
    db_utilisateur = get_utilisateur_by_id(db, user_id)
    if db_utilisateur:
        update_data = utilisateur.model_dump(exclude_unset=True)
        
        # Vérifier si le nouvel email existe déjà (sauf pour l'utilisateur actuel)
        if 'email' in update_data:
            existing_user = get_utilisateur_by_email(db, update_data['email'])
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email déjà utilisé")
        
        for field, value in update_data.items():
            setattr(db_utilisateur, field, value)
        
        db.commit()
        db.refresh(db_utilisateur)
    return db_utilisateur

def delete_utilisateur(db: Session, user_id: int):
    """Supprimer un utilisateur"""
    db_utilisateur = get_utilisateur_by_id(db, user_id)
    if db_utilisateur:
        db.delete(db_utilisateur)
        db.commit()
    return db_utilisateur

def change_password(db: Session, user_id: int, old_password: str, new_password: str):
    """Changer le mot de passe d'un utilisateur"""
    from auth import verify_password, get_password_hash
    
    db_utilisateur = get_utilisateur_by_id(db, user_id)
    if not db_utilisateur:
        raise ValueError("Utilisateur non trouvé")
    
    # Vérifier l'ancien mot de passe
    if not verify_password(old_password, db_utilisateur.hashed_password):
        raise ValueError("Ancien mot de passe incorrect")
    
    # Mettre à jour avec le nouveau mot de passe hashé
    db_utilisateur.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur

def update_last_login(db: Session, user_id: int):
    """Mettre à jour la date de dernière connexion"""
    db_utilisateur = get_utilisateur_by_id(db, user_id)
    if db_utilisateur:
        db_utilisateur.derniere_connexion = datetime.utcnow()
        db.commit()
        db.refresh(db_utilisateur)
    return db_utilisateur

# =====================================================
# CRUD POUR UNITÉS DE STOCKAGE
# =====================================================

def get_unites_stockage(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer toutes les unités de stockage"""
    return db.query(models.UniteStockage).offset(skip).limit(limit).all()

def get_unite_stockage_by_id(db: Session, unite_id: int):
    """Récupérer une unité de stockage par son ID"""
    return db.query(models.UniteStockage).filter(models.UniteStockage.id == unite_id).first()

def get_unite_stockage_by_code(db: Session, code_unite: str):
    """Récupérer une unité de stockage par son code"""
    return db.query(models.UniteStockage).filter(models.UniteStockage.code_unite == code_unite).first()

def get_unite_stockage_by_nom(db: Session, nom_unite: str):
    """Récupérer une unité de stockage par son nom"""
    return db.query(models.UniteStockage).filter(models.UniteStockage.nom_unite == nom_unite).first()

def get_unites_stockage_actives(db: Session):
    """Récupérer toutes les unités de stockage actives"""
    return db.query(models.UniteStockage).filter(models.UniteStockage.statut == 'Actif').all()

def create_unite_stockage(db: Session, unite: schemas.UniteStockageCreate):
    """Créer une nouvelle unité de stockage"""
    db_unite = models.UniteStockage(**unite.model_dump())
    db.add(db_unite)
    db.commit()
    db.refresh(db_unite)
    return db_unite

def update_unite_stockage(db: Session, unite_id: int, unite: schemas.UniteStockageUpdate):
    """Mettre à jour une unité de stockage"""
    db_unite = db.query(models.UniteStockage).filter(models.UniteStockage.id == unite_id).first()
    if db_unite:
        update_data = unite.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_unite, field, value)
        db.commit()
        db.refresh(db_unite)
    return db_unite

def delete_unite_stockage(db: Session, unite_id: int):
    """Supprimer une unité de stockage"""
    db_unite = db.query(models.UniteStockage).filter(models.UniteStockage.id == unite_id).first()
    if db_unite:
        db.delete(db_unite)
        db.commit()
    return db_unite

# =====================================================
# CRUD POUR UNITÉS DE COMMANDE
# =====================================================

def get_unites_commande(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer toutes les unités de commande"""
    return db.query(models.UniteCommande).offset(skip).limit(limit).all()

def get_unite_commande_by_id(db: Session, unite_id: int):
    """Récupérer une unité de commande par son ID"""
    return db.query(models.UniteCommande).filter(models.UniteCommande.id == unite_id).first()

def get_unite_commande_by_code(db: Session, code_unite: str):
    """Récupérer une unité de commande par son code"""
    return db.query(models.UniteCommande).filter(models.UniteCommande.code_unite == code_unite).first()

def get_unite_commande_by_nom(db: Session, nom_unite: str):
    """Récupérer une unité de commande par son nom"""
    return db.query(models.UniteCommande).filter(models.UniteCommande.nom_unite == nom_unite).first()

def get_unites_commande_actives(db: Session):
    """Récupérer toutes les unités de commande actives"""
    return db.query(models.UniteCommande).filter(models.UniteCommande.statut == 'Actif').all()

def create_unite_commande(db: Session, unite: schemas.UniteCommandeCreate):
    """Créer une nouvelle unité de commande"""
    db_unite = models.UniteCommande(**unite.model_dump())
    db.add(db_unite)
    db.commit()
    db.refresh(db_unite)
    return db_unite

def update_unite_commande(db: Session, unite_id: int, unite: schemas.UniteCommandeUpdate):
    """Mettre à jour une unité de commande"""
    db_unite = db.query(models.UniteCommande).filter(models.UniteCommande.id == unite_id).first()
    if db_unite:
        update_data = unite.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_unite, field, value)
        db.commit()
        db.refresh(db_unite)
    return db_unite

def delete_unite_commande(db: Session, unite_id: int):
    """Supprimer une unité de commande"""
    db_unite = db.query(models.UniteCommande).filter(models.UniteCommande.id == unite_id).first()
    if db_unite:
        db.delete(db_unite)
        db.commit()
    return db_unite

# =====================================================
# CRUD POUR GESTION DES DEMANDES - WORKFLOW
# =====================================================

def update_demande_statut(db: Session, demande_id: int, nouveau_statut: str, traite_par: str = None, commentaire: str = None):
    """Met à jour le statut d'une demande"""
    demande = db.query(models.Demande).filter(models.Demande.id == demande_id).first()
    if not demande:
        return None
    
    demande.statut = nouveau_statut
    if traite_par:
        demande.traite_par = traite_par
    if commentaire:
        demande.commentaires = commentaire
    
    # Mettre à jour la date de traitement si c'est une validation/rejet
    if nouveau_statut in ['Approuvée', 'Rejetée']:
        from datetime import datetime
        demande.date_traitement = datetime.now()
    
    db.commit()
    db.refresh(demande)
    return demande

def get_demandes_by_id_base(db: Session, id_demande_base: str):
    """Récupère toutes les demandes d'un même panier (id_demande_base)"""
    return db.query(models.Demande).filter(models.Demande.id_demande_base == id_demande_base).all()

def approuver_demande_panier(db: Session, id_demande_base: str, traite_par: str):
    """Approuve toutes les demandes d'un même panier"""
    demandes = get_demandes_by_id_base(db, id_demande_base)
    if not demandes:
        return None
    
    # Approuver toutes les demandes du panier
    for demande in demandes:
        if demande.statut == 'En attente':
            demande.statut = 'Approuvée'
            demande.traite_par = traite_par
            from datetime import datetime
            demande.date_traitement = datetime.now()
    
    db.commit()
    return demandes

def rejeter_demande_panier(db: Session, id_demande_base: str, traite_par: str, commentaire: str = None):
    """Rejette toutes les demandes d'un même panier"""
    demandes = get_demandes_by_id_base(db, id_demande_base)
    if not demandes:
        return None
    
    # Rejeter toutes les demandes du panier
    for demande in demandes:
        if demande.statut == 'En attente':
            demande.statut = 'Rejetée'
            demande.traite_par = traite_par
            if commentaire:
                demande.commentaires = commentaire
            from datetime import datetime
            demande.date_traitement = datetime.now()
    
    db.commit()
    return demandes

def traiter_demande_panier(db: Session, id_demande_base: str, traite_par: str):
    """Met en cours de traitement toutes les demandes approuvées d'un panier"""
    demandes = get_demandes_by_id_base(db, id_demande_base)
    if not demandes:
        return None
    
    # Vérifier que toutes les demandes sont approuvées
    for demande in demandes:
        if demande.statut != 'Approuvée':
            return None
    
    # Mettre en cours de traitement
    for demande in demandes:
        demande.statut = 'En cours'
        demande.traite_par = traite_par
        from datetime import datetime
        demande.date_traitement = datetime.now()
    
    db.commit()
    return demandes

# =====================================================
# CRUD POUR GESTION DE LA PRÉPARATION AVEC SCAN
# =====================================================

def get_or_create_preparation(db: Session, id_demande_base: str, prepare_par: str):
    """Récupère ou crée une préparation pour un panier de demandes"""
    preparation = db.query(models.PreparationDemande).filter(
        models.PreparationDemande.id_demande_base == id_demande_base
    ).first()
    
    if not preparation:
        # Compter le nombre de produits dans le panier
        demandes = get_demandes_by_id_base(db, id_demande_base)
        if not demandes:
            return None
            
        preparation = models.PreparationDemande(
            id_demande_base=id_demande_base,
            statut_preparation='Non commencée',
            prepare_par=prepare_par,
            nb_produits_total=len(demandes),
            nb_produits_scannes=0
        )
        db.add(preparation)
        db.commit()
        db.refresh(preparation)
    
    return preparation

def get_produits_scannes(db: Session, preparation_id: int):
    """Récupère la liste des produits déjà scannés pour une préparation"""
    return db.query(models.ProduitScanne).filter(
        models.ProduitScanne.preparation_id == preparation_id
    ).all()

def scanner_produit(db: Session, id_demande_base: str, reference_produit: str, scanne_par: str):
    """Scanne un produit lors de la préparation"""
    from datetime import datetime
    
    # Récupérer ou créer la préparation
    preparation = get_or_create_preparation(db, id_demande_base, scanne_par)
    if not preparation:
        return None
    
    # Vérifier que le produit fait partie de la demande
    demandes = get_demandes_by_id_base(db, id_demande_base)
    references_demandees = [d.reference_produit for d in demandes]
    
    if reference_produit not in references_demandees:
        return {'error': 'Produit non trouvé dans cette demande'}
    
    # Vérifier que le produit n'est pas déjà scanné
    produit_deja_scanne = db.query(models.ProduitScanne).filter(
        models.ProduitScanne.preparation_id == preparation.id,
        models.ProduitScanne.reference_produit == reference_produit
    ).first()
    
    if produit_deja_scanne:
        return {'error': 'Produit déjà scanné'}
    
    # Ajouter le scan
    nouveau_scan = models.ProduitScanne(
        preparation_id=preparation.id,
        reference_produit=reference_produit,
        scanne_par=scanne_par,
        date_scan=datetime.now()
    )
    db.add(nouveau_scan)
    
    # Mettre à jour le compteur
    preparation.nb_produits_scannes += 1
    
    # Si c'est le premier scan, mettre la préparation en cours et changer le statut des demandes
    if preparation.nb_produits_scannes == 1:
        preparation.statut_preparation = 'En cours'
        preparation.date_debut_preparation = datetime.now()
        
        # Mettre à jour le statut des demandes à "En cours"
        for demande in demandes:
            if demande.statut == 'Approuvée':
                demande.statut = 'En cours'
                demande.traite_par = scanne_par
                demande.date_traitement = datetime.now()
    
    db.commit()
    db.refresh(preparation)
    
    return {
        'success': True,
        'preparation': preparation,
        'produits_scannes': preparation.nb_produits_scannes,
        'produits_total': preparation.nb_produits_total
    }

def valider_preparation(db: Session, id_demande_base: str, prepare_par: str):
    """Valide la préparation une fois tous les produits scannés"""
    from datetime import datetime
    
    preparation = db.query(models.PreparationDemande).filter(
        models.PreparationDemande.id_demande_base == id_demande_base
    ).first()
    
    if not preparation:
        return {'error': 'Préparation non trouvée'}
    
    if preparation.nb_produits_scannes != preparation.nb_produits_total:
        return {'error': 'Tous les produits doivent être scannés avant validation'}
    
    if preparation.statut_preparation == 'Validée':
        return {'error': 'Préparation déjà validée'}
    
    preparation.statut_preparation = 'Validée'
    preparation.date_validation_preparation = datetime.now()
    
    db.commit()
    
    return {'success': True, 'preparation': preparation}

def livrer_demande_panier(db: Session, id_demande_base: str, traite_par: str):
    """Livre les demandes et retire du stock - AVEC VALIDATION DE PRÉPARATION"""
    from datetime import datetime
    
    # Vérifier que la préparation est validée
    preparation = db.query(models.PreparationDemande).filter(
        models.PreparationDemande.id_demande_base == id_demande_base
    ).first()
    
    if not preparation:
        return {'error': 'Aucune préparation trouvée pour cette demande'}
    
    if preparation.statut_preparation != 'Validée':
        return {'error': 'La préparation doit être validée avant la livraison'}
    
    # Vérifier que tous les produits ont été scannés
    if preparation.nb_produits_scannes != preparation.nb_produits_total:
        return {'error': 'Tous les produits doivent être scannés avant la livraison'}
    
    demandes = get_demandes_by_id_base(db, id_demande_base)
    if not demandes:
        return {'error': 'Demandes non trouvées'}
    
    # Vérifier que toutes les demandes sont en cours
    for demande in demandes:
        if demande.statut != 'En cours':
            return {'error': f'La demande {demande.id_demande} n\'est pas en cours de traitement'}
    
    # Vérifier que tous les produits demandés ont été scannés
    produits_scannes = get_produits_scannes(db, preparation.id)
    references_scannees = [p.reference_produit for p in produits_scannes]
    
    for demande in demandes:
        if demande.reference_produit not in references_scannees:
            return {'error': f'Le produit {demande.reference_produit} n\'a pas été scanné'}
    
    # Livrer chaque produit
    resultats = []
    for demande in demandes:
        # Mettre à jour le statut
        demande.statut = 'Terminée'
        demande.traite_par = traite_par
        demande.date_traitement = datetime.now()
        
        # Retirer du stock (utiliser Inventaire au lieu de Produit)
        produit = db.query(models.Inventaire).filter(models.Inventaire.reference == demande.reference_produit).first()
        if produit:
            quantite_avant = produit.quantite
            quantite_apres = max(0, produit.quantite - demande.quantite_demandee)
            produit.quantite = quantite_apres
            
            # Créer un historique de mouvement avec informations détaillées
            try:
                motif_detaille = (
                    f"DEMANDE MATÉRIEL | "
                    f"ID: {demande.id_demande_base} | "
                    f"Demandeur: {demande.demandeur} | "
                    f"Table: {demande.table_atelier} | "
                    f"Livré par: {traite_par} | "
                    f"Statut: Livraison avec scan validé"
                )
                if demande.commentaires:
                    motif_detaille += f" | Commentaires: {demande.commentaires}"
                
                historique = models.Historique(
                    date_mouvement=datetime.now(),
                    reference=demande.reference_produit,
                    produit=demande.designation_produit or produit.produits,
                    nature='Sortie',
                    quantite_mouvement=demande.quantite_demandee,
                    quantite_avant=quantite_avant,
                    quantite_apres=quantite_apres,
                    motif=motif_detaille
                )
                db.add(historique)
            except Exception as e:
                print(f"Erreur lors de la création de l'historique: {e}")
            
            resultats.append({
                'reference': demande.reference_produit,
                'quantite_retiree': demande.quantite_demandee,
                'stock_avant': quantite_avant,
                'stock_apres': quantite_apres
            })
        else:
            print(f"Produit non trouvé pour la référence: {demande.reference_produit}")
    
    # Marquer la préparation comme livrée
    preparation.statut_preparation = 'Livrée'
    preparation.date_livraison = datetime.now()
    
    db.commit()
    return {'success': True, 'demandes': demandes, 'mouvements': resultats}

def get_demandes_pretes_livraison_table(db: Session, id_table: str):
    """
    Récupérer les demandes prêtes à être livrées pour une table d'atelier spécifique
    (statut 'Approuvée', préparation validée mais pas encore livrée)
    """
    # Récupérer les demandes approuvées pour cette table avec préparation validée
    demandes_query = db.query(models.Demande).join(
        models.PreparationDemande,
        models.Demande.id_demande_base == models.PreparationDemande.id_demande_base
    ).filter(
        models.Demande.id_table == id_table,
        models.Demande.statut == 'En cours',  # Les demandes en cours avec préparation validée
        models.PreparationDemande.statut_preparation == 'Validée'
    )
    
    # Grouper par id_demande_base pour éviter les doublons
    demandes_groupees = {}
    for demande in demandes_query.all():
        if demande.id_demande_base not in demandes_groupees:
            demandes_groupees[demande.id_demande_base] = {
                'id_demande_base': demande.id_demande_base,
                'demandeur': demande.demandeur,
                'date_demande': demande.date_demande,
                'commentaires': demande.commentaires,
                'produits': [],
                'total_produits': 0
            }
        
        # Ajouter le produit au groupe
        demandes_groupees[demande.id_demande_base]['produits'].append({
            'reference_produit': demande.reference_produit,
            'produits': demande.designation_produit,
            'quantite_demandee': demande.quantite_demandee,
            'unite_stockage': demande.unite
        })
        demandes_groupees[demande.id_demande_base]['total_produits'] += 1
    
    return list(demandes_groupees.values()) 