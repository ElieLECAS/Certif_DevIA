from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import models
import schemas
from database import SessionLocal, engine, get_db

# Créer les tables
models.Base.metadata.create_all(bind=engine)

# Initialiser FastAPI
app = FastAPI(
    title="GMAO - API de Gestion de Stock",
    description="API pour la gestion de stock dans le système GMAO - Compatible avec l'application Streamlit",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ROUTES POUR L'INVENTAIRE (PRODUITS)
# =====================================================

@app.get("/inventaire/", response_model=List[schemas.InventaireResponse])
def read_inventaire(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les produits de l'inventaire"""
    inventaire = crud.get_inventaire(db, skip=skip, limit=limit)
    return inventaire

@app.post("/inventaire/", response_model=schemas.InventaireResponse)
def create_inventaire(inventaire: schemas.InventaireCreate, db: Session = Depends(get_db)):
    """Créer un nouveau produit dans l'inventaire"""
    # Vérifier si la référence existe déjà
    db_inventaire = crud.get_inventaire_by_reference(db, reference=inventaire.reference)
    if db_inventaire:
        raise HTTPException(status_code=400, detail="Un produit avec cette référence existe déjà")
    
    # Vérifier si le code existe déjà
    db_inventaire_code = crud.get_inventaire_by_code(db, code=inventaire.code)
    if db_inventaire_code:
        raise HTTPException(status_code=400, detail="Un produit avec ce code existe déjà")
    
    return crud.create_inventaire(db=db, inventaire=inventaire)

@app.get("/inventaire/{inventaire_id}", response_model=schemas.InventaireResponse)
def read_inventaire_by_id(inventaire_id: int, db: Session = Depends(get_db)):
    """Récupérer un produit par son ID"""
    db_inventaire = crud.get_inventaire_by_id(db, inventaire_id=inventaire_id)
    if db_inventaire is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return db_inventaire

@app.get("/inventaire/reference/{reference}", response_model=schemas.InventaireResponse)
def read_inventaire_by_reference(reference: str, db: Session = Depends(get_db)):
    """Récupérer un produit par sa référence QR"""
    db_inventaire = crud.get_inventaire_by_reference(db, reference=reference)
    if db_inventaire is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return db_inventaire

@app.get("/inventaire/code/{code}", response_model=schemas.InventaireResponse)
def read_inventaire_by_code(code: str, db: Session = Depends(get_db)):
    """Récupérer un produit par son code"""
    db_inventaire = crud.get_inventaire_by_code(db, code=code)
    if db_inventaire is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return db_inventaire

@app.get("/inventaire/search/", response_model=List[schemas.InventaireResponse])
def search_inventaire(
    search: str = Query(..., description="Terme de recherche"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Rechercher des produits par terme de recherche"""
    inventaire = crud.search_inventaire(db, search_term=search, skip=skip, limit=limit)
    return inventaire

@app.put("/inventaire/{inventaire_id}", response_model=schemas.InventaireResponse)
def update_inventaire(inventaire_id: int, inventaire: schemas.InventaireUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un produit de l'inventaire"""
    db_inventaire = crud.update_inventaire(db, inventaire_id=inventaire_id, inventaire=inventaire)
    if db_inventaire is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return db_inventaire

@app.delete("/inventaire/{inventaire_id}")
def delete_inventaire(inventaire_id: int, db: Session = Depends(get_db)):
    """Supprimer un produit de l'inventaire"""
    db_inventaire = crud.delete_inventaire(db, inventaire_id=inventaire_id)
    if db_inventaire is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"message": "Produit supprimé avec succès"}

@app.get("/inventaire/emplacement/{emplacement}", response_model=List[schemas.InventaireResponse])
def read_inventaire_by_emplacement(emplacement: str, db: Session = Depends(get_db)):
    """Récupérer tous les produits d'un emplacement"""
    inventaire = crud.get_inventaire_by_emplacement(db, emplacement=emplacement)
    return inventaire

@app.get("/inventaire/fournisseur/{fournisseur}", response_model=List[schemas.InventaireResponse])
def read_inventaire_by_fournisseur(fournisseur: str, db: Session = Depends(get_db)):
    """Récupérer tous les produits d'un fournisseur"""
    inventaire = crud.get_inventaire_by_fournisseur(db, fournisseur=fournisseur)
    return inventaire

@app.get("/inventaire/stock-faible/", response_model=List[schemas.InventaireResponse])
def read_inventaire_stock_faible(db: Session = Depends(get_db)):
    """Récupérer les produits avec un stock faible"""
    inventaire = crud.get_inventaire_stock_faible(db)
    return inventaire

# =====================================================
# ROUTES POUR LES FOURNISSEURS
# =====================================================

@app.get("/fournisseurs/", response_model=List[schemas.FournisseurResponse])
def read_fournisseurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les fournisseurs"""
    fournisseurs = crud.get_fournisseurs(db, skip=skip, limit=limit)
    return fournisseurs

@app.post("/fournisseurs/", response_model=schemas.FournisseurResponse)
def create_fournisseur(fournisseur: schemas.FournisseurCreate, db: Session = Depends(get_db)):
    """Créer un nouveau fournisseur"""
    # Vérifier si l'ID fournisseur existe déjà
    db_fournisseur = crud.get_fournisseur_by_id_fournisseur(db, id_fournisseur=fournisseur.id_fournisseur)
    if db_fournisseur:
        raise HTTPException(status_code=400, detail="Un fournisseur avec cet ID existe déjà")
    
    return crud.create_fournisseur(db=db, fournisseur=fournisseur)

@app.get("/fournisseurs/{fournisseur_id}", response_model=schemas.FournisseurResponse)
def read_fournisseur(fournisseur_id: int, db: Session = Depends(get_db)):
    """Récupérer un fournisseur par son ID"""
    db_fournisseur = crud.get_fournisseur_by_id(db, fournisseur_id=fournisseur_id)
    if db_fournisseur is None:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return db_fournisseur

@app.get("/fournisseurs/id/{id_fournisseur}", response_model=schemas.FournisseurResponse)
def read_fournisseur_by_id_fournisseur(id_fournisseur: str, db: Session = Depends(get_db)):
    """Récupérer un fournisseur par son ID fournisseur"""
    db_fournisseur = crud.get_fournisseur_by_id_fournisseur(db, id_fournisseur=id_fournisseur)
    if db_fournisseur is None:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return db_fournisseur

@app.put("/fournisseurs/{fournisseur_id}", response_model=schemas.FournisseurResponse)
def update_fournisseur(fournisseur_id: int, fournisseur: schemas.FournisseurUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un fournisseur"""
    db_fournisseur = crud.update_fournisseur(db, fournisseur_id=fournisseur_id, fournisseur=fournisseur)
    if db_fournisseur is None:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return db_fournisseur

@app.delete("/fournisseurs/{fournisseur_id}")
def delete_fournisseur(fournisseur_id: int, db: Session = Depends(get_db)):
    """Supprimer un fournisseur"""
    db_fournisseur = crud.delete_fournisseur(db, fournisseur_id=fournisseur_id)
    if db_fournisseur is None:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return {"message": "Fournisseur supprimé avec succès"}

# =====================================================
# ROUTES POUR LA HIÉRARCHIE SITE > LIEU > EMPLACEMENT
# =====================================================

# SITES
@app.get("/sites/", response_model=List[schemas.SiteResponse])
def read_sites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les sites"""
    sites = crud.get_sites(db, skip=skip, limit=limit)
    return sites

@app.post("/sites/", response_model=schemas.SiteResponse)
def create_site(site: schemas.SiteCreate, db: Session = Depends(get_db)):
    """Créer un nouveau site"""
    # Vérifier si le code site existe déjà
    db_site = crud.get_site_by_code(db, code_site=site.code_site)
    if db_site:
        raise HTTPException(status_code=400, detail="Un site avec ce code existe déjà")
    
    return crud.create_site(db=db, site=site)

@app.get("/sites/{site_id}", response_model=schemas.SiteResponse)
def read_site(site_id: int, db: Session = Depends(get_db)):
    """Récupérer un site par son ID"""
    db_site = crud.get_site_by_id(db, site_id=site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return db_site

@app.put("/sites/{site_id}", response_model=schemas.SiteResponse)
def update_site(site_id: int, site: schemas.SiteUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un site"""
    db_site = crud.update_site(db, site_id=site_id, site=site)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return db_site

@app.delete("/sites/{site_id}")
def delete_site(site_id: int, db: Session = Depends(get_db)):
    """Supprimer un site"""
    db_site = crud.delete_site(db, site_id=site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return {"message": "Site supprimé avec succès"}

# LIEUX
@app.get("/lieux/", response_model=List[schemas.LieuResponse])
def read_lieux(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les lieux"""
    lieux = crud.get_lieux(db, skip=skip, limit=limit)
    return lieux

@app.get("/lieux/site/{site_id}", response_model=List[schemas.LieuResponse])
def read_lieux_by_site(site_id: int, db: Session = Depends(get_db)):
    """Récupérer tous les lieux d'un site"""
    lieux = crud.get_lieux_by_site(db, site_id=site_id)
    return lieux

@app.post("/lieux/", response_model=schemas.LieuResponse)
def create_lieu(lieu: schemas.LieuCreate, db: Session = Depends(get_db)):
    """Créer un nouveau lieu"""
    # Vérifier si le code lieu existe déjà
    db_lieu = crud.get_lieu_by_code(db, code_lieu=lieu.code_lieu)
    if db_lieu:
        raise HTTPException(status_code=400, detail="Un lieu avec ce code existe déjà")
    
    # Vérifier que le site existe
    db_site = crud.get_site_by_id(db, site_id=lieu.site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    return crud.create_lieu(db=db, lieu=lieu)

@app.get("/lieux/{lieu_id}", response_model=schemas.LieuResponse)
def read_lieu(lieu_id: int, db: Session = Depends(get_db)):
    """Récupérer un lieu par son ID"""
    db_lieu = crud.get_lieu_by_id(db, lieu_id=lieu_id)
    if db_lieu is None:
        raise HTTPException(status_code=404, detail="Lieu non trouvé")
    return db_lieu

@app.put("/lieux/{lieu_id}", response_model=schemas.LieuResponse)
def update_lieu(lieu_id: int, lieu: schemas.LieuUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un lieu"""
    db_lieu = crud.update_lieu(db, lieu_id=lieu_id, lieu=lieu)
    if db_lieu is None:
        raise HTTPException(status_code=404, detail="Lieu non trouvé")
    return db_lieu

@app.delete("/lieux/{lieu_id}")
def delete_lieu(lieu_id: int, db: Session = Depends(get_db)):
    """Supprimer un lieu"""
    db_lieu = crud.delete_lieu(db, lieu_id=lieu_id)
    if db_lieu is None:
        raise HTTPException(status_code=404, detail="Lieu non trouvé")
    return {"message": "Lieu supprimé avec succès"}

# EMPLACEMENTS
@app.get("/emplacements/", response_model=List[schemas.EmplacementResponse])
def read_emplacements(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les emplacements"""
    emplacements = crud.get_emplacements(db, skip=skip, limit=limit)
    return emplacements

@app.get("/emplacements/lieu/{lieu_id}", response_model=List[schemas.EmplacementResponse])
def read_emplacements_by_lieu(lieu_id: int, db: Session = Depends(get_db)):
    """Récupérer tous les emplacements d'un lieu"""
    emplacements = crud.get_emplacements_by_lieu(db, lieu_id=lieu_id)
    return emplacements

@app.post("/emplacements/", response_model=schemas.EmplacementResponse)
def create_emplacement(emplacement: schemas.EmplacementCreate, db: Session = Depends(get_db)):
    """Créer un nouvel emplacement"""
    # Vérifier que le lieu existe
    db_lieu = crud.get_lieu_by_id(db, lieu_id=emplacement.lieu_id)
    if db_lieu is None:
        raise HTTPException(status_code=404, detail="Lieu non trouvé")
    
    return crud.create_emplacement(db=db, emplacement=emplacement)

@app.get("/emplacements/{emplacement_id}", response_model=schemas.EmplacementResponse)
def read_emplacement(emplacement_id: int, db: Session = Depends(get_db)):
    """Récupérer un emplacement par son ID"""
    db_emplacement = crud.get_emplacement_by_id(db, emplacement_id=emplacement_id)
    if db_emplacement is None:
        raise HTTPException(status_code=404, detail="Emplacement non trouvé")
    return db_emplacement

@app.put("/emplacements/{emplacement_id}", response_model=schemas.EmplacementResponse)
def update_emplacement(emplacement_id: int, emplacement: schemas.EmplacementUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un emplacement"""
    db_emplacement = crud.update_emplacement(db, emplacement_id=emplacement_id, emplacement=emplacement)
    if db_emplacement is None:
        raise HTTPException(status_code=404, detail="Emplacement non trouvé")
    return db_emplacement

@app.delete("/emplacements/{emplacement_id}")
def delete_emplacement(emplacement_id: int, db: Session = Depends(get_db)):
    """Supprimer un emplacement"""
    db_emplacement = crud.delete_emplacement(db, emplacement_id=emplacement_id)
    if db_emplacement is None:
        raise HTTPException(status_code=404, detail="Emplacement non trouvé")
    return {"message": "Emplacement supprimé avec succès"}

# ROUTES AVEC HIÉRARCHIE COMPLÈTE
@app.get("/emplacements-hierarchy/", response_model=List[schemas.EmplacementWithHierarchy])
def read_emplacements_with_hierarchy(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les emplacements avec leur hiérarchie complète"""
    results = crud.get_emplacements_with_hierarchy(db, skip=skip, limit=limit)
    
    emplacements_with_hierarchy = []
    for emplacement, lieu_nom, site_nom in results:
        emplacement_dict = {
            **emplacement.__dict__,
            "lieu_nom": lieu_nom,
            "site_nom": site_nom,
            "chemin_complet": f"{site_nom} > {lieu_nom} > {emplacement.nom_emplacement}"
        }
        emplacements_with_hierarchy.append(emplacement_dict)
    
    return emplacements_with_hierarchy

# =====================================================
# ROUTES POUR LES DEMANDES
# =====================================================

@app.get("/demandes/", response_model=List[schemas.DemandeResponse])
def read_demandes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les demandes"""
    demandes = crud.get_demandes(db, skip=skip, limit=limit)
    return demandes

@app.post("/demandes/", response_model=schemas.DemandeResponse)
def create_demande(demande: schemas.DemandeCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle demande"""
    # Vérifier si l'ID demande existe déjà
    db_demande = crud.get_demande_by_id_demande(db, id_demande=demande.id_demande)
    if db_demande:
        raise HTTPException(status_code=400, detail="Une demande avec cet ID existe déjà")
    
    return crud.create_demande(db=db, demande=demande)

@app.get("/demandes/{demande_id}", response_model=schemas.DemandeResponse)
def read_demande(demande_id: int, db: Session = Depends(get_db)):
    """Récupérer une demande par son ID"""
    db_demande = crud.get_demande_by_id(db, demande_id=demande_id)
    if db_demande is None:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return db_demande

@app.get("/demandes/statut/{statut}", response_model=List[schemas.DemandeResponse])
def read_demandes_by_statut(statut: str, db: Session = Depends(get_db)):
    """Récupérer les demandes par statut"""
    demandes = crud.get_demandes_by_statut(db, statut=statut)
    return demandes

@app.get("/demandes/demandeur/{demandeur}", response_model=List[schemas.DemandeResponse])
def read_demandes_by_demandeur(demandeur: str, db: Session = Depends(get_db)):
    """Récupérer les demandes par demandeur"""
    demandes = crud.get_demandes_by_demandeur(db, demandeur=demandeur)
    return demandes

@app.put("/demandes/{demande_id}", response_model=schemas.DemandeResponse)
def update_demande(demande_id: int, demande: schemas.DemandeUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une demande"""
    db_demande = crud.update_demande(db, demande_id=demande_id, demande=demande)
    if db_demande is None:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return db_demande

# =====================================================
# ROUTES POUR L'HISTORIQUE
# =====================================================

@app.get("/historique/", response_model=List[schemas.HistoriqueResponse])
def read_historique(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer l'historique des mouvements"""
    historique = crud.get_historique(db, skip=skip, limit=limit)
    return historique

@app.get("/historique/reference/{reference}", response_model=List[schemas.HistoriqueResponse])
def read_historique_by_reference(reference: str, db: Session = Depends(get_db)):
    """Récupérer l'historique d'un produit par sa référence"""
    historique = crud.get_historique_by_reference(db, reference=reference)
    return historique

@app.get("/historique/nature/{nature}", response_model=List[schemas.HistoriqueResponse])
def read_historique_by_nature(nature: str, db: Session = Depends(get_db)):
    """Récupérer l'historique par type de mouvement"""
    historique = crud.get_historique_by_nature(db, nature=nature)
    return historique

# =====================================================
# ROUTES POUR LES TABLES D'ATELIER
# =====================================================

@app.get("/tables-atelier/", response_model=List[schemas.TableAtelierResponse])
def read_tables_atelier(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les tables d'atelier"""
    tables = crud.get_tables_atelier(db, skip=skip, limit=limit)
    return tables

@app.post("/tables-atelier/", response_model=schemas.TableAtelierResponse)
def create_table_atelier(table: schemas.TableAtelierCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle table d'atelier"""
    # Vérifier si l'ID table existe déjà
    db_table = crud.get_table_atelier_by_id_table(db, id_table=table.id_table)
    if db_table:
        raise HTTPException(status_code=400, detail="Une table avec cet ID existe déjà")
    
    return crud.create_table_atelier(db=db, table=table)

@app.get("/tables-atelier/{table_id}", response_model=schemas.TableAtelierResponse)
def read_table_atelier(table_id: int, db: Session = Depends(get_db)):
    """Récupérer une table d'atelier par son ID"""
    db_table = crud.get_table_atelier_by_id(db, table_id=table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table d'atelier non trouvée")
    return db_table

@app.get("/tables-atelier/type/{type_atelier}", response_model=List[schemas.TableAtelierResponse])
def read_tables_atelier_by_type(type_atelier: str, db: Session = Depends(get_db)):
    """Récupérer les tables d'atelier par type"""
    tables = crud.get_tables_atelier_by_type(db, type_atelier=type_atelier)
    return tables

@app.put("/tables-atelier/{table_id}", response_model=schemas.TableAtelierResponse)
def update_table_atelier(table_id: int, table: schemas.TableAtelierUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une table d'atelier"""
    db_table = crud.update_table_atelier(db, table_id=table_id, table=table)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table d'atelier non trouvée")
    return db_table

@app.delete("/tables-atelier/{table_id}")
def delete_table_atelier(table_id: int, db: Session = Depends(get_db)):
    """Supprimer une table d'atelier"""
    db_table = crud.delete_table_atelier(db, table_id=table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table d'atelier non trouvée")
    return {"message": "Table d'atelier supprimée avec succès"}

# =====================================================
# ROUTES POUR LES LISTES D'INVENTAIRE
# =====================================================

@app.get("/listes-inventaire/", response_model=List[schemas.ListeInventaireResponse])
def read_listes_inventaire(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les listes d'inventaire"""
    listes = crud.get_listes_inventaire(db, skip=skip, limit=limit)
    return listes

@app.post("/listes-inventaire/", response_model=schemas.ListeInventaireResponse)
def create_liste_inventaire(liste: schemas.ListeInventaireCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle liste d'inventaire"""
    # Vérifier si l'ID liste existe déjà
    db_liste = crud.get_liste_inventaire_by_id_liste(db, id_liste=liste.id_liste)
    if db_liste:
        raise HTTPException(status_code=400, detail="Une liste avec cet ID existe déjà")
    
    return crud.create_liste_inventaire(db=db, liste=liste)

@app.get("/listes-inventaire/{liste_id}", response_model=schemas.ListeInventaireResponse)
def read_liste_inventaire(liste_id: int, db: Session = Depends(get_db)):
    """Récupérer une liste d'inventaire par son ID"""
    db_liste = crud.get_liste_inventaire_by_id(db, liste_id=liste_id)
    if db_liste is None:
        raise HTTPException(status_code=404, detail="Liste d'inventaire non trouvée")
    return db_liste

@app.put("/listes-inventaire/{liste_id}", response_model=schemas.ListeInventaireResponse)
def update_liste_inventaire(liste_id: int, liste: schemas.ListeInventaireUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une liste d'inventaire"""
    db_liste = crud.update_liste_inventaire(db, liste_id=liste_id, liste=liste)
    if db_liste is None:
        raise HTTPException(status_code=404, detail="Liste d'inventaire non trouvée")
    return db_liste

@app.delete("/listes-inventaire/{liste_id}")
def delete_liste_inventaire(liste_id: int, db: Session = Depends(get_db)):
    """Supprimer une liste d'inventaire"""
    db_liste = crud.delete_liste_inventaire(db, liste_id=liste_id)
    if db_liste is None:
        raise HTTPException(status_code=404, detail="Liste d'inventaire non trouvée")
    return {"message": "Liste d'inventaire supprimée avec succès"}

@app.get("/listes-inventaire/{id_liste}/produits", response_model=List[schemas.ProduitListeInventaireResponse])
def read_produits_liste_inventaire(id_liste: str, db: Session = Depends(get_db)):
    """Récupérer tous les produits d'une liste d'inventaire"""
    produits = crud.get_produits_liste_inventaire(db, id_liste=id_liste)
    return produits

@app.post("/listes-inventaire/produits/", response_model=schemas.ProduitListeInventaireResponse)
def create_produit_liste_inventaire(produit: schemas.ProduitListeInventaireCreate, db: Session = Depends(get_db)):
    """Ajouter un produit à une liste d'inventaire"""
    return crud.create_produit_liste_inventaire(db=db, produit=produit)

@app.put("/listes-inventaire/produits/{produit_id}", response_model=schemas.ProduitListeInventaireResponse)
def update_produit_liste_inventaire(produit_id: int, produit: schemas.ProduitListeInventaireUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un produit dans une liste d'inventaire"""
    db_produit = crud.update_produit_liste_inventaire(db, produit_id=produit_id, produit=produit)
    if db_produit is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé dans la liste d'inventaire")
    return db_produit

# =====================================================
# ROUTES POUR LES MOUVEMENTS DE STOCK
# =====================================================

@app.post("/mouvements-stock/", response_model=schemas.MouvementStockResponse)
def effectuer_mouvement_stock(mouvement: schemas.MouvementStockCreate, db: Session = Depends(get_db)):
    """Effectuer un mouvement de stock"""
    result = crud.effectuer_mouvement_stock(db=db, mouvement=mouvement)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# =====================================================
# ROUTES UTILITAIRES
# =====================================================

@app.get("/health")
def health_check():
    """Vérification de l'état de l'API"""
    return {"status": "healthy", "message": "API GMAO fonctionnelle"}

@app.get("/")
def read_root():
    """Page d'accueil de l'API"""
    return {
        "message": "API GMAO - Gestion de Stock",
        "version": "2.0.0",
        "description": "API compatible avec l'application Streamlit GMAO",
        "endpoints": {
            "inventaire": "/inventaire/",
            "fournisseurs": "/fournisseurs/",
            "sites": "/sites/",
            "lieux": "/lieux/",
            "emplacements": "/emplacements/",
            "emplacements_hierarchy": "/emplacements-hierarchy/",
            "demandes": "/demandes/",
            "historique": "/historique/",
            "tables_atelier": "/tables-atelier/",
            "listes_inventaire": "/listes-inventaire/",
            "mouvements_stock": "/mouvements-stock/",
            "documentation": "/docs"
        }
    } 