from fastapi import FastAPI, Depends, HTTPException, Query, Request, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
import crud
import models
import schemas
from database import SessionLocal, engine, get_db
import auth
import qrcode
import io
import base64
import json
import os
import time
import logging
import math
import pandas as pd
import traceback
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Configurer le logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Créer les tables
print("🔧 Création des tables de base de données...")
# models.Base.metadata.create_all(bind=engine)
print("✅ Tables créées avec succès!")

# Créer le superuser si les variables d'environnement sont définies
print("👤 Vérification de la création du superuser...")
try:
    from create_superuser import create_superuser
    create_superuser()
except Exception as e:
    logger.error(f"❌ Erreur lors de la création du superuser: {e}")
    print(f"❌ Erreur lors de la création du superuser: {e}")
else:
    print("✅ Processus de création du superuser terminé!")

# Initialiser FastAPI
app = FastAPI(
    title="GMAO - Système de Gestion de Stock",
    description="Système complet de gestion de stock avec interface web intégrée",
    version="3.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour gérer les redirections d'authentification
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException as e:
        if e.status_code == 302 and "Location" in e.headers:
            return RedirectResponse(url=e.headers["Location"], status_code=302)
        raise e

# Configuration des templates et fichiers statiques
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Fonctions helper pour les templates
def get_stock_status(produit):
    """Détermine le statut du stock d'un produit"""
    quantite = produit.get('quantite', 0)
    stock_min = produit.get('stock_min', produit.get('seuil_alerte', 0))
    stock_max = produit.get('stock_max', 100)
    
    # Calcul du seuil d'alerte (30% entre min et max)
    seuil_alerte = stock_min + (stock_max - stock_min) * 0.3
    
    if quantite < stock_min:
        return 'critique'
    elif quantite > stock_max:
        return 'surstock'
    elif quantite <= seuil_alerte:
        return 'faible'
    else:
        return 'normal'

def get_status_class(produit):
    """Retourne la classe CSS pour le statut du stock"""
    status = get_stock_status(produit)
    return f'status-{status}'

def get_stock_status_text(produit):
    """Retourne le texte du statut du stock"""
    status = get_stock_status(produit)
    status_texts = {
        'critique': '🔴 Critique',
        'faible': '🟠 Faible',
        'surstock': '🟡 Surstock',
        'normal': '🟢 Normal'
    }
    return status_texts.get(status, '❓ Inconnu')

def moment():
    """Retourner un objet datetime pour les templates avec méthode format"""
    class MomentJS:
        def __init__(self):
            self.now = datetime.now()
        
        def format(self, pattern):
            """Formater la date selon un pattern similaire à moment.js"""
            # Convertir les patterns moment.js vers strftime
            pattern = pattern.replace('DD', '%d')
            pattern = pattern.replace('MM', '%m') 
            pattern = pattern.replace('YYYY', '%Y')
            pattern = pattern.replace('HH', '%H')
            pattern = pattern.replace('mm', '%M')
            return self.now.strftime(pattern)
    
    return MomentJS()

def get_flashed_messages(with_categories=False):
    """Fonction de remplacement pour Flask's get_flashed_messages"""
    # Pour FastAPI, nous retournons une liste vide car nous n'utilisons pas le système de flash messages
    if with_categories:
        return []  # Liste de tuples (category, message)
    return []  # Liste de messages

def url_for(endpoint, **values):
    """Fonction de remplacement pour Flask's url_for"""
    # Mapping des endpoints vers les URLs
    routes = {
        'index': '/',
        'magasin': '/magasin',
        'scanner': '/scanner',
        'historique_mouvements': '/historique-mouvements',
        'alertes_stock': '/alertes-stock',
        'demande_materiel': '/demande-materiel',
        'gestion_demandes': '/gestion-demandes',
        'entree_stock': '/entree-stock',
        'sortie_stock': '/sortie-stock',
        'regule_stock': '/regule-stock',
        'gestion_produits': '/gestion-produits',
        'gestion_fournisseurs': '/gestion-fournisseurs',
        'gestion_emplacements': '/gestion-emplacements',
        'gestion_tables': '/gestion-tables',
        'gestion_utilisateurs': '/gestion-utilisateurs',
        'gestion_qr_codes': '/gestion-qr-codes',
        'demandes': '/demandes',
        'nouvelle_demande': '/nouvelle-demande',
        'stock_faible': '/stock-faible',
        'preparer_inventaire': '/preparer-inventaire'
    }
    
    # Gestion des routes avec paramètres
    if endpoint == 'produit_detail' and 'reference' in values:
        return f"/produit/{values['reference']}"
    if endpoint == 'fournisseur_detail' and 'nom_fournisseur' in values:
        return f"/fournisseur/{values['nom_fournisseur']}"
    
    # Retourner l'URL de base
    return routes.get(endpoint, f"/{endpoint}")

# Les fonctions helper seront enregistrées après leur définition

# =====================================================
# ROUTES WEB (FRONT-END)
# =====================================================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Page de connexion"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_web(request: Request, db: Session = Depends(get_db)):
    """Traitement du formulaire de connexion web"""
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        
        if not username or not password:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Nom d'utilisateur et mot de passe requis"
            })
        
        # Authentifier l'utilisateur
        user = auth.authenticate_user(db, username, password)
        if not user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Nom d'utilisateur ou mot de passe incorrect"
            })
        
        # Mettre à jour la date de dernière connexion
        auth.update_last_login(db, user)
        
        # Créer le token d'accès
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "role": user.role
            },
            expires_delta=access_token_expires
        )
        
        # Rediriger vers la page d'accueil avec le cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            max_age=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=False,  # Mettre à True en production avec HTTPS
            samesite="lax"
        )
        return response
        
    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Erreur lors de la connexion"
        })

@app.get("/logout", response_class=HTMLResponse)
async def logout_page(request: Request):
    """Déconnexion et redirection vers la page de connexion"""
    response = RedirectResponse(url="/login", status_code=302)
    # Supprimer tous les cookies d'authentification possibles
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("access_token", path="/", domain=None)
    # Ajouter des headers pour empêcher la mise en cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, current_user: models.Utilisateur = Depends(auth.require_authentication_web)):
    """Page d'accueil avec menu principal"""
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "current_user": current_user,
        "permissions": auth.get_user_permissions(current_user)
    })

@app.get("/magasin", response_class=HTMLResponse)
async def magasin(request: Request, page: int = 1, fournisseur: Optional[str] = None, search: Optional[str] = None, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page principale du magasin avec filtrage par fournisseur et pagination"""
    try:
        # Configuration de la pagination
        items_per_page = 100
        skip = (page - 1) * items_per_page
        
        # Récupérer les produits avec filtrage et pagination
        if search and search.strip():
            # Recherche avec filtrage par fournisseur optionnel
            if fournisseur and fournisseur != 'tous':
                # Recherche combinée avec fournisseur - plus efficace
                all_search_results = crud.search_inventaire_enrichi(db, search.strip(), skip=0, limit=10000)
                filtered_results = [p for p in all_search_results if p.get('fournisseur') == fournisseur]
                total_produits = len(filtered_results)
                # Appliquer la pagination manuellement
                produits_raw = filtered_results[skip:skip + items_per_page]
            else:
                # Recherche simple
                produits_raw = crud.search_inventaire_enrichi(db, search.strip(), skip=skip, limit=items_per_page)
                # Compter le total pour la recherche
                all_search_results = crud.search_inventaire_enrichi(db, search.strip(), skip=0, limit=10000)
                total_produits = len(all_search_results)
        elif fournisseur and fournisseur != 'tous':
            # Filtrage par fournisseur uniquement
            produits_raw = crud.get_inventaire_by_fournisseur_enrichi(db, fournisseur, skip=skip, limit=items_per_page)
            total_produits = db.query(models.Inventaire).join(
                models.Fournisseur, models.Inventaire.fournisseur_id == models.Fournisseur.id
            ).filter(models.Fournisseur.nom_fournisseur == fournisseur).count()
        else:
            # Récupérer tous les produits
            produits_raw = crud.get_inventaire_enrichi(db, skip=skip, limit=items_per_page)
            total_produits = db.query(models.Inventaire).count()
        
        # Calculer les informations de pagination
        total_pages = (total_produits + items_per_page - 1) // items_per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        # Normaliser les produits pour les templates
        produits = [normalize_produit(p) for p in produits_raw]
        
        # Récupérer tous les fournisseurs (pas seulement les actifs)
        fournisseurs_raw = crud.get_fournisseurs(db)
        fournisseurs = [clean_sqlalchemy_object(f) for f in fournisseurs_raw]
        
        # Calculer les statistiques directement en base de données (optimisé)
        stats = crud.calculate_stock_stats_db(db, fournisseur)
        
        return templates.TemplateResponse("magasin.html", {
            "request": request,
            "produits": produits,
            "stats": stats,
            "fournisseurs": fournisseurs,
            "fournisseur_filtre": fournisseur,
            "search_query": search,
            "current_user": current_user,
            # Informations de pagination
            "page": page,
            "total_pages": total_pages,
            "total_produits": total_produits,
            "items_per_page": items_per_page,
            "has_prev": has_prev,
            "has_next": has_next,
            "start_item": skip + 1,
            "end_item": min(skip + items_per_page, total_produits)
        })
    except Exception as e:
        print(f"Erreur dans magasin: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/historique-mouvements", response_class=HTMLResponse)
async def historique_mouvements(request: Request, fournisseur: Optional[str] = None, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page Historique des mouvements"""
    try:
        historique_raw = crud.get_historique(db)
        fournisseurs_raw = crud.get_fournisseurs(db)  # Récupérer TOUS les fournisseurs
        produits_raw = crud.get_inventaire_enrichi(db, skip=0, limit=10000)  # Récupérer tous les produits
        
        # Traiter les données pour l'affichage
        historique = []
        reference_to_fournisseur = {}
        
        # Créer un dictionnaire de référence → fournisseur
        for produit in produits_raw:
            reference = produit.get('reference')
            fournisseur_prod = produit.get('fournisseur')
            if reference and fournisseur_prod:
                reference_to_fournisseur[reference] = fournisseur_prod
        
        for mouvement in historique_raw:
            mouvement_dict = mouvement.__dict__.copy()
            
            # Ajouter le fournisseur basé sur la référence
            reference = mouvement_dict.get('reference')
            if reference and reference in reference_to_fournisseur:
                mouvement_dict['fournisseur'] = reference_to_fournisseur[reference]
            else:
                mouvement_dict['fournisseur'] = 'Non défini'
            
            # Normaliser les champs pour l'affichage
            process_mouvement_for_display(mouvement_dict)
            historique.append(mouvement_dict)
        
        fournisseurs = [clean_sqlalchemy_object(f) for f in fournisseurs_raw]
        
        # Filtrer par fournisseur si spécifié
        if fournisseur and fournisseur != 'tous':
            historique = [h for h in historique if h.get('fournisseur') == fournisseur]
        
        return templates.TemplateResponse("historique_mouvements.html", {
            "request": request,
            "historique": historique,
            "fournisseurs": fournisseurs,
            "fournisseur_filtre": fournisseur,
            "current_user": current_user
        })
    except Exception as e:
        print(f"Erreur dans historique_mouvements: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/alertes-stock", response_class=HTMLResponse)
async def alertes_stock(request: Request, page: int = 1, fournisseur: Optional[str] = None, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page Alertes de stock"""
    try:
        items_per_page = 100
        
        # Récupérer tous les produits d'abord pour calculer les alertes
        produits_raw = crud.get_inventaire_enrichi(db, skip=0, limit=10000)
        fournisseurs_raw = crud.get_fournisseurs(db)
        
        # Calculer les alertes
        produits_avec_alertes = []
        
        for produit_dict in produits_raw:
            quantite = produit_dict.get('quantite', 0)
            stock_min = produit_dict.get('stock_min', 0)
            stock_max = produit_dict.get('stock_max', 100)
            
            # Calcul du seuil d'alerte (30% entre min et max)
            if stock_max > stock_min:
                seuil_alerte = stock_min + (stock_max - stock_min) * 0.3
            else:
                seuil_alerte = stock_min
            
            # Déterminer le statut
            statut = None
            if quantite < stock_min:
                statut = 'critique'
            elif quantite > stock_max:
                statut = 'surstock'
            elif quantite <= seuil_alerte:
                statut = 'faible'
            
            # Ajouter seulement les produits avec des alertes
            if statut:
                produit_dict['statut'] = statut
                produit_dict['seuil_alerte'] = int(seuil_alerte)
                normalize_produit(produit_dict)
                produits_avec_alertes.append(produit_dict)
        
        # Filtrer par fournisseur si spécifié (côté serveur)
        if fournisseur and fournisseur != 'tous':
            produits_avec_alertes = [p for p in produits_avec_alertes if p.get('fournisseur') == fournisseur]
        
        # Calcul des totaux globaux par statut (avant pagination)
        total_critique = sum(1 for p in produits_avec_alertes if p.get('statut') == 'critique')
        total_faible = sum(1 for p in produits_avec_alertes if p.get('statut') == 'faible')
        total_surstock = sum(1 for p in produits_avec_alertes if p.get('statut') == 'surstock')
        
        # Trier par priorité (critique > faible > surstock)
        priority_order = {'critique': 1, 'faible': 2, 'surstock': 3}
        produits_avec_alertes.sort(key=lambda x: priority_order.get(x.get('statut'), 4))
        
        # Calculer la pagination
        total_products = len(produits_avec_alertes)
        total_pages = (total_products + items_per_page - 1) // items_per_page
        
        # Paginer les résultats
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        produits_pagines = produits_avec_alertes[start_index:end_index]
        
        fournisseurs = [clean_sqlalchemy_object(f) for f in fournisseurs_raw]
        
        return templates.TemplateResponse("alertes_stock.html", {
            "request": request,
            "produits": produits_pagines,
            "fournisseurs": fournisseurs,
            "fournisseur_filtre": fournisseur,
            "current_user": current_user,
            "current_page": page,
            "total_pages": total_pages,
            "total_products": total_products,
            "items_per_page": items_per_page,
            "start_index": start_index + 1,
            "end_index": min(end_index, total_products),
            "total_critique": total_critique,
            "total_faible": total_faible,
            "total_surstock": total_surstock
        })
    except Exception as e:
        print(f"Erreur dans alertes_stock: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/demande-materiel", response_class=HTMLResponse)
async def demande_materiel(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_authentication_web)):
    """Page Demande de matériel"""
    try:
        tables = crud.get_tables_atelier(db)
        produits_raw = crud.get_inventaire_enrichi(db, skip=0, limit=10000)  # Récupérer tous les produits
        produits = [normalize_produit(p) for p in produits_raw]
        
        return templates.TemplateResponse("demande_materiel.html", {
            "request": request,
            "tables": [clean_sqlalchemy_object(t) for t in tables],
            "produits": produits,
            "current_user": current_user
        })
    except Exception as e:
        print(f"Erreur dans demande_materiel: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/gestion-demandes", response_class=HTMLResponse)
async def gestion_demandes(request: Request, statut: Optional[str] = None, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_authentication_web)):
    """Page Gestion des demandes"""
    # Récupérer les demandes selon le rôle de l'utilisateur
    if current_user.role == 'utilisateur':
        # Les utilisateurs normaux ne voient que leurs propres demandes
        demandes = crud.get_demandes_by_demandeur(db, current_user.username)
    else:
        # Les managers et admins voient toutes les demandes
        demandes = crud.get_demandes(db)
    
    # Mise à jour des demandes existantes sans id_demande_base
    for demande in demandes:
        if not hasattr(demande, 'id_demande_base') or not demande.id_demande_base:
            # Pour les demandes existantes, utiliser l'id_demande comme id_demande_base
            demande.id_demande_base = demande.id_demande
            db.add(demande)
    db.commit()
    
    # Grouper les demandes par panier (ID de base)
    demandes_groupees = {}
    for demande in demandes:
        # Utiliser le vrai id_demande_base de la base de données
        id_base = demande.id_demande_base if hasattr(demande, 'id_demande_base') and demande.id_demande_base else demande.id_demande
        

        
        if id_base not in demandes_groupees:
            demandes_groupees[id_base] = {
                'id_demande': id_base,
                'id_demande_base': id_base,  # Ajouter explicitement l'id_demande_base
                'demandeur': demande.demandeur,
                'table_atelier': demande.table_atelier,
                'id_table': demande.id_table,
                'date_demande': demande.date_demande,
                'statut': demande.statut,
                'commentaires': demande.commentaires,
                'produits': [],
                'date_creation': demande.created_at,
                'urgence': 'Normal'  # Calculé plus tard
            }
        
        # Récupérer les informations de stock pour le produit
        produit_stock = crud.get_inventaire_by_reference(db, reference=demande.reference_produit)
        stock_info = {
            'quantite_stock': 0,
            'stock_min': 0,
            'stock_max': 100,
            'statut_stock': 'critique'
        }
        
        if produit_stock:
            stock_info = {
                'quantite_stock': produit_stock.quantite or 0,
                'stock_min': produit_stock.stock_min or 0,
                'stock_max': produit_stock.stock_max or 100,
                'statut_stock': get_stock_status({'quantite': produit_stock.quantite, 'stock_min': produit_stock.stock_min, 'stock_max': produit_stock.stock_max})
            }
        
        # Calculer l'état du stock après validation
        stock_apres = stock_info['quantite_stock'] - demande.quantite_demandee
        statut_apres = 'critique'
        
        if produit_stock:
            # Simuler le nouveau statut après la demande
            produit_simule = {
                'quantite': max(0, stock_apres),
                'stock_min': stock_info['stock_min'],
                'stock_max': stock_info['stock_max']
            }
            statut_apres = get_stock_status(produit_simule)
        
        stock_info_apres = {
            'quantite_stock': max(0, stock_apres),
            'stock_min': stock_info['stock_min'],
            'stock_max': stock_info['stock_max'],
            'statut_stock': statut_apres
        }

        # Ajouter le produit à la liste avec informations de stock
        demandes_groupees[id_base]['produits'].append({
            'reference': demande.reference_produit,
            'designation': demande.designation_produit,
            'quantite': demande.quantite_demandee,
            'unite': demande.unite,
            'emplacement': demande.emplacement,
            'fournisseur': demande.fournisseur,
            'stock_info': stock_info,
            'stock_info_apres': stock_info_apres
        })

    # Ajouter l'état de préparation pour chaque demande groupée
    for id_base, demande_group in demandes_groupees.items():
        preparation = db.query(models.PreparationDemande).filter(
            models.PreparationDemande.id_demande_base == id_base
        ).first()
        
        if preparation:
            demande_group['statut_preparation'] = preparation.statut_preparation
            demande_group['nb_produits_scannes'] = preparation.nb_produits_scannes
            demande_group['nb_produits_total'] = preparation.nb_produits_total
        else:
            demande_group['statut_preparation'] = 'Non commencée'
            demande_group['nb_produits_scannes'] = 0
            demande_group['nb_produits_total'] = len(demande_group['produits'])
    
    # Convertir en liste et trier par date
    demandes_toutes = list(demandes_groupees.values())
    demandes_toutes.sort(key=lambda x: x['date_creation'], reverse=True)
    
    # Calculer les statistiques sur TOUTES les demandes (pas filtrées)
    stats = {
        'en_attente': sum(1 for d in demandes_toutes if d['statut'] == 'En attente'),
        'approuvee': sum(1 for d in demandes_toutes if d['statut'] == 'Approuvée'),
        'en_cours': sum(1 for d in demandes_toutes if d['statut'] == 'En cours'),
        'rejetee': sum(1 for d in demandes_toutes if d['statut'] == 'Rejetée'),
        'terminee': sum(1 for d in demandes_toutes if d['statut'] == 'Terminée')
    }
    
    # Appliquer le filtre par statut APRÈS le calcul des statistiques
    if statut and statut != 'tous':
        demandes_finales = [d for d in demandes_toutes if d['statut'] == statut]
    else:
        demandes_finales = demandes_toutes
    
    # Générer les alertes
    alertes = []
    
    # Alertes de stock - UNIQUEMENT pour les demandes EN ATTENTE
    produits_critiques = []
    produits_faibles = []
    produits_insuffisants = []
    
    # Filtrer uniquement les demandes en attente pour les alertes de stock
    demandes_en_attente = [d for d in demandes_toutes if d['statut'] == 'En attente']
    
    for demande in demandes_en_attente:
        for produit in demande['produits']:
            stock_info = produit['stock_info']
            if stock_info['statut_stock'] == 'critique':
                produits_critiques.append({
                    'reference': produit['reference'],
                    'designation': produit['designation'],
                    'quantite_stock': stock_info['quantite_stock'],
                    'quantite_demandee': produit['quantite'],
                    'demande_id': demande['id_demande']
                })
            elif stock_info['statut_stock'] == 'faible':
                produits_faibles.append({
                    'reference': produit['reference'],
                    'designation': produit['designation'],
                    'quantite_stock': stock_info['quantite_stock'],
                    'quantite_demandee': produit['quantite'],
                    'demande_id': demande['id_demande']
                })
            
            # Vérifier si le stock est insuffisant pour la demande
            if stock_info['quantite_stock'] < produit['quantite']:
                produits_insuffisants.append({
                    'reference': produit['reference'],
                    'designation': produit['designation'],
                    'quantite_stock': stock_info['quantite_stock'],
                    'quantite_demandee': produit['quantite'],
                    'demande_id': demande['id_demande']
                })
    
    # Créer les alertes
    if produits_critiques:
        alertes.append({
            'type': 'danger',
            'icon': 'bi-exclamation-triangle-fill',
            'titre': 'Stock critique',
            'message': f'{len(produits_critiques)} produit(s) en stock critique dans les demandes en attente',
            'details': produits_critiques
        })
    
    if produits_insuffisants:
        alertes.append({
            'type': 'warning',
            'icon': 'bi-exclamation-circle-fill',
            'titre': 'Stock insuffisant',
            'message': f'{len(produits_insuffisants)} produit(s) avec stock insuffisant pour les demandes en attente',
            'details': produits_insuffisants
        })
    
    if produits_faibles:
        alertes.append({
            'type': 'info',
            'icon': 'bi-info-circle-fill',
            'titre': 'Stock faible',
            'message': f'{len(produits_faibles)} produit(s) en stock faible dans les demandes en attente',
            'details': produits_faibles
        })
    
    # Alertes de changement d'état (demandes récentes EN ATTENTE uniquement)
    from datetime import datetime, timedelta
    demandes_recentes_en_attente = [d for d in demandes_finales if d['date_creation'] and 
                                   (datetime.now() - d['date_creation']).days <= 1 and
                                   d['statut'] == 'En attente']
    
    if demandes_recentes_en_attente:
        alertes.append({
            'type': 'success',
            'icon': 'bi-clock-history',
            'titre': 'Nouvelles demandes',
            'message': f'{len(demandes_recentes_en_attente)} nouvelle(s) demande(s) en attente dans les dernières 24h',
            'details': [{'demande_id': d['id_demande'], 'demandeur': d['demandeur']} for d in demandes_recentes_en_attente]
        })
    
    return templates.TemplateResponse("gestion_demandes.html", {
        "request": request,
        "demandes": demandes_finales,
        "stats": stats,
        "alertes": alertes,
        "current_user": current_user,
        "statut_filtre": statut or 'tous',
        "is_user_role": current_user.role == 'utilisateur'
    })

@app.post("/api/demandes/")
async def creer_demande_materiel(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_authentication_web)):
    """Créer une nouvelle demande de matériel avec le nouveau format"""
    try:
        data = await request.json()
        
        # Validation des champs requis
        required_fields = ['id_demande', 'demandeur', 'table_atelier', 'id_table', 'reference_produit', 'quantite_demandee']
        for field in required_fields:
            if not data.get(field):
                return JSONResponse({'success': False, 'message': f'Le champ {field} est requis'})
        
        # Vérifier que l'ID de demande est unique
        existing_demande = crud.get_demande_by_id_demande(db, id_demande=data['id_demande'])
        if existing_demande:
            # Générer un nouvel ID unique
            data['id_demande'] = f"DEM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{current_user.id}"
        
        # Vérifier que la table d'atelier existe
        table = crud.get_table_atelier_by_id_table(db, id_table=data['id_table'])
        if not table:
            return JSONResponse({'success': False, 'message': 'Table d\'atelier non trouvée'})
        
        # Vérifier que le produit existe
        produit = crud.get_inventaire_by_reference(db, reference=data['reference_produit'])
        if not produit:
            return JSONResponse({'success': False, 'message': 'Produit non trouvé'})
        
        # Créer l'objet demande
        demande_data = schemas.DemandeCreate(
            id_demande=data['id_demande'],
            id_demande_base=data.get('id_demande_base', data['id_demande']),  # Utiliser id_demande si id_demande_base n'est pas fourni
            demandeur=data['demandeur'],
            table_atelier=data['table_atelier'],
            reference_produit=data['reference_produit'],
            quantite_demandee=int(data['quantite_demandee']),
            statut=data.get('statut', 'En attente'),
            date_demande=datetime.now().date(),
            commentaires=data.get('commentaires'),
            # Champs additionnels pour traçabilité
            unite=data.get('unite'),
            fournisseur=data.get('fournisseur'),
            emplacement=data.get('emplacement'),
            designation_produit=data.get('designation_produit'),
            id_table=data['id_table']
        )
        
        # Créer la demande
        result = crud.create_demande(db=db, demande=demande_data)
        
        if result:
            return JSONResponse({
                'success': True, 
                'message': 'Demande créée avec succès',
                'demande': clean_sqlalchemy_object_for_json(result)
            })
        else:
            return JSONResponse({'success': False, 'message': 'Erreur lors de la création de la demande'})
            
    except ValueError as e:
        return JSONResponse({'success': False, 'message': f'Erreur de validation: {str(e)}'})
    except Exception as e:
        print(f"Erreur dans creer_demande_materiel: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/entree-stock", response_class=HTMLResponse)
async def entree_stock_page(request: Request, current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page Entrée de stock"""
    return templates.TemplateResponse("entree_stock.html", {"request": request, "current_user": current_user})

@app.post("/entree-stock")
async def entree_stock_post(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Traiter l'entrée de stock"""
    data = await request.json()
    
    # Construire le motif avec utilisateur connecté et commentaires
    motif_parts = []
    if current_user:
        motif_parts.append(f"Utilisateur: {current_user.nom_complet} ({current_user.username})")
    if data.get('commentaires'):
        motif_parts.append(f"Commentaires: {data['commentaires']}")
    motif = " | ".join(motif_parts) if motif_parts else None
    
    mouvement_data = schemas.MouvementStockCreate(
        reference_produit=data['reference'],
        nature='Entrée',
        quantite=int(data['quantite']),
        motif=motif
    )
    
    try:
        result = crud.effectuer_mouvement_stock(db=db, mouvement=mouvement_data)
        return JSONResponse({'success': True, 'message': 'Entrée enregistrée avec succès'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)})

@app.get("/sortie-stock", response_class=HTMLResponse)
async def sortie_stock_page(request: Request, current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page Sortie de stock"""
    return templates.TemplateResponse("sortie_stock.html", {"request": request, "current_user": current_user})

@app.post("/sortie-stock")
async def sortie_stock_post(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Traiter la sortie de stock"""
    data = await request.json()
    
    # Construire le motif avec utilisateur connecté et commentaires
    motif_parts = []
    if current_user:
        motif_parts.append(f"Utilisateur: {current_user.nom_complet} ({current_user.username})")
    if data.get('commentaires'):
        motif_parts.append(f"Commentaires: {data['commentaires']}")
    motif = " | ".join(motif_parts) if motif_parts else None
    
    mouvement_data = schemas.MouvementStockCreate(
        reference_produit=data['reference'],
        nature='Sortie',
        quantite=int(data['quantite']),
        motif=motif
    )
    
    try:
        result = crud.effectuer_mouvement_stock(db=db, mouvement=mouvement_data)
        return JSONResponse({'success': True, 'message': 'Sortie enregistrée avec succès'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)})

@app.get("/regule-stock", response_class=HTMLResponse)
async def regule_stock_page(request: Request, current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page Régule - Ajustement d'inventaire"""
    return templates.TemplateResponse("regule_stock.html", {"request": request, "current_user": current_user})

@app.post("/regule-stock")
async def regule_stock_post(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Traiter l'ajustement de stock"""
    data = await request.json()
    
    # Construire le motif avec utilisateur connecté et commentaires
    motif_parts = []
    if current_user:
        motif_parts.append(f"Utilisateur: {current_user.nom_complet} ({current_user.username})")
    if data.get('commentaires'):
        motif_parts.append(f"Commentaires: {data['commentaires']}")
    motif = " | ".join(motif_parts) if motif_parts else None
    
    mouvement_data = schemas.MouvementStockCreate(
        reference_produit=data['reference'],
        nature='Ajustement',
        quantite=int(data['quantite']),
        motif=motif
    )
    
    try:
        result = crud.effectuer_mouvement_stock(db=db, mouvement=mouvement_data)
        return JSONResponse({'success': True, 'message': 'Ajustement enregistré avec succès'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)})

@app.get("/gestion-produits", response_class=HTMLResponse)
async def gestion_produits(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Page de gestion des produits"""
    try:
        # Récupérer les données enrichies
        produits_raw = crud.get_inventaire_enrichi(db, skip=0, limit=10000)  # Récupérer tous les produits
        produits = [normalize_produit(p) for p in produits_raw]
        
        # Récupérer les données pour les formulaires
        sites = crud.get_sites(db)
        lieux = crud.get_lieux(db)  
        emplacements = crud.get_emplacements(db)
        fournisseurs_actifs = crud.get_fournisseurs(db)  # Récupérer TOUS les fournisseurs
        
        # Récupérer tous les fournisseurs pour les statistiques (pas seulement les actifs)
        tous_fournisseurs = crud.get_fournisseurs(db)
        
        # Calculer les statistiques de stock critique
        stock_critique_count = 0
        for produit in produits:
            quantite = produit.get('quantite', 0) or 0
            stock_min = produit.get('stock_min', 0) or 0
            if quantite <= stock_min and stock_min > 0:
                stock_critique_count += 1
        
        return templates.TemplateResponse("gestion_produits.html", {
            "request": request,
            "current_user": current_user,
            "produits": produits,
            "sites": [clean_sqlalchemy_object_for_json(s) for s in sites],
            "lieux": [clean_sqlalchemy_object_for_json(l) for l in lieux],
            "emplacements": [clean_sqlalchemy_object_for_json(e) for e in emplacements],
            "fournisseurs_actifs": [clean_sqlalchemy_object_for_json(f) for f in fournisseurs_actifs],
            "fournisseurs": [clean_sqlalchemy_object_for_json(f) for f in tous_fournisseurs],  # Pour les statistiques
            "stock_critique_count": stock_critique_count  # Pour les statistiques
        })
    except Exception as e:
        print(f"Erreur dans gestion_produits: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/gestion-fournisseurs", response_class=HTMLResponse)
async def gestion_fournisseurs(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Page Gestion des fournisseurs"""
    fournisseurs = crud.get_fournisseurs(db)
    
    return templates.TemplateResponse("gestion_fournisseurs.html", {
        "request": request,
        "current_user": current_user,
        "fournisseurs": [clean_sqlalchemy_object(f) for f in fournisseurs]
    })

@app.get("/gestion-emplacements", response_class=HTMLResponse)
async def gestion_emplacements(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Page Gestion de la hiérarchie Site > Lieu > Emplacement"""
    sites = crud.get_sites(db)
    lieux = crud.get_lieux(db)
    
    # Récupérer tous les emplacements avec leurs informations de lieu
    from sqlalchemy.orm import outerjoin
    emplacements_query = db.query(
        models.Emplacement,
        models.Lieu.nom_lieu,
        models.Site.nom_site
    ).outerjoin(
        models.Lieu, models.Emplacement.lieu_id == models.Lieu.id
    ).outerjoin(
        models.Site, models.Lieu.site_id == models.Site.id
    ).all()
    
    # Transformer les résultats pour inclure les noms des lieux
    emplacements = []
    for emplacement, lieu_nom, site_nom in emplacements_query:
        emplacement_dict = clean_sqlalchemy_object_for_json(emplacement)
        emplacement_dict['lieu_nom'] = lieu_nom or '-'
        emplacement_dict['site_nom'] = site_nom or '-'
        emplacements.append(emplacement_dict)
    
    return templates.TemplateResponse("gestion_emplacements.html", {
        "request": request,
        "current_user": current_user,
        "sites": [clean_sqlalchemy_object_for_json(s) for s in sites],
        "lieux": [clean_sqlalchemy_object_for_json(l) for l in lieux],
        "emplacements": emplacements
    })

@app.get("/gestion-tables", response_class=HTMLResponse)
async def gestion_tables(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Page Gestion des tables d'atelier"""
    tables = crud.get_tables_atelier(db)
    
    return templates.TemplateResponse("gestion_tables.html", {
        "request": request,
        "current_user": current_user,
        "tables": [clean_sqlalchemy_object(t) for t in tables]
    })

@app.get("/gestion-utilisateurs", response_class=HTMLResponse)
async def gestion_utilisateurs(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Page Gestion des utilisateurs - Réservée aux administrateurs"""
    
    try:
        # Récupérer tous les utilisateurs
        utilisateurs_raw = crud.get_utilisateurs(db)
        utilisateurs = [clean_sqlalchemy_object(u) for u in utilisateurs_raw]
        
        # Calculer les statistiques
        stats = {
            'total': len(utilisateurs),
            'actifs': len([u for u in utilisateurs if u.get('statut') == 'actif']),
            'admins': len([u for u in utilisateurs if u.get('role') == 'admin']),
            'managers': len([u for u in utilisateurs if u.get('role') == 'manager'])
        }
        
        return templates.TemplateResponse("gestion_utilisateurs.html", {
            "request": request,
            "utilisateurs": utilisateurs,
            "stats": stats,
            "current_user": current_user,
            "permissions": auth.get_user_permissions(current_user)
        })
    except Exception as e:
        print(f"Erreur dans gestion_utilisateurs: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/gestion-unites", response_class=HTMLResponse)
async def gestion_unites(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Page de gestion des unités de stockage et de commande"""
    try:
        unites_stockage = crud.get_unites_stockage(db)
        unites_commande = crud.get_unites_commande(db)
        
        # Calculer les statistiques
        stats_stockage = {
            'total': len(unites_stockage),
            'actives': len([u for u in unites_stockage if u.statut == 'Actif']),
            'types': len(set([u.type_unite for u in unites_stockage if u.type_unite]))
        }
        
        stats_commande = {
            'total': len(unites_commande),
            'actives': len([u for u in unites_commande if u.statut == 'Actif']),
            'types': len(set([u.type_unite for u in unites_commande if u.type_unite]))
        }
        
        return templates.TemplateResponse("gestion_unites.html", {
            "request": request,
            "unites_stockage": [clean_sqlalchemy_object(u) for u in unites_stockage],
            "unites_commande": [clean_sqlalchemy_object(u) for u in unites_commande],
            "stats_stockage": stats_stockage,
            "stats_commande": stats_commande,
            "current_user": current_user
        })
    except Exception as e:
        print(f"Erreur dans gestion_unites: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/gestion-qr-codes", response_class=HTMLResponse)
async def gestion_qr_codes(request: Request, page: int = 1, fournisseur: Optional[str] = None, all: Optional[int] = 0, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page de gestion des QR codes pour impression avec pagination"""
    try:
        # Configuration de la pagination
        items_per_page = 100
        skip = (page - 1) * items_per_page
        limit = None if all else items_per_page
        
        # Récupérer le nombre total de produits pour la pagination
        if fournisseur and fournisseur != 'tous':
            total_produits = db.query(models.Inventaire).join(
                models.Fournisseur, models.Inventaire.fournisseur_id == models.Fournisseur.id
            ).filter(models.Fournisseur.nom_fournisseur == fournisseur).count()
        else:
            total_produits = db.query(models.Inventaire).count()
        
        total_pages = (total_produits + items_per_page - 1) // items_per_page if not all else 1
        
        # Calculer les informations de pagination
        start_item = skip + 1 if total_produits > 0 else 0
        end_item = min(skip + items_per_page, total_produits)
        
        # Récupérer les produits avec pagination et filtrage par fournisseur
        if fournisseur and fournisseur != 'tous':
            produits_raw = crud.get_inventaire_by_fournisseur_enrichi(db, fournisseur, skip=skip, limit=limit)
        else:
            produits_raw = crud.get_inventaire_enrichi(db, skip=skip, limit=limit)
        
        # Générer les QR codes sans normaliser (pour préserver les objets fournisseur)
        produits = []
        for produit in produits_raw:
            # Générer le QR code pour chaque produit
            reference = produit.get('reference', '')
            qr_code_data = generate_qr_code(reference)
            produit['qr_code'] = qr_code_data
            produits.append(produit)
        
        # Récupérer toutes les tables d'atelier
        tables_atelier_raw = crud.get_tables_atelier(db, skip=0, limit=10000)
        
        # Générer les QR codes pour les tables d'atelier
        tables_atelier = []
        for table in tables_atelier_raw:
            table_clean = clean_sqlalchemy_object(table)
            # Générer le QR code pour chaque table (utiliser l'id_table)
            id_table = table_clean.get('id_table', '')
            qr_code_data = generate_qr_code(id_table)
            table_clean['qr_code'] = qr_code_data
            tables_atelier.append(table_clean)
        
        # Récupérer la liste des fournisseurs pour le filtre
        fournisseurs = crud.get_fournisseurs(db)
        
        # Récupérer la liste des catégories uniques
        categories = list(set([p.get('categorie') for p in produits if p.get('categorie')]))
        categories.sort()
        
        # Récupérer la liste des types d'atelier uniques
        types_atelier = list(set([t.get('type_atelier') for t in tables_atelier if t.get('type_atelier')]))
        types_atelier.sort()
        
        return templates.TemplateResponse("gestion_qr_codes.html", {
            "request": request,
            "produits": produits,
            "tables_atelier": tables_atelier,
            "fournisseurs": [clean_sqlalchemy_object(f) for f in fournisseurs],
            "categories": categories,
            "types_atelier": types_atelier,
            "fournisseur_filtre": fournisseur,
            "current_user": current_user,
            # Informations de pagination
            "page": page,
            "total_pages": total_pages,
            "total_produits": total_produits,
            "start_item": start_item,
            "end_item": end_item,
            "items_per_page": items_per_page,
            "all": all
        })
    except Exception as e:
        print(f"Erreur dans gestion_qr_codes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.post("/gestion-tables")
async def gestion_tables_post(request: Request, db: Session = Depends(get_db)):
    """Traiter la soumission du formulaire de création de table"""
    try:
        form_data = await request.form()
        
        # Générer un id_table numérique unique à 10 chiffres si non fourni
        id_table = form_data.get("id_table")
        if not id_table or not id_table.strip():
            import random
            from sqlalchemy.exc import NoResultFound
            for _ in range(10):  # 10 tentatives max
                id_table_candidate = ''.join([str(random.randint(0, 9)) for _ in range(10)])
                # Vérifier l'unicité
                db_table = crud.get_table_atelier_by_id_table(db, id_table=id_table_candidate)
                if not db_table:
                    id_table = id_table_candidate
                    break
            else:
                raise Exception("Impossible de générer un id_table unique à 10 chiffres")
        
        # Préparer les champs optionnels
        emplacement = form_data.get("emplacement") or None
        responsable = form_data.get("responsable") or None
        
        # Créer l'objet table à partir des données du formulaire
        table_data = schemas.TableAtelierCreate(
            id_table=id_table,
            nom_table=form_data.get("nom_table"),
            type_atelier=form_data.get("type_atelier"),
            emplacement=emplacement,
            responsable=responsable,
            statut=form_data.get("statut", "Actif")
        )
        
        # Vérifier si l'ID table existe déjà
        db_table = crud.get_table_atelier_by_id_table(db, id_table=table_data.id_table)
        if db_table:
            # Rediriger avec un message d'erreur
            tables = crud.get_tables_atelier(db)
            return templates.TemplateResponse("gestion_tables.html", {
                "request": request,
                "tables": [clean_sqlalchemy_object(t) for t in tables],
                "error_message": "Une table avec cet ID existe déjà"
            })
        
        # Créer la table
        crud.create_table_atelier(db=db, table=table_data)
        
        # Rediriger vers la page avec un message de succès
        tables = crud.get_tables_atelier(db)
        return templates.TemplateResponse("gestion_tables.html", {
            "request": request,
            "tables": [clean_sqlalchemy_object(t) for t in tables],
            "success_message": "Table créée avec succès"
        })
        
    except ValueError as e:
        # Erreur de validation Pydantic
        tables = crud.get_tables_atelier(db)
        return templates.TemplateResponse("gestion_tables.html", {
            "request": request,
            "tables": [clean_sqlalchemy_object(t) for t in tables],
            "error_message": f"Erreur de validation : {str(e)}"
        })
    except Exception as e:
        # Autres erreurs
        tables = crud.get_tables_atelier(db)
        return templates.TemplateResponse("gestion_tables.html", {
            "request": request,
            "tables": [clean_sqlalchemy_object(t) for t in tables],
            "error_message": f"Erreur lors de la création : {str(e)}"
        })

@app.get("/scanner", response_class=HTMLResponse)
async def scanner(request: Request, current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page de scanner QR code"""
    return templates.TemplateResponse("scanner.html", {"request": request, "current_user": current_user})

@app.get("/mouvement-stock", response_class=HTMLResponse)
async def mouvement_stock_page(request: Request, current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page de mouvement de stock générique"""
    return templates.TemplateResponse("mouvement_stock.html", {"request": request, "current_user": current_user})

@app.get("/produit/{reference}", response_class=HTMLResponse)
async def produit_detail(request: Request, reference: str, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page de détail d'un produit"""
    try:
        produit = crud.get_inventaire_by_reference_enrichi(db, reference=reference)
        if produit is None:
            return templates.TemplateResponse("404.html", {"request": request, "current_user": current_user}, status_code=404)
        
        # Générer le QR code
        qr_code_data = generate_qr_code(reference)
        
        return templates.TemplateResponse("produit_detail.html", {
            "request": request,
            "current_user": current_user,
            "produit": normalize_produit(produit),
            "qr_code": qr_code_data
        })
    except Exception as e:
        print(f"Erreur dans produit_detail: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("500.html", {"request": request, "current_user": current_user}, status_code=500)

@app.get("/fournisseur/{nom_fournisseur}", response_class=HTMLResponse)
async def fournisseur_detail(request: Request, nom_fournisseur: str, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page de détail d'un fournisseur"""
    try:
        # Récupérer le fournisseur par son nom
        fournisseur = crud.get_fournisseur_by_nom(db, nom_fournisseur=nom_fournisseur)
        if fournisseur is None:
            return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
        
        # Récupérer tous les produits de ce fournisseur
        produits_raw = crud.get_inventaire_by_fournisseur_enrichi(db, fournisseur=nom_fournisseur)
        produits = [normalize_produit(p) for p in produits_raw]
        
        # Calculer les statistiques
        stats = {
            'nb_produits': len(produits),
            'valeur_stock_total': sum((p.get('quantite', 0) or 0) * (p.get('prix_unitaire', 0) or 0) for p in produits),
            'nb_produits_stock_faible': 0
        }
        
        # Compter les produits en stock faible
        for produit in produits:
            quantite = produit.get('quantite', 0) or 0
            stock_min = produit.get('stock_min', 0) or 0
            if quantite <= stock_min and stock_min > 0:
                stats['nb_produits_stock_faible'] += 1
        
        return templates.TemplateResponse("fournisseur_detail.html", {
            "request": request,
            "fournisseur": clean_sqlalchemy_object(fournisseur),
            "produits": produits,
            "stats": stats,
            "current_user": current_user
        })
    except Exception as e:
        print(f"Erreur dans fournisseur_detail: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("500.html", {"request": request}, status_code=500)



# Routes de redirection pour compatibilité
@app.get("/inventaire")
async def inventaire_redirect():
    return RedirectResponse(url="/magasin")

@app.get("/demandes")
async def demandes_redirect():
    return RedirectResponse(url="/gestion-demandes")

@app.get("/nouvelle-demande")
async def nouvelle_demande_redirect():
    return RedirectResponse(url="/demande-materiel")

@app.get("/stock-faible")
async def stock_faible_redirect():
    return RedirectResponse(url="/alertes-stock")

# =====================================================
# ROUTES API POUR LE FRONT-END
# =====================================================

@app.get("/api/produit/{reference}")
async def api_produit(reference: str, db: Session = Depends(get_db)):
    """API pour récupérer un produit par référence"""
    try:
        produit = crud.get_inventaire_by_reference_enrichi(db, reference=reference)
        if produit:
            return JSONResponse({'success': True, 'produit': normalize_produit(produit)})
        else:
            return JSONResponse({'success': False, 'message': 'Produit non trouvé'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/table-atelier/{id_table}")
async def api_table_atelier(id_table: str, db: Session = Depends(get_db)):
    """API pour récupérer une table d'atelier par son ID"""
    try:
        table = crud.get_table_atelier_by_id_table(db, id_table=id_table)
        if table:
            return JSONResponse({'success': True, 'table': clean_sqlalchemy_object_for_json(table)})
        else:
            return JSONResponse({'success': False, 'message': 'Table d\'atelier non trouvée'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/historique/reference/{reference}")
async def historique_by_reference(reference: str, db: Session = Depends(get_db)):
    """Récupérer l'historique des mouvements d'un produit par référence"""
    historique_raw = crud.get_historique_by_reference(db, reference=reference)
    
    # Traiter les données pour l'affichage
    historique = []
    for mouvement in historique_raw:
        mouvement_dict = mouvement.__dict__.copy()
        # Normaliser les champs pour l'affichage
        process_mouvement_for_display(mouvement_dict)
        historique.append(mouvement_dict)
    
    return historique

@app.post("/mouvement-stock")
async def mouvement_stock_api(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Effectuer un mouvement de stock depuis la page de détail"""
    data = await request.json()
    
    # Mapper les natures pour l'API
    nature_mapping = {
        'entree': 'Entrée',
        'sortie': 'Sortie', 
        'inventaire': 'Ajustement'
    }
    
    motif = f"Utilisateur: {current_user.nom_complet} ({current_user.username})"
    if data.get('commentaires'):
        motif += f" | {data.get('commentaires')}"
    
    mouvement_data = schemas.MouvementStockCreate(
        reference_produit=data.get('reference'),
        nature=nature_mapping.get(data.get('nature'), data.get('nature')),
        quantite=int(data.get('quantite')),
        motif=motif
    )
    
    try:
        result = crud.effectuer_mouvement_stock(db=db, mouvement=mouvement_data)
        return {'success': True, 'message': 'Mouvement enregistré avec succès'}
    except Exception as e:
        return {'success': False, 'message': str(e)}

# =====================================================
# FONCTIONS HELPER
# =====================================================

def clean_sqlalchemy_object(obj):
    """Nettoie un objet SQLAlchemy pour le rendre JSON serializable"""
    
    if hasattr(obj, '__dict__'):
        # Créer une copie du dictionnaire sans les attributs SQLAlchemy internes
        cleaned = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):  # Ignorer les attributs privés comme _sa_instance_state
                # Pour les templates, garder les objets datetime comme objets datetime
                # Seulement convertir en string pour les réponses JSON
                if isinstance(value, Decimal):
                    cleaned[key] = float(value)
                else:
                    cleaned[key] = value
        return cleaned
    else:
        return obj

def clean_sqlalchemy_object_for_json(obj):
    """Nettoie un objet SQLAlchemy pour les réponses JSON"""
    
    if hasattr(obj, '__dict__'):
        # Créer une copie du dictionnaire sans les attributs SQLAlchemy internes
        cleaned = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):  # Ignorer les attributs privés comme _sa_instance_state
                # Convertir les objets datetime en string ISO pour JSON
                if isinstance(value, datetime):
                    cleaned[key] = value.isoformat()
                elif isinstance(value, date):
                    cleaned[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    cleaned[key] = float(value)
                elif hasattr(value, 'isoformat'):  # Autres types de dates
                    cleaned[key] = value.isoformat()
                else:
                    cleaned[key] = value
        return cleaned
    else:
        return obj

def normalize_produit(produit):
    """Normalise les données d'un produit pour compatibilité entre API et templates"""
    if not produit:
        return produit
    
    # Ajouter des alias pour la compatibilité
    if 'stock_min' in produit and 'seuil_alerte' not in produit:
        produit['seuil_alerte'] = produit['stock_min']
    if 'produits' in produit and 'nom' not in produit:
        # Extraire le nom de base du champ produits
        nom_complet = produit['produits']
        if ' - ' in nom_complet:
            produit['nom'] = nom_complet.split(' - ')[0]
        else:
            produit['nom'] = nom_complet
    
    # Ajouter designation comme alias de produits pour compatibilité
    if 'produits' in produit and 'designation' not in produit:
        produit['designation'] = produit['produits']
    
    # S'assurer que les champs manquants ont des valeurs par défaut, mais ne pas écraser les valeurs existantes
    if not produit.get('fournisseur'):
        produit['fournisseur'] = 'Non défini'
    if not produit.get('emplacement'):
        produit['emplacement'] = 'Non défini'
    if not produit.get('site'):
        produit['site'] = 'Non défini'
    if not produit.get('lieu'):
        produit['lieu'] = 'Non défini'
    
    return produit

# Fonction helper pour formater les dates dans les templates
def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Formater une date/datetime pour l'affichage"""
    if value is None:
        return None
    
    # Si c'est déjà une string, la retourner telle quelle
    if isinstance(value, str):
        try:
            # Essayer de parser la date ISO et la reformater
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime(format)
        except:
            return value
    
    # Si c'est un objet datetime, le formater
    if hasattr(value, 'strftime'):
        return value.strftime(format)
    
    return str(value)

# Enregistrer les fonctions helper pour les templates après leur définition
templates.env.globals.update(
    get_stock_status=get_stock_status,
    get_status_class=get_status_class,
    get_stock_status_text=get_stock_status_text,
    normalize_produit=normalize_produit,
    moment=moment,
    get_flashed_messages=get_flashed_messages,
    url_for=url_for,
    format_datetime=format_datetime
)

def calculate_stock_stats(produits):
    """Calculer les statistiques de stock"""
    stats = {
        'total_produits': len(produits),
        'stock_critique': 0,
        'stock_faible': 0,
        'surstock': 0,
        'stock_normal': 0,
        'valeur_totale': 0
    }
    
    if produits:
        for produit in produits:
            # Conversion sécurisée des valeurs numériques
            try:
                quantite = int(produit.get('quantite', 0))
            except (ValueError, TypeError):
                quantite = 0
                
            try:
                stock_min = int(produit.get('stock_min', 0))
            except (ValueError, TypeError):
                stock_min = 0
                
            try:
                stock_max = int(produit.get('stock_max', 100))
            except (ValueError, TypeError):
                stock_max = 100
                
            try:
                prix = float(produit.get('prix_unitaire', 0))
            except (ValueError, TypeError):
                prix = 0
            
            # Calcul du seuil d'alerte (30% entre min et max)
            if stock_max > stock_min:
                seuil_alerte = stock_min + (stock_max - stock_min) * 0.3
            else:
                seuil_alerte = stock_min
            
            # Classification du stock
            if quantite < stock_min:
                stats['stock_critique'] += 1
            elif quantite > stock_max:
                stats['surstock'] += 1
            elif quantite <= seuil_alerte:
                stats['stock_faible'] += 1
            else:
                stats['stock_normal'] += 1
            
            # Valeur du stock
            stats['valeur_totale'] += quantite * prix
    
    return stats

def process_mouvement_for_display(mouvement):
    """Traiter un mouvement pour l'affichage"""
    # S'assurer que les champs nécessaires existent
    if 'date_mouvement' in mouvement:
        mouvement['date'] = mouvement['date_mouvement']
    elif 'date' not in mouvement:
        mouvement['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Initialiser les champs
    mouvement['utilisateur'] = '👤 Utilisateur historique'
    mouvement['utilisateur_nom'] = 'Utilisateur historique'
    mouvement['utilisateur_username'] = ''
    mouvement['type_operation'] = 'Mouvement manuel'
    mouvement['demande_info'] = ''
    mouvement['demandeur'] = ''
    mouvement['table_atelier'] = ''
    mouvement['id_demande'] = ''
    
    # Vérifier si le champ motif existe (pour compatibilité avec anciennes données)
    if 'motif' in mouvement and mouvement['motif']:
        motif = str(mouvement['motif'])
        import re
        
        # Vérifier s'il s'agit d'une demande matériel
        if 'DEMANDE MATÉRIEL' in motif:
            mouvement['type_operation'] = '📋 Demande matériel'
            
            # Extraire les informations de demande
            id_match = re.search(r'ID:\s*([^|]+)', motif)
            if id_match:
                mouvement['id_demande'] = id_match.group(1).strip()
                mouvement['demande_info'] = f"📋 {mouvement['id_demande']}"
            
            demandeur_match = re.search(r'Demandeur:\s*([^|]+)', motif)
            if demandeur_match:
                mouvement['demandeur'] = demandeur_match.group(1).strip()
            
            table_match = re.search(r'Table:\s*([^|]+)', motif)
            if table_match:
                mouvement['table_atelier'] = table_match.group(1).strip()
            
            livre_par_match = re.search(r'Livré par:\s*([^|]+)', motif)
            if livre_par_match:
                livre_par = livre_par_match.group(1).strip()
                mouvement['utilisateur'] = f"🚚 {livre_par}"
                mouvement['utilisateur_nom'] = livre_par
        else:
            # Pattern 1: "Utilisateur: Nom Complet (username)" - nouveau format
            user_match = re.search(r'Utilisateur:\s*([^(]+?)\s*\(([^)]+)\)', motif)
            if user_match:
                mouvement['utilisateur_nom'] = user_match.group(1).strip()
                mouvement['utilisateur_username'] = user_match.group(2).strip()
                mouvement['utilisateur'] = f"{mouvement['utilisateur_nom']} ({mouvement['utilisateur_username']})"
            else:
                # Pattern 2: "Utilisateur: quelque chose" - ancien format (Mobile User, etc.)
                simple_match = re.search(r'Utilisateur:\s*([^|]+)', motif)
                if simple_match:
                    user_extracted = simple_match.group(1).strip()
                    mouvement['utilisateur'] = user_extracted
                    mouvement['utilisateur_nom'] = user_extracted
                    # Si c'est "Mobile User", on peut l'améliorer
                    if user_extracted.lower() == 'mobile user':
                        mouvement['utilisateur'] = '📱 Mobile User'
                        mouvement['utilisateur_nom'] = 'Mobile User'
                else:
                    # Pattern 3: Chercher dans tout le motif s'il contient des noms d'utilisateur
                    # Si le motif ne contient pas "Utilisateur:" mais contient d'autres infos
                    if motif and motif.strip() and motif.lower() != 'none':
                        # Prendre les premiers mots comme utilisateur potentiel
                        words = motif.split('|')[0].strip()  # Prendre la première partie avant |
                        if len(words) > 0 and len(words) < 50:  # Éviter les motifs trop longs
                            mouvement['utilisateur'] = f"📝 {words}"
                            mouvement['utilisateur_nom'] = words
    
    # Normaliser la nature pour l'affichage
    if 'nature' not in mouvement:
        mouvement['nature'] = 'Mouvement'
        mouvement['nature_normalized'] = 'inventaire'
        mouvement['nature_display'] = 'Mouvement'
    else:
        # Conserver la nature originale et ajouter une version normalisée
        mouvement['nature_originale'] = mouvement['nature']
        nature_lower = mouvement['nature'].lower()
        if 'entrée' in nature_lower or 'entree' in nature_lower:
            mouvement['nature_normalized'] = 'entree'
            mouvement['nature_display'] = 'Entrée'
        elif 'sortie' in nature_lower:
            mouvement['nature_normalized'] = 'sortie'
            mouvement['nature_display'] = 'Sortie'
        elif 'ajustement' in nature_lower or 'régule' in nature_lower or 'regule' in nature_lower:
            mouvement['nature_normalized'] = 'ajustement'
            mouvement['nature_display'] = 'Ajustement'
        else:
            mouvement['nature_normalized'] = 'inventaire'
            mouvement['nature_display'] = mouvement['nature']
        
    if 'quantite_mouvement' not in mouvement:
        mouvement['quantite_mouvement'] = mouvement.get('quantite', 0)
    if 'quantite_avant' not in mouvement:
        mouvement['quantite_avant'] = 0
    if 'quantite_apres' not in mouvement:
        mouvement['quantite_apres'] = mouvement.get('quantite', 0)
    if 'commentaires' not in mouvement:
        mouvement['commentaires'] = ''

def generate_qr_code(data):
    """Générer un QR code et le retourner en base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir en base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

# =====================================================
# ROUTES API EXISTANTES (INCHANGÉES)
# =====================================================

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
    """Rechercher des produits dans l'inventaire"""
    # La fonction search_inventaire ne prend plus les paramètres skip et limit
    inventaire = crud.search_inventaire(db, search_term=search)
    # Appliquer la pagination manuellement
    return inventaire[skip:skip + limit]

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

# =====================================================
# ROUTES POUR GESTION DES DEMANDES - WORKFLOW
# =====================================================

@app.post("/demandes/{id_demande_base}/approuver")
async def approuver_demande(
    id_demande_base: str, 
    db: Session = Depends(get_db), 
    current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)
):
    """Approuver toutes les demandes d'un panier"""
    try:
        demandes = crud.approuver_demande_panier(db, id_demande_base, current_user.username)
        if not demandes:
            raise HTTPException(status_code=404, detail="Demandes non trouvées")
        
        return {
            "success": True,
            "message": f"Panier approuvé avec succès ({len(demandes)} produits)",
            "demandes": [d.id_demande for d in demandes]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'approbation: {str(e)}")

@app.post("/demandes/{id_demande_base}/rejeter")
async def rejeter_demande(
    id_demande_base: str,
    request: Request,
    db: Session = Depends(get_db), 
    current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)
):
    """Rejeter toutes les demandes d'un panier"""
    try:
        # Récupérer le commentaire depuis le body
        body = await request.json()
        commentaire = body.get('commentaire', '')
        
        demandes = crud.rejeter_demande_panier(db, id_demande_base, current_user.username, commentaire)
        if not demandes:
            raise HTTPException(status_code=404, detail="Demandes non trouvées")
        
        return {
            "success": True,
            "message": f"Panier rejeté ({len(demandes)} produits)",
            "demandes": [d.id_demande for d in demandes],
            "commentaire": commentaire
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du rejet: {str(e)}")

@app.get("/preparation-livraison/{id_demande_base}", response_class=HTMLResponse)
async def preparation_livraison_page(
    request: Request,
    id_demande_base: str,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)
):
    """Page de préparation avec scan des produits"""
    try:
        # Récupérer les demandes du panier
        demandes = crud.get_demandes_by_id_base(db, id_demande_base)
        if not demandes:
            raise HTTPException(status_code=404, detail="Demandes non trouvées")
        
        # Vérifier que les demandes sont approuvées ou en cours
        if not all(d.statut in ['Approuvée', 'En cours'] for d in demandes):
            raise HTTPException(status_code=400, detail="Les demandes doivent être approuvées pour être préparées")
        
        # Récupérer ou créer la préparation
        preparation = crud.get_or_create_preparation(db, id_demande_base, current_user.username)
        if not preparation:
            raise HTTPException(status_code=500, detail="Impossible de créer la préparation")
        
        # Récupérer les produits déjà scannés
        produits_scannes = crud.get_produits_scannes(db, preparation.id)
        references_scannees = [p.reference_produit for p in produits_scannes]
        
        # Grouper les informations de la demande
        demande_info = {
            'id_demande_base': id_demande_base,
            'demandeur': demandes[0].demandeur,
            'date_demande': demandes[0].date_demande,
            'statut': demandes[0].statut,
            'statut_preparation': preparation.statut_preparation,
            'nb_produits_scannes': preparation.nb_produits_scannes,
            'nb_produits_total': preparation.nb_produits_total,
            'produits': []
        }
        
        # Ajouter les produits avec leurs informations détaillées
        for demande in demandes:
            # Récupérer les informations du produit depuis l'inventaire
            produit_stock = db.query(models.Inventaire).filter(
                models.Inventaire.reference == demande.reference_produit
            ).first()
            
            emplacement_complet = demande.emplacement or "Non défini"
            if produit_stock:
                # Construire l'emplacement complet avec la hiérarchie
                if produit_stock.site_obj:
                    emplacement_complet = produit_stock.site_obj.nom_site
                    if produit_stock.lieu_obj:
                        emplacement_complet += f" > {produit_stock.lieu_obj.nom_lieu}"
                        if produit_stock.emplacement_obj:
                            emplacement_complet += f" > {produit_stock.emplacement_obj.nom_emplacement}"
            
            demande_info['produits'].append({
                'reference': demande.reference_produit,
                'designation': demande.designation_produit or (produit_stock.produits if produit_stock else "Produit inconnu"),
                'quantite': demande.quantite_demandee,
                'unite': demande.unite or "unité",
                'emplacement': emplacement_complet,
                'fournisseur': demande.fournisseur or (produit_stock.fournisseur_obj.nom_fournisseur if produit_stock and produit_stock.fournisseur_obj else "Non défini"),
                'scanne': demande.reference_produit in references_scannees
            })
        
        return templates.TemplateResponse("preparation_livraison.html", {
            "request": request,
            "demande_info": demande_info,
            "current_user": current_user
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement de la page de préparation: {str(e)}")

@app.post("/demandes/{id_demande_base}/traiter")
async def traiter_demande(
    id_demande_base: str, 
    db: Session = Depends(get_db), 
    current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)
):
    """Mettre en cours de traitement (magasinier prépare le matériel)"""
    try:
        demandes = crud.traiter_demande_panier(db, id_demande_base, current_user.username)
        if not demandes:
            raise HTTPException(status_code=404, detail="Demandes non trouvées ou non approuvées")
        
        return {
            "success": True,
            "message": f"Préparation en cours ({len(demandes)} produits)",
            "demandes": [d.id_demande for d in demandes]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")

@app.post("/api/scan-produit")
async def scanner_produit_api(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)
):
    """API pour scanner un produit lors de la préparation"""
    try:
        data = await request.json()
        id_demande_base = data.get('id_demande_base')
        reference_produit = data.get('reference_produit')
        
        if not id_demande_base or not reference_produit:
            raise HTTPException(status_code=400, detail="Paramètres manquants")
        
        resultat = crud.scanner_produit(db, id_demande_base, reference_produit, current_user.username)
        
        if resultat and 'error' in resultat:
            return {"success": False, "message": resultat['error']}
        
        return {
            "success": True,
            "message": f"Produit {reference_produit} scanné avec succès",
            "produits_scannes": resultat['produits_scannes'],
            "produits_total": resultat['produits_total']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du scan: {str(e)}")

@app.post("/api/valider-preparation")
async def valider_preparation_api(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)
):
    """API pour valider la préparation"""
    try:
        data = await request.json()
        id_demande_base = data.get('id_demande_base')
        
        if not id_demande_base:
            raise HTTPException(status_code=400, detail="ID demande manquant")
        
        resultat = crud.valider_preparation(db, id_demande_base, current_user.username)
        
        if resultat and 'error' in resultat:
            return {"success": False, "message": resultat['error']}
        
        return {
            "success": True,
            "message": "Préparation validée avec succès"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la validation: {str(e)}")

@app.post("/demandes/{id_demande_base}/livrer")
async def livrer_demande(
    id_demande_base: str, 
    db: Session = Depends(get_db), 
    current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)
):
    """Livrer le matériel et retirer du stock - AVEC VALIDATION DE PRÉPARATION"""
    try:
        resultat = crud.livrer_demande_panier(db, id_demande_base, current_user.username)
        
        if resultat and 'error' in resultat:
            return {"success": False, "message": resultat['error']}
        
        return {
            "success": True,
            "message": f"Livraison effectuée ({len(resultat['demandes'])} produits)",
            "demandes": [d.id_demande for d in resultat['demandes']],
            "mouvements_stock": resultat['mouvements']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la livraison: {str(e)}")

@app.post("/api/livrer-depuis-table")
async def livrer_depuis_table_api(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)
):
    """Livrer une demande depuis la page table d'atelier"""
    try:
        form_data = await request.form()
        id_demande_base = form_data.get("id_demande_base")
        
        if not id_demande_base:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "ID demande manquant"}
            )
        
        result = crud.livrer_demande_panier(db, id_demande_base, current_user.username)
        
        if 'error' in result:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": result['error']}
            )
        
        return JSONResponse(content={
            "success": True,
            "message": f"Demande {id_demande_base} livrée avec succès depuis la table d'atelier"
        })
        
    except Exception as e:
        print(f"Erreur lors de la livraison depuis table: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur: {str(e)}"}
        )

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

# =====================================================
# ROUTES D'AUTHENTIFICATION
# =====================================================

@app.post("/auth/login", response_model=schemas.Token)
async def login(utilisateur: schemas.UtilisateurLogin, db: Session = Depends(get_db)):
    """Authentification d'un utilisateur et génération du token JWT"""
    user = auth.authenticate_user(db, utilisateur.username, utilisateur.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mettre à jour la date de dernière connexion
    auth.update_last_login(db, user)
    
    # Créer le token d'accès
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # en secondes
        "user": schemas.UtilisateurResponse.model_validate(user)
    }

@app.post("/auth/register", response_model=schemas.UtilisateurResponse)
async def register(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    """Création d'un nouvel utilisateur"""
    try:
        db_user = crud.create_utilisateur(db, utilisateur)
        return schemas.UtilisateurResponse.model_validate(db_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/me", response_model=schemas.UtilisateurResponse)
async def get_current_user_info(current_user: models.Utilisateur = Depends(auth.get_current_active_user)):
    """Récupérer les informations de l'utilisateur connecté"""
    return schemas.UtilisateurResponse.model_validate(current_user)

@app.put("/auth/me", response_model=schemas.UtilisateurResponse)
async def update_current_user(
    utilisateur: schemas.UtilisateurUpdate,
    current_user: models.Utilisateur = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mettre à jour les informations de l'utilisateur connecté"""
    try:
        db_user = crud.update_utilisateur(db, current_user.id, utilisateur)
        return schemas.UtilisateurResponse.model_validate(db_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: models.Utilisateur = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Changer le mot de passe de l'utilisateur connecté"""
    try:
        crud.change_password(db, current_user.id, old_password, new_password)
        return {"message": "Mot de passe modifié avec succès"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =====================================================
# ROUTES API POUR LA GESTION DES UTILISATEURS
# =====================================================

@app.get("/api/utilisateurs")
async def get_utilisateurs_api(db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Récupérer tous les utilisateurs - Réservé aux administrateurs"""
    try:
        utilisateurs = crud.get_utilisateurs(db)
        return JSONResponse({
            'success': True, 
            'utilisateurs': [clean_sqlalchemy_object_for_json(u) for u in utilisateurs]
        })
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/utilisateurs/{user_id}")
async def get_utilisateur_by_id_api(user_id: int, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Récupérer un utilisateur par son ID - Réservé aux administrateurs"""
    try:
        utilisateur = crud.get_utilisateur_by_id(db, user_id=user_id)
        if utilisateur:
            return JSONResponse({
                'success': True, 
                'utilisateur': clean_sqlalchemy_object_for_json(utilisateur)
            })
        else:
            return JSONResponse({'success': False, 'message': 'Utilisateur non trouvé'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.post("/api/utilisateurs")
async def creer_utilisateur_api(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Créer un nouvel utilisateur - Réservé aux administrateurs"""
    
    try:
        data = await request.json()
        
        # Validation des champs requis
        required_fields = ['username', 'email', 'nom_complet', 'password', 'role', 'statut']
        for field in required_fields:
            if not data.get(field):
                return JSONResponse({'success': False, 'message': f'Le champ {field} est requis'})
        
        # Validation du mot de passe
        if len(data.get('password', '')) < 6:
            return JSONResponse({'success': False, 'message': 'Le mot de passe doit contenir au moins 6 caractères'})
        
        # Créer l'utilisateur
        utilisateur_data = schemas.UtilisateurCreate(
            username=data['username'],
            email=data['email'],
            nom_complet=data['nom_complet'],
            telephone=data.get('telephone'),
            password=data['password'],
            role=data['role'],
            statut=data['statut']
        )
        
        result = crud.create_utilisateur(db=db, utilisateur=utilisateur_data)
        
        if result:
            return JSONResponse({
                'success': True, 
                'message': 'Utilisateur créé avec succès',
                'utilisateur': clean_sqlalchemy_object_for_json(result)
            })
        else:
            return JSONResponse({'success': False, 'message': 'Erreur lors de la création de l\'utilisateur'})
            
    except ValueError as e:
        return JSONResponse({'success': False, 'message': str(e)})
    except Exception as e:
        print(f"Erreur dans creer_utilisateur_api: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.put("/api/utilisateurs/{user_id}")
async def modifier_utilisateur_api(user_id: int, request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Modifier un utilisateur - Réservé aux administrateurs"""
    
    try:
        data = await request.json()
        
        # Validation des champs requis (sauf password qui est optionnel en modification)
        required_fields = ['username', 'email', 'nom_complet', 'role', 'statut']
        for field in required_fields:
            if not data.get(field):
                return JSONResponse({'success': False, 'message': f'Le champ {field} est requis'})
        
        # Préparer les données de mise à jour
        update_data = {
            'email': data['email'],
            'nom_complet': data['nom_complet'],
            'telephone': data.get('telephone'),
            'role': data['role'],
            'statut': data['statut']
        }
        
        # Si un nouveau mot de passe est fourni, le valider et l'inclure
        if data.get('password'):
            if len(data['password']) < 6:
                return JSONResponse({'success': False, 'message': 'Le mot de passe doit contenir au moins 6 caractères'})
            
            # Pour la modification avec mot de passe, on doit utiliser une approche spéciale
            from auth import get_password_hash
            utilisateur = crud.get_utilisateur_by_id(db, user_id=user_id)
            if not utilisateur:
                return JSONResponse({'success': False, 'message': 'Utilisateur non trouvé'})
            
            # Vérifier si le nouvel email existe déjà (sauf pour l'utilisateur actuel)
            if data['email'] != utilisateur.email:
                existing_user = crud.get_utilisateur_by_email(db, data['email'])
                if existing_user and existing_user.id != user_id:
                    return JSONResponse({'success': False, 'message': 'Email déjà utilisé'})
            
            # Mettre à jour tous les champs y compris le mot de passe
            for field, value in update_data.items():
                setattr(utilisateur, field, value)
            
            utilisateur.hashed_password = get_password_hash(data['password'])
            db.commit()
            db.refresh(utilisateur)
            result = utilisateur
        else:
            # Mise à jour sans mot de passe
            utilisateur_update = schemas.UtilisateurUpdate(**update_data)
            result = crud.update_utilisateur(db=db, user_id=user_id, utilisateur=utilisateur_update)
        
        if result:
            return JSONResponse({
                'success': True, 
                'message': 'Utilisateur modifié avec succès',
                'utilisateur': clean_sqlalchemy_object_for_json(result)
            })
        else:
            return JSONResponse({'success': False, 'message': 'Utilisateur non trouvé'})
            
    except ValueError as e:
        return JSONResponse({'success': False, 'message': str(e)})
    except Exception as e:
        print(f"Erreur dans modifier_utilisateur_api: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.delete("/api/utilisateurs/{user_id}")
async def supprimer_utilisateur_api(user_id: int, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Supprimer un utilisateur - Réservé aux administrateurs"""
    
    # Empêcher l'auto-suppression
    if user_id == current_user.id:
        return JSONResponse({'success': False, 'message': 'Vous ne pouvez pas supprimer votre propre compte'})
    
    try:
        result = crud.delete_utilisateur(db=db, user_id=user_id)
        
        if result:
            return JSONResponse({
                'success': True, 
                'message': 'Utilisateur supprimé avec succès'
            })
        else:
            return JSONResponse({'success': False, 'message': 'Utilisateur non trouvé'})
            
    except Exception as e:
        print(f"Erreur dans supprimer_utilisateur_api: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/utilisateurs-stats")
async def get_utilisateurs_stats_api(db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Récupérer les statistiques des utilisateurs - Réservé aux administrateurs"""
    try:
        utilisateurs = crud.get_utilisateurs(db)
        
        stats = {
            'total_utilisateurs': len(utilisateurs),
            'utilisateurs_actifs': len([u for u in utilisateurs if u.statut == 'actif']),
            'utilisateurs_inactifs': len([u for u in utilisateurs if u.statut == 'inactif']),
            'utilisateurs_bloques': len([u for u in utilisateurs if u.statut == 'bloque']),
            'administrateurs': len([u for u in utilisateurs if u.role == 'admin']),
            'managers': len([u for u in utilisateurs if u.role == 'manager']),
            'utilisateurs_simples': len([u for u in utilisateurs if u.role == 'utilisateur'])
        }
        
        return JSONResponse({'success': True, 'stats': stats})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

# =====================================================
# FONCTION HELPER POUR VÉRIFIER LES RÔLES
# =====================================================

def require_admin_role(current_user: models.Utilisateur = Depends(auth.get_current_active_user)):
    """Middleware pour vérifier que l'utilisateur est administrateur"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Droits administrateur requis")
    return current_user

def require_manager_or_admin_role(current_user: models.Utilisateur = Depends(auth.get_current_active_user)):
    """Middleware pour vérifier que l'utilisateur est manager ou administrateur"""
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Accès refusé - Droits manager ou administrateur requis")
    return current_user

# =====================================================
# ROUTES API SUPPLÉMENTAIRES POUR LE FRONT-END
# =====================================================

@app.post("/api/import-produits")
async def import_produits(file: UploadFile = File(...), gestion_doublons: str = Form("ignorer"), db: Session = Depends(get_db)):
    """Importer des produits depuis un fichier Excel"""
    try:
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return JSONResponse({'success': False, 'message': 'Format de fichier non supporté. Utilisez Excel (.xlsx ou .xls)'})
        
        # Lire le fichier Excel
        import pandas as pd
        import io
        import random
        import string
        import time
        
        # Lire le fichier Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Vérifier les colonnes requises
        colonnes_requises = ['Désignation']
        colonnes_manquantes = [col for col in colonnes_requises if col not in df.columns]
        if colonnes_manquantes:
            return JSONResponse({
                'success': False, 
                'message': f'Colonnes manquantes: {", ".join(colonnes_manquantes)}'
            })
        
        # Statistiques d'importation
        stats = {
            'total_lignes': len(df),
            'produits_crees': 0,
            'produits_ignores': 0,
            'produits_mis_a_jour': 0,
            'fournisseurs_crees': 0,
            'sites_crees': 0,
            'lieux_crees': 0,
            'emplacements_crees': 0,
            'unites_stockage_creees': 0,
            'unites_commande_creees': 0,
            'erreurs': []
        }
        
        # Caches pour éviter les doublons et optimiser les performances
        fournisseurs_cache = {}
        sites_cache = {}
        lieux_cache = {}
        emplacements_cache = {}
        unites_stockage_cache = {}
        unites_commande_cache = {}
        
        # Traiter chaque ligne
        for index, row in df.iterrows():
            try:
                ligne_num = index + 2  # +2 car index commence à 0 et ligne 1 = en-têtes
                
                # Petite pause pour éviter les conflits de timestamp
                time.sleep(0.001)  # 1ms de pause
                
                # Extraire les données de base
                designation = str(row.get('Désignation', '')).strip()
                if not designation or designation == 'nan':
                    stats['erreurs'].append(f"Ligne {ligne_num}: Désignation manquante")
                    continue
                
                # Vérifier les doublons selon la stratégie choisie
                produit_existant = None
                mode_mise_a_jour = False
                produit_id = None
                
                # Extraire la référence fournisseur pour la détection de doublons
                reference_fournisseur = str(row.get('Référence fournisseur', '')).strip() if pd.notna(row.get('Référence fournisseur')) else None
                if reference_fournisseur and reference_fournisseur == 'nan':
                    reference_fournisseur = None
                
                fournisseur_nom = str(row.get('Fournisseur Standard', '')).strip() if pd.notna(row.get('Fournisseur Standard')) else None
                if fournisseur_nom and fournisseur_nom == 'nan':
                    fournisseur_nom = None
                
                # Recherche de doublons par référence fournisseur UNIQUEMENT (critère principal)
                if reference_fournisseur:
                    # Récupérer tous les produits avec leurs relations chargées

                    produits_existants = db.query(models.Inventaire).options(
                        joinedload(models.Inventaire.fournisseur_obj)
                    ).all()
                    for produit in produits_existants:
                        produit_ref_fournisseur = produit.reference_fournisseur
                        if (produit_ref_fournisseur and 
                            produit_ref_fournisseur.lower().strip() == reference_fournisseur.lower().strip()):
                            # Doublon détecté basé uniquement sur la référence fournisseur
                            produit_existant = produit
                            break
                
                # Gestion des doublons selon la stratégie
                if produit_existant:
                    if gestion_doublons == "ignorer":
                        stats['produits_ignores'] += 1
                        continue
                    elif gestion_doublons == "mettre_a_jour":
                        # Mode mise à jour du produit existant
                        mode_mise_a_jour = True
                        produit_id = produit_existant.id
                    # Pour "creer_nouveau", on continue avec la création normale
                
                # Conversion sécurisée des valeurs numériques pour les données du produit
                try:
                    stock_min_val = 0
                    if pd.notna(row.get('Min')) and str(row.get('Min')).strip():
                        try:
                            stock_min_val = int(float(row.get('Min')))
                        except (ValueError, TypeError):
                            stock_min_val = 0
                    
                    stock_max_val = 100
                    if pd.notna(row.get('Max')) and str(row.get('Max')).strip():
                        try:
                            stock_max_val = int(float(row.get('Max')))
                        except (ValueError, TypeError):
                            stock_max_val = 100
                    
                    prix_val = 0.0
                    if pd.notna(row.get('Prix')) and str(row.get('Prix')).strip():
                        try:
                            prix_val = float(row.get('Prix'))
                        except (ValueError, TypeError):
                            prix_val = 0.0
                    
                    quantite_val = 0
                    if pd.notna(row.get('Quantité')) and str(row.get('Quantité')).strip():
                        try:
                            quantite_val = int(float(row.get('Quantité')))
                        except (ValueError, TypeError):
                            quantite_val = 0
                except Exception as conversion_error:
                    stats['erreurs'].append(f"Ligne {ligne_num}: Erreur conversion données - {str(conversion_error)}")
                    continue
                
                # Extraction des unités avec debug
                unite_stockage_raw = row.get('Unité de stockage', '')
                unite_commande_raw = row.get('Unite Commande', '')  # SANS accent !
                
                unite_stockage_val = str(unite_stockage_raw).strip() if pd.notna(unite_stockage_raw) and str(unite_stockage_raw).strip() != 'nan' else None
                unite_commande_val = str(unite_commande_raw).strip() if pd.notna(unite_commande_raw) and str(unite_commande_raw).strip() != 'nan' else None
                
                # Debug des unités
                print(f"Ligne {ligne_num}: Unité stockage = '{unite_stockage_val}', Unité commande = '{unite_commande_val}'")
                
                # Données du produit (comme dans Flask)
                produit_data = {
                    'designation': designation,
                    'reference_fournisseur': reference_fournisseur,
                    'unite_stockage': unite_stockage_val,
                    'unite_commande': unite_commande_val,
                    'stock_min': stock_min_val,
                    'stock_max': stock_max_val,
                    'prix_unitaire': prix_val,
                    'categorie': str(row.get('Catégorie', '')).strip() if pd.notna(row.get('Catégorie')) else None,
                    'secteur': str(row.get('Secteur', '')).strip() if pd.notna(row.get('Secteur')) else None,
                    'quantite': quantite_val
                }
                

                
                # === TRAITEMENT DES FOURNISSEURS ===
                if fournisseur_nom:
                    if fournisseur_nom not in fournisseurs_cache:
                        # Vérifier si le fournisseur existe
                        fournisseurs_existants = crud.get_fournisseurs(db) or []
                        fournisseur_existe = any(f.nom_fournisseur == fournisseur_nom for f in fournisseurs_existants)
                        
                        if not fournisseur_existe:
                            # Créer le fournisseur
                            id_fournisseur = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}{index}"
                            
                            fournisseur_data = schemas.FournisseurCreate(
                                id_fournisseur=id_fournisseur,
                                nom_fournisseur=fournisseur_nom,
                                adresse='',
                                contact1_nom='',
                                contact1_prenom='',
                                contact1_fonction='',
                                contact1_tel_fixe='',
                                contact1_tel_mobile='',
                                contact1_email='',
                                contact2_nom='',
                                contact2_prenom='',
                                contact2_fonction='',
                                contact2_tel_fixe='',
                                contact2_tel_mobile='',
                                contact2_email='',
                                statut='Actif'
                            )
                            
                            try:
                                result = crud.create_fournisseur(db=db, fournisseur=fournisseur_data)
                                if result:
                                    stats['fournisseurs_crees'] += 1
                                    fournisseurs_cache[fournisseur_nom] = True
                                else:
                                    stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création fournisseur {fournisseur_nom}")
                            except Exception as e:
                                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création fournisseur {fournisseur_nom} - {str(e)}")
                        else:
                            fournisseurs_cache[fournisseur_nom] = True
                
                # === TRAITEMENT DES UNITÉS DE STOCKAGE ===
                unite_stockage_nom = produit_data.get('unite_stockage')
                if unite_stockage_nom:
                    if unite_stockage_nom not in unites_stockage_cache:
                        # Vérifier si l'unité de stockage existe
                        unites_existantes = crud.get_unites_stockage(db) or []
                        unite_existe = any(u.nom_unite == unite_stockage_nom for u in unites_existantes)
                        
                        if not unite_existe:
                            # Créer l'unité de stockage
                            code_unite = unite_stockage_nom.upper().replace(' ', '_')[:20]
                            symbole = unite_stockage_nom[:10]
                            
                            unite_data = schemas.UniteStockageCreate(
                                code_unite=code_unite,
                                nom_unite=unite_stockage_nom,
                                symbole=symbole,
                                description=f"Unité créée automatiquement lors de l'import",
                                type_unite='Autre',
                                facteur_conversion=1.0000,
                                unite_base=symbole,
                                statut='Actif'
                            )
                            
                            try:
                                result = crud.create_unite_stockage(db=db, unite=unite_data)
                                if result:
                                    stats['unites_stockage_creees'] += 1
                                    unites_stockage_cache[unite_stockage_nom] = True
                                else:
                                    stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création unité de stockage {unite_stockage_nom}")
                            except Exception as e:
                                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création unité de stockage {unite_stockage_nom} - {str(e)}")
                        else:
                            unites_stockage_cache[unite_stockage_nom] = True
                
                # === TRAITEMENT DES UNITÉS DE COMMANDE ===
                unite_commande_nom = produit_data.get('unite_commande')
                if unite_commande_nom:
                    if unite_commande_nom not in unites_commande_cache:
                        # Vérifier si l'unité de commande existe
                        unites_existantes = crud.get_unites_commande(db) or []
                        unite_existe = any(u.nom_unite == unite_commande_nom for u in unites_existantes)
                        
                        if not unite_existe:
                            # Créer l'unité de commande
                            code_unite = unite_commande_nom.upper().replace(' ', '_')[:20]
                            symbole = unite_commande_nom[:10]
                            
                            unite_data = schemas.UniteCommandeCreate(
                                code_unite=code_unite,
                                nom_unite=unite_commande_nom,
                                symbole=symbole,
                                description=f"Unité créée automatiquement lors de l'import",
                                type_unite='Autre',
                                quantite_unitaire=1,
                                facteur_conversion=1.0000,
                                statut='Actif'
                            )
                            
                            try:
                                result = crud.create_unite_commande(db=db, unite=unite_data)
                                if result:
                                    stats['unites_commande_creees'] += 1
                                    unites_commande_cache[unite_commande_nom] = True
                                else:
                                    stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création unité de commande {unite_commande_nom}")
                            except Exception as e:
                                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création unité de commande {unite_commande_nom} - {str(e)}")
                        else:
                            unites_commande_cache[unite_commande_nom] = True
                
                # === TRAITEMENT DE LA HIÉRARCHIE SITE → LIEU → EMPLACEMENT ===
                site_nom = str(row.get('Site', '')).strip() if pd.notna(row.get('Site')) else None
                lieu_nom = str(row.get('Lieu', '')).strip() if pd.notna(row.get('Lieu')) else None
                emplacement_nom = str(row.get('Emplacement', '')).strip() if pd.notna(row.get('Emplacement')) else None
                
                # Nettoyer les valeurs 'nan'
                if site_nom == 'nan':
                    site_nom = None
                if lieu_nom == 'nan':
                    lieu_nom = None
                if emplacement_nom == 'nan':
                    emplacement_nom = None
                
                site_id = None
                lieu_id = None
                
                # Traiter le site
                if site_nom:
                    if site_nom not in sites_cache:
                        # Vérifier si le site existe
                        sites_existants = crud.get_sites(db) or []
                        site_existant = next((s for s in sites_existants if s.nom_site == site_nom), None)
                        
                        if not site_existant:
                            # Créer le site avec un code unique (max 20 caractères)
                            timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
                            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
                            code_site = f"S{timestamp}{random_suffix}"  # S + 12 + 4 = 17 caractères max
                            
                            site_data = schemas.SiteCreate(
                                code_site=code_site,
                                nom_site=site_nom,
                                adresse='',
                                ville='',
                                code_postal='',
                                pays='France',
                                responsable='',
                                telephone='',
                                email='',
                                statut='Actif'
                            )
                            
                            try:
                                result = crud.create_site(db=db, site=site_data)
                                if result:
                                    stats['sites_crees'] += 1
                                    sites_cache[site_nom] = result.id
                                    site_id = result.id
                                else:
                                    stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création site {site_nom}")
                            except Exception as e:
                                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création site {site_nom} - {str(e)}")
                        else:
                            sites_cache[site_nom] = site_existant.id
                            site_id = site_existant.id
                    else:
                        site_id = sites_cache[site_nom]
                
                # Traiter le lieu
                if lieu_nom and site_id:
                    lieu_key = f"{site_id}_{lieu_nom}"
                    if lieu_key not in lieux_cache:
                        # Vérifier si le lieu existe
                        lieux_existants = crud.get_lieux_by_site(db, site_id=site_id) or []
                        lieu_existant = next((l for l in lieux_existants if l.nom_lieu == lieu_nom), None)
                        
                        if not lieu_existant:
                            # Créer le lieu avec un code unique
                            timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
                            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
                            code_lieu = f"L{timestamp}{random_suffix}"  # L + 12 + 4 = 17 caractères max
                            
                            lieu_data = schemas.LieuCreate(
                                code_lieu=code_lieu,
                                nom_lieu=lieu_nom,
                                site_id=site_id,
                                type_lieu='',
                                niveau='',
                                surface=None,
                                responsable='',
                                statut='Actif'
                            )
                            
                            try:
                                result = crud.create_lieu(db=db, lieu=lieu_data)
                                if result:
                                    stats['lieux_crees'] += 1
                                    lieux_cache[lieu_key] = result.id
                                    lieu_id = result.id
                                else:
                                    stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création lieu {lieu_nom}")
                            except Exception as e:
                                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création lieu {lieu_nom} - {str(e)}")
                        else:
                            lieux_cache[lieu_key] = lieu_existant.id
                            lieu_id = lieu_existant.id
                    else:
                        lieu_id = lieux_cache[lieu_key]
                elif lieu_nom and not site_id:
                    # Si pas de site_id, on ne peut pas créer le lieu
                    stats['erreurs'].append(f"Ligne {ligne_num}: Impossible de créer le lieu {lieu_nom} - site manquant")
                
                # Traiter l'emplacement
                if emplacement_nom and lieu_id:
                    emplacement_key = f"{lieu_id}_{emplacement_nom}"
                    if emplacement_key not in emplacements_cache:
                        # Vérifier si l'emplacement existe
                        emplacements_existants = crud.get_emplacements_by_lieu(db, lieu_id=lieu_id) or []
                        emplacement_existant = next((e for e in emplacements_existants if e.nom_emplacement == emplacement_nom), None)
                        
                        if not emplacement_existant:
                            # Créer l'emplacement avec un code unique
                            timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
                            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
                            code_emplacement = f"E{timestamp}{random_suffix}"  # E + 12 + 4 = 17 caractères max
                            
                            emplacement_data = schemas.EmplacementCreate(
                                code_emplacement=code_emplacement,
                                nom_emplacement=emplacement_nom,
                                lieu_id=lieu_id,
                                type_emplacement='',
                                position='',
                                capacite_max=100,
                                temperature_min=None,
                                temperature_max=None,
                                humidite_max=None,
                                conditions_speciales='',
                                responsable='',
                                statut='Actif'
                            )
                            
                            try:
                                result = crud.create_emplacement(db=db, emplacement=emplacement_data)
                                if result:
                                    stats['emplacements_crees'] += 1
                                    emplacements_cache[emplacement_key] = result.id
                                else:
                                    stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création emplacement {emplacement_nom}")
                            except Exception as e:
                                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création emplacement {emplacement_nom} - {str(e)}")
                        else:
                            emplacements_cache[emplacement_key] = emplacement_existant.id
                elif emplacement_nom and not lieu_id:
                    # Si pas de lieu_id, on ne peut pas créer l'emplacement
                    stats['erreurs'].append(f"Ligne {ligne_num}: Impossible de créer l'emplacement {emplacement_nom} - lieu manquant")
                
                # Récupérer les IDs des entités créées/existantes
                emplacement_id = emplacements_cache.get(f"{lieu_id}_{emplacement_nom}") if emplacement_nom and lieu_id else None
                
                # Récupérer l'ID du fournisseur
                fournisseur_id = None
                if fournisseur_nom:
                    fournisseurs_existants = crud.get_fournisseurs(db) or []
                    fournisseur_obj = next((f for f in fournisseurs_existants if f.nom_fournisseur == fournisseur_nom), None)
                    if fournisseur_obj:
                        fournisseur_id = fournisseur_obj.id
                
                # Récupérer les IDs des unités
                unite_stockage_id = None
                unite_commande_id = None
                
                if unite_stockage_nom:
                    unites_stockage_existantes = crud.get_unites_stockage(db) or []
                    unite_stockage_obj = next((u for u in unites_stockage_existantes if u.nom_unite == unite_stockage_nom), None)
                    if unite_stockage_obj:
                        unite_stockage_id = unite_stockage_obj.id
                
                if unite_commande_nom:
                    unites_commande_existantes = crud.get_unites_commande(db) or []
                    unite_commande_obj = next((u for u in unites_commande_existantes if u.nom_unite == unite_commande_nom), None)
                    if unite_commande_obj:
                        unite_commande_id = unite_commande_obj.id
                
                # Ajouter les données de localisation au produit_data (pour compatibilité avec le schéma)
                produit_data['site'] = site_nom
                produit_data['lieu'] = lieu_nom
                produit_data['emplacement'] = emplacement_nom
                produit_data['fournisseur'] = fournisseur_nom
                
                # === CRÉATION OU MISE À JOUR DU PRODUIT ===
                if mode_mise_a_jour and produit_id:
                    # Mise à jour du produit existant - TOUS les champs disponibles avec les IDs des relations
                    produit_final = {
                        'quantite': produit_data.get('quantite', 0),
                        'prix_unitaire': produit_data.get('prix_unitaire', 0.0),
                        'stock_min': produit_data.get('stock_min', 0),
                        'stock_max': produit_data.get('stock_max', 100),
                        'unite_stockage': produit_data.get('unite_stockage'),
                        'unite_commande': produit_data.get('unite_commande'),
                        'site': produit_data.get('site'),
                        'lieu': produit_data.get('lieu'),
                        'emplacement': produit_data.get('emplacement'),
                        'fournisseur': produit_data.get('fournisseur'),
                        'secteur': produit_data.get('secteur'),
                        'categorie': produit_data.get('categorie')
                    }
                    
                    # Nettoyer les valeurs None pour éviter d'écraser avec des valeurs vides
                    produit_final = {k: v for k, v in produit_final.items() if v is not None and str(v).strip() != '' and str(v) != 'nan'}
                    
                    # Mettre à jour directement les relations par ID dans la base de données
                    try:
                        produit_existant = crud.get_inventaire_by_id(db, inventaire_id=produit_id)
                        if produit_existant:
                            # Mettre à jour les IDs des relations
                            if site_id is not None:
                                produit_existant.site_id = site_id
                            if lieu_id is not None:
                                produit_existant.lieu_id = lieu_id
                            if emplacement_id is not None:
                                produit_existant.emplacement_id = emplacement_id
                            if fournisseur_id is not None:
                                produit_existant.fournisseur_id = fournisseur_id
                            if unite_stockage_id is not None:
                                produit_existant.unite_stockage_id = unite_stockage_id
                            if unite_commande_id is not None:
                                produit_existant.unite_commande_id = unite_commande_id
                            
                            # Commit les changements des relations
                            db.commit()
                            db.refresh(produit_existant)
                    except Exception as e:
                        print(f"Erreur mise à jour relations: {e}")
                    
                    # Puis mettre à jour les autres champs via le schéma
                    update_data = schemas.InventaireUpdate(**produit_final)
                    result = crud.update_inventaire(db=db, inventaire_id=produit_id, inventaire=update_data)
                    if result:
                        stats['produits_mis_a_jour'] += 1
                    else:
                        stats['erreurs'].append(f"Ligne {ligne_num}: Erreur mise à jour produit {designation}")
                else:
                    # Création d'un nouveau produit
                    # Générer un code QR automatique à 10 chiffres (unique)
                    qr_code = None
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        qr_code = ''.join(random.choices(string.digits, k=10))
                        # Vérifier l'unicité du code QR
                        existing_by_code = crud.get_inventaire_by_code(db, code=qr_code)
                        existing_by_ref = crud.get_inventaire_by_reference(db, reference=qr_code)
                        if not existing_by_code and not existing_by_ref:
                            break
                        if attempt == max_attempts - 1:
                            stats['erreurs'].append(f"Ligne {ligne_num}: Impossible de générer un code QR unique")
                            continue
                    
                    if not qr_code:
                        continue
                    
                    produit_final = {
                        'code': qr_code,
                        'reference': qr_code,
                        'reference_fournisseur': produit_data.get('reference_fournisseur'),
                        'produits': produit_data['designation'],
                        'unite_stockage': produit_data.get('unite_stockage'),
                        'unite_commande': produit_data.get('unite_commande'),
                        'stock_min': produit_data.get('stock_min', 0),
                        'stock_max': produit_data.get('stock_max', 100),
                        'site': produit_data.get('site'),
                        'lieu': produit_data.get('lieu'),
                        'emplacement': produit_data.get('emplacement'),
                        'fournisseur': produit_data.get('fournisseur'),
                        'prix_unitaire': produit_data.get('prix_unitaire', 0.0),
                        'categorie': produit_data.get('categorie'),
                        'secteur': produit_data.get('secteur'),
                        'quantite': produit_data.get('quantite', 0)
                    }
                    
                    # Préparer les données pour l'API
                    produit_create_data = schemas.InventaireCreate(**produit_final)
                    
                    # Créer le produit
                    result = crud.create_inventaire(db=db, inventaire=produit_create_data)
                    if result:
                        stats['produits_crees'] += 1
                    else:
                        stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création produit {designation}")
                        
            except Exception as e:
                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur - {str(e)}")
        
        # Préparer le message de résultat
        message = f"Importation terminée:\n"
        message += f"• {stats['produits_crees']} produits créés\n"
        
        if stats['produits_mis_a_jour'] > 0:
            message += f"• {stats['produits_mis_a_jour']} produits mis à jour\n"
        
        if stats['produits_ignores'] > 0:
            message += f"• {stats['produits_ignores']} produits ignorés (doublons)\n"
        
        message += f"• {stats['fournisseurs_crees']} fournisseurs créés\n"
        message += f"• {stats['sites_crees']} sites créés\n"
        message += f"• {stats['lieux_crees']} lieux créés\n"
        message += f"• {stats['emplacements_crees']} emplacements créés\n"
        message += f"• {stats['unites_stockage_creees']} unités de stockage créées\n"
        message += f"• {stats['unites_commande_creees']} unités de commande créées\n"
        
        if stats['erreurs']:
            message += f"\n{len(stats['erreurs'])} erreurs:\n"
            message += "\n".join(stats['erreurs'][:10])  # Limiter à 10 erreurs
            if len(stats['erreurs']) > 10:
                message += f"\n... et {len(stats['erreurs']) - 10} autres erreurs"
        
        return JSONResponse({
            'success': True,
            'message': message,
            'stats': stats
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur lors de l\'importation: {str(e)}'})

@app.post("/api/produits")
async def creer_produit(request: Request, db: Session = Depends(get_db)):
    """Créer un nouveau produit via l'interface web"""
    try:
        data = await request.json()
        print(f"Données reçues pour création de produit: {data}")  # Debug
        
        # Validation des champs requis
        if not data.get('designation'):
            return JSONResponse({'success': False, 'message': 'La désignation est requise'})
        
        # Générer un code QR automatique à 10 chiffres (unique)
        import random
        import string
        qr_code = None
        max_attempts = 10
        
        for attempt in range(max_attempts):
            qr_code = ''.join(random.choices(string.digits, k=10))
            # Vérifier l'unicité du code QR
            existing_by_code = crud.get_inventaire_by_code(db, code=qr_code)
            existing_by_ref = crud.get_inventaire_by_reference(db, reference=qr_code)
            if not existing_by_code and not existing_by_ref:
                break
            if attempt == max_attempts - 1:
                return JSONResponse({'success': False, 'message': 'Impossible de générer un code QR unique'})
        
        print(f"Code QR généré: {qr_code}")  # Debug
        
        # Préparer les données pour l'API avec validation des types
        try:
            produit_data = schemas.InventaireCreate(
                code=qr_code,
                reference=qr_code,
                reference_fournisseur=data.get('reference_fournisseur') or None,
                produits=data.get('designation', ''),
                unite_stockage=data.get('unite_stockage') or None,
                unite_commande=data.get('unite_commande') or None,
                stock_min=int(data.get('seuil_alerte', 0)) if data.get('seuil_alerte') and str(data.get('seuil_alerte')).strip() else 0,
                stock_max=int(data.get('stock_max', 100)) if data.get('stock_max') and str(data.get('stock_max')).strip() else 100,
                site=data.get('site') or None,
                lieu=data.get('lieu') or None,
                emplacement=data.get('emplacement') or None,
                fournisseur=data.get('fournisseur') or None,
                prix_unitaire=float(data.get('prix_unitaire', 0)) if data.get('prix_unitaire') and str(data.get('prix_unitaire')).strip() else 0.0,
                categorie=data.get('categorie') or None,
                secteur=data.get('secteur') or None,
                quantite=int(data.get('quantite', 0)) if data.get('quantite') and str(data.get('quantite')).strip() else 0
            )
            print(f"Données validées: {produit_data}")  # Debug
        except ValueError as ve:
            print(f"Erreur de validation Pydantic: {ve}")  # Debug
            return JSONResponse({'success': False, 'message': f'Erreur de validation des données: {str(ve)}'})
        
        result = crud.create_inventaire(db=db, inventaire=produit_data)
        print(f"Résultat création: {result}")  # Debug
        
        if result:
            # Nettoyer l'objet result pour la réponse JSON avec conversion des dates
            produit_dict = clean_sqlalchemy_object_for_json(result)
            return JSONResponse({'success': True, 'message': 'Produit créé avec succès', 'produit': produit_dict})
        else:
            return JSONResponse({'success': False, 'message': 'Erreur lors de la création du produit'})
            
    except Exception as e:
        print(f"Erreur dans creer_produit: {e}")  # Debug
        import traceback
        traceback.print_exc()  # Debug
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/lieux/site/{site_id}")
async def get_lieux_by_site_api(site_id: int, db: Session = Depends(get_db)):
    """Récupérer les lieux d'un site pour l'interface web"""
    try:
        lieux = crud.get_lieux_by_site(db, site_id=site_id)
        return JSONResponse({'success': True, 'lieux': [clean_sqlalchemy_object_for_json(l) for l in lieux]})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/emplacements/lieu/{lieu_id}")
async def get_emplacements_by_lieu_api(lieu_id: int, db: Session = Depends(get_db)):
    """Récupérer les emplacements d'un lieu pour l'interface web"""
    try:
        emplacements = crud.get_emplacements_by_lieu(db, lieu_id=lieu_id)
        return JSONResponse({'success': True, 'emplacements': [clean_sqlalchemy_object_for_json(e) for e in emplacements]})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/fournisseurs-actifs")
async def get_fournisseurs_actifs(db: Session = Depends(get_db)):
    """Récupérer tous les fournisseurs (pas seulement ceux avec du stock)"""
    try:
        fournisseurs = crud.get_fournisseurs(db)  # Récupérer TOUS les fournisseurs
        return JSONResponse({'success': True, 'fournisseurs': [clean_sqlalchemy_object_for_json(f) for f in fournisseurs]})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/emplacements-actifs")
async def get_emplacements_actifs(db: Session = Depends(get_db)):
    """Récupérer les emplacements qui ont des produits en stock"""
    try:
        emplacements_actifs = crud.get_emplacements_actifs(db)
        return JSONResponse({'success': True, 'emplacements': [clean_sqlalchemy_object_for_json(e) for e in emplacements_actifs]})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/unites-stockage")
async def get_unites_stockage_api(db: Session = Depends(get_db)):
    """Récupérer toutes les unités de stockage actives"""
    try:
        unites = crud.get_unites_stockage_actives(db)
        return JSONResponse({'success': True, 'unites': [clean_sqlalchemy_object_for_json(u) for u in unites]})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/unites-commande")
async def get_unites_commande_api(db: Session = Depends(get_db)):
    """Récupérer toutes les unités de commande actives"""
    try:
        unites = crud.get_unites_commande_actives(db)
        return JSONResponse({'success': True, 'unites': [clean_sqlalchemy_object_for_json(u) for u in unites]})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/unites-stockage/{unite_id}")
async def get_unite_stockage_api(unite_id: int, db: Session = Depends(get_db)):
    """Récupérer une unité de stockage par ID"""
    try:
        unite = crud.get_unite_stockage_by_id(db, unite_id=unite_id)
        if unite:
            return JSONResponse({'success': True, 'unite': clean_sqlalchemy_object_for_json(unite)})
        else:
            return JSONResponse({'success': False, 'message': 'Unité non trouvée'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/unites-commande/{unite_id}")
async def get_unite_commande_api(unite_id: int, db: Session = Depends(get_db)):
    """Récupérer une unité de commande par ID"""
    try:
        unite = crud.get_unite_commande_by_id(db, unite_id=unite_id)
        if unite:
            return JSONResponse({'success': True, 'unite': clean_sqlalchemy_object_for_json(unite)})
        else:
            return JSONResponse({'success': False, 'message': 'Unité non trouvée'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.post("/api/unites-stockage")
async def creer_unite_stockage_api(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Créer une nouvelle unité de stockage"""
    try:
        data = await request.json()
        
        # Créer l'objet UniteStockageCreate
        unite_data = schemas.UniteStockageCreate(
            code_unite=data.get('code_unite'),
            nom_unite=data.get('nom_unite'),
            symbole=data.get('symbole'),
            description=data.get('description'),
            type_unite=data.get('type_unite'),
            facteur_conversion=float(data.get('facteur_conversion', 1.0)),
            unite_base=data.get('unite_base'),
            statut=data.get('statut', 'Actif')
        )
        
        # Vérifier si le code ou nom existe déjà
        existing_code = crud.get_unite_stockage_by_code(db, code_unite=unite_data.code_unite)
        if existing_code:
            return JSONResponse({'success': False, 'message': 'Une unité avec ce code existe déjà'})
        
        existing_nom = crud.get_unite_stockage_by_nom(db, nom_unite=unite_data.nom_unite)
        if existing_nom:
            return JSONResponse({'success': False, 'message': 'Une unité avec ce nom existe déjà'})
        
        # Créer l'unité
        unite = crud.create_unite_stockage(db=db, unite=unite_data)
        
        return JSONResponse({
            'success': True, 
            'message': 'Unité de stockage créée avec succès',
            'unite': clean_sqlalchemy_object_for_json(unite)
        })
        
    except ValueError as e:
        return JSONResponse({'success': False, 'message': f'Erreur de validation: {str(e)}'})
    except Exception as e:
        print(f"Erreur lors de la création de l'unité de stockage: {e}")
        return JSONResponse({'success': False, 'message': f'Erreur lors de la création: {str(e)}'})

@app.post("/api/unites-commande")
async def creer_unite_commande_api(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Créer une nouvelle unité de commande"""
    try:
        data = await request.json()
        
        # Créer l'objet UniteCommandeCreate
        unite_data = schemas.UniteCommandeCreate(
            code_unite=data.get('code_unite'),
            nom_unite=data.get('nom_unite'),
            symbole=data.get('symbole'),
            description=data.get('description'),
            type_unite=data.get('type_unite'),
            quantite_unitaire=int(data.get('quantite_unitaire', 1)),
            facteur_conversion=float(data.get('facteur_conversion', 1.0)),
            statut=data.get('statut', 'Actif')
        )
        
        # Vérifier si le code ou nom existe déjà
        existing_code = crud.get_unite_commande_by_code(db, code_unite=unite_data.code_unite)
        if existing_code:
            return JSONResponse({'success': False, 'message': 'Une unité avec ce code existe déjà'})
        
        existing_nom = crud.get_unite_commande_by_nom(db, nom_unite=unite_data.nom_unite)
        if existing_nom:
            return JSONResponse({'success': False, 'message': 'Une unité avec ce nom existe déjà'})
        
        # Créer l'unité
        unite = crud.create_unite_commande(db=db, unite=unite_data)
        
        return JSONResponse({
            'success': True, 
            'message': 'Unité de commande créée avec succès',
            'unite': clean_sqlalchemy_object_for_json(unite)
        })
        
    except ValueError as e:
        return JSONResponse({'success': False, 'message': f'Erreur de validation: {str(e)}'})
    except Exception as e:
        print(f"Erreur lors de la création de l'unité de commande: {e}")
        return JSONResponse({'success': False, 'message': f'Erreur lors de la création: {str(e)}'})

@app.put("/api/unites-stockage/{unite_id}")
async def modifier_unite_stockage_api(unite_id: int, request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Modifier une unité de stockage"""
    try:
        data = await request.json()
        
        # Vérifier si l'unité existe
        unite_existante = crud.get_unite_stockage_by_id(db, unite_id=unite_id)
        if not unite_existante:
            return JSONResponse({'success': False, 'message': 'Unité non trouvée'})
        
        # Créer l'objet de mise à jour
        unite_data = schemas.UniteStockageUpdate(
            code_unite=data.get('code_unite'),
            nom_unite=data.get('nom_unite'),
            symbole=data.get('symbole'),
            description=data.get('description'),
            type_unite=data.get('type_unite'),
            facteur_conversion=float(data.get('facteur_conversion', 1.0)),
            unite_base=data.get('unite_base'),
            statut=data.get('statut', 'Actif')
        )
        
        # Mettre à jour l'unité
        unite = crud.update_unite_stockage(db=db, unite_id=unite_id, unite=unite_data)
        
        return JSONResponse({
            'success': True, 
            'message': 'Unité de stockage modifiée avec succès',
            'unite': clean_sqlalchemy_object_for_json(unite)
        })
        
    except Exception as e:
        print(f"Erreur lors de la modification de l'unité de stockage: {e}")
        return JSONResponse({'success': False, 'message': f'Erreur lors de la modification: {str(e)}'})

@app.delete("/api/unites-stockage/{unite_id}")
async def supprimer_unite_stockage_api(unite_id: int, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Supprimer une unité de stockage"""
    try:
        # Vérifier si l'unité existe
        unite_existante = crud.get_unite_stockage_by_id(db, unite_id=unite_id)
        if not unite_existante:
            return JSONResponse({'success': False, 'message': 'Unité non trouvée'})
        
        # Vérifier si l'unité est utilisée par des produits
        produits_utilisant = db.query(models.Inventaire).filter(models.Inventaire.unite_stockage_id == unite_id).count()
        if produits_utilisant > 0:
            return JSONResponse({'success': False, 'message': f'Impossible de supprimer: {produits_utilisant} produit(s) utilisent cette unité'})
        
        # Supprimer l'unité
        crud.delete_unite_stockage(db=db, unite_id=unite_id)
        
        return JSONResponse({
            'success': True, 
            'message': 'Unité de stockage supprimée avec succès'
        })
        
    except Exception as e:
        print(f"Erreur lors de la suppression de l'unité de stockage: {e}")
        return JSONResponse({'success': False, 'message': f'Erreur lors de la suppression: {str(e)}'})

@app.put("/api/unites-commande/{unite_id}")
async def modifier_unite_commande_api(unite_id: int, request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Modifier une unité de commande"""
    try:
        data = await request.json()
        
        # Vérifier si l'unité existe
        unite_existante = crud.get_unite_commande_by_id(db, unite_id=unite_id)
        if not unite_existante:
            return JSONResponse({'success': False, 'message': 'Unité non trouvée'})
        
        # Créer l'objet de mise à jour
        unite_data = schemas.UniteCommandeUpdate(
            code_unite=data.get('code_unite'),
            nom_unite=data.get('nom_unite'),
            symbole=data.get('symbole'),
            description=data.get('description'),
            type_unite=data.get('type_unite'),
            quantite_unitaire=int(data.get('quantite_unitaire', 1)),
            facteur_conversion=float(data.get('facteur_conversion', 1.0)),
            statut=data.get('statut', 'Actif')
        )
        
        # Mettre à jour l'unité
        unite = crud.update_unite_commande(db=db, unite_id=unite_id, unite=unite_data)
        
        return JSONResponse({
            'success': True, 
            'message': 'Unité de commande modifiée avec succès',
            'unite': clean_sqlalchemy_object_for_json(unite)
        })
        
    except Exception as e:
        print(f"Erreur lors de la modification de l'unité de commande: {e}")
        return JSONResponse({'success': False, 'message': f'Erreur lors de la modification: {str(e)}'})

@app.delete("/api/unites-commande/{unite_id}")
async def supprimer_unite_commande_api(unite_id: int, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_admin_web)):
    """Supprimer une unité de commande"""
    try:
        # Vérifier si l'unité existe
        unite_existante = crud.get_unite_commande_by_id(db, unite_id=unite_id)
        if not unite_existante:
            return JSONResponse({'success': False, 'message': 'Unité non trouvée'})
        
        # Vérifier si l'unité est utilisée par des produits
        produits_utilisant = db.query(models.Inventaire).filter(models.Inventaire.unite_commande_id == unite_id).count()
        if produits_utilisant > 0:
            return JSONResponse({'success': False, 'message': f'Impossible de supprimer: {produits_utilisant} produit(s) utilisent cette unité'})
        
        # Supprimer l'unité
        crud.delete_unite_commande(db=db, unite_id=unite_id)
        
        return JSONResponse({
            'success': True, 
            'message': 'Unité de commande supprimée avec succès'
        })
        
    except Exception as e:
        print(f"Erreur lors de la suppression de l'unité de commande: {e}")
        return JSONResponse({'success': False, 'message': f'Erreur lors de la suppression: {str(e)}'})


@app.get("/api/produits/{reference}")
async def get_produit_by_reference(reference: str, db: Session = Depends(get_db)):
    """Récupérer un produit par sa référence pour l'interface web"""
    try:
        produit = crud.get_inventaire_by_reference_enrichi(db, reference=reference)
        if produit:
            return JSONResponse({'success': True, 'produit': normalize_produit(produit)})
        else:
            return JSONResponse({'success': False, 'message': 'Produit non trouvé'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.put("/api/produits/{produit_id}")
async def modifier_produit(produit_id: int, request: Request, db: Session = Depends(get_db)):
    """Modifier un produit via l'interface web"""
    try:
        data = await request.json()
        print(f"Données reçues pour modification produit {produit_id}: {data}")  # Debug
        
        # Validation des champs requis
        if not data.get('designation'):
            return JSONResponse({'success': False, 'message': 'La désignation est requise'})
        
        # Préparer les données pour l'API avec validation des types
        try:
            produit_data = schemas.InventaireUpdate(
                reference_fournisseur=data.get('reference_fournisseur') or None,
                produits=data.get('designation', ''),
                unite_stockage=data.get('unite_stockage') or None,
                unite_commande=data.get('unite_commande') or None,
                stock_min=int(data.get('seuil_alerte', 0)) if data.get('seuil_alerte') and str(data.get('seuil_alerte')).strip() else 0,
                stock_max=int(data.get('stock_max', 100)) if data.get('stock_max') and str(data.get('stock_max')).strip() else 100,
                site=data.get('site') or None,
                lieu=data.get('lieu') or None,
                emplacement=data.get('emplacement') or None,
                fournisseur=data.get('fournisseur') or None,
                prix_unitaire=float(data.get('prix_unitaire', 0)) if data.get('prix_unitaire') and str(data.get('prix_unitaire')).strip() else 0.0,
                categorie=data.get('categorie') or None,
                secteur=data.get('secteur') or None,
                quantite=int(data.get('quantite', 0)) if data.get('quantite') and str(data.get('quantite')).strip() else 0
            )
            print(f"Données validées pour modification: {produit_data}")  # Debug
        except ValueError as ve:
            print(f"Erreur de validation Pydantic: {ve}")  # Debug
            return JSONResponse({'success': False, 'message': f'Erreur de validation des données: {str(ve)}'})
        
        result = crud.update_inventaire(db=db, inventaire_id=produit_id, inventaire=produit_data)
        print(f"Résultat modification: {result}")  # Debug
        
        if result:
            # Nettoyer l'objet result pour la réponse JSON
            produit_dict = clean_sqlalchemy_object_for_json(result)
            return JSONResponse({'success': True, 'message': 'Produit modifié avec succès', 'produit': produit_dict})
        else:
            return JSONResponse({'success': False, 'message': 'Produit non trouvé ou erreur lors de la modification'})
            
    except Exception as e:
        print(f"Erreur dans modifier_produit: {e}")  # Debug
        import traceback
        traceback.print_exc()  # Debug
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.delete("/api/produits/{produit_id}")
async def supprimer_produit(produit_id: int, db: Session = Depends(get_db)):
    """Supprimer un produit via l'interface web"""
    try:
        print(f"Tentative de suppression du produit ID: {produit_id}")  # Debug
        
        result = crud.delete_inventaire(db=db, inventaire_id=produit_id)
        print(f"Résultat suppression: {result}")  # Debug
        
        if result:
            return JSONResponse({'success': True, 'message': 'Produit supprimé avec succès'})
        else:
            return JSONResponse({'success': False, 'message': 'Produit non trouvé'})
            
    except Exception as e:
        print(f"Erreur dans supprimer_produit: {e}")  # Debug
        import traceback
        traceback.print_exc()  # Debug
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

# =====================================================
# GESTIONNAIRES D'ERREURS
# =====================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Gestionnaire d'erreur 404"""
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Gestionnaire d'erreur 500"""
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

@app.get("/api/root")
def read_root():
    """Page d'accueil de l'API"""
    return {
        "message": "API GMAO - Gestion de Stock",
        "version": "3.0.0",
        "description": "Système complet de gestion de stock avec interface web intégrée",
        "endpoints": {
            "web": "/",
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

# =====================================================
# ROUTES UTILITAIRES POUR LA GESTION DES RELATIONS
# =====================================================

@app.post("/api/synchroniser-fournisseurs")
async def synchroniser_fournisseurs(db: Session = Depends(get_db)):
    """Synchroniser les relations fournisseur_id pour les produits existants"""
    try:
        liens_crees = crud.synchroniser_relations_fournisseurs(db)
        return JSONResponse({
            'success': True, 
            'message': f'Synchronisation terminée: {liens_crees} produits liés à leurs fournisseurs',
            'liens_crees': liens_crees
        })
    except Exception as e:
        return JSONResponse({
            'success': False, 
            'message': f'Erreur lors de la synchronisation: {str(e)}'
        })

@app.get("/api/fournisseurs-avec-stats")
async def get_fournisseurs_avec_stats(db: Session = Depends(get_db)):
    """Récupérer tous les fournisseurs avec leurs statistiques détaillées"""
    try:
        fournisseurs_stats = crud.get_fournisseurs_avec_stats(db)
        
        result = []
        for fournisseur, nb_produits_lies, valeur_stock_total in fournisseurs_stats:
            fournisseur_dict = clean_sqlalchemy_object_for_json(fournisseur)
            fournisseur_dict['nb_produits_lies'] = nb_produits_lies
            fournisseur_dict['valeur_stock_total'] = float(valeur_stock_total)
            result.append(fournisseur_dict)
        
        return JSONResponse({'success': True, 'fournisseurs': result})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

# =====================================================
# ROUTES POUR LA SYNCHRONISATION HIÉRARCHIQUE
# =====================================================

@app.post("/api/synchroniser-hierarchie")
async def synchroniser_hierarchie(db: Session = Depends(get_db)):
    """Synchroniser les relations hiérarchiques Site > Lieu > Emplacement"""
    try:
        result = crud.synchroniser_relations_hierarchiques(db)
        return JSONResponse({
            'success': True,
            'message': f"Synchronisation terminée. Sites: {result['sites_lies']}, Lieux: {result['lieux_lies']}, Emplacements: {result['emplacements_lies']}",
            'data': result
        })
    except Exception as e:
        return JSONResponse({
            'success': False, 
            'message': f'Erreur lors de la synchronisation: {str(e)}'
        })

@app.get("/api/sites-avec-stats")
async def get_sites_avec_stats(db: Session = Depends(get_db)):
    """Récupérer tous les sites avec leurs statistiques de produits"""
    try:
        sites = crud.get_sites_avec_stats(db)
        return JSONResponse({'success': True, 'sites': sites})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/lieux-avec-stats")
async def get_lieux_avec_stats(db: Session = Depends(get_db)):
    """Récupérer tous les lieux avec leurs statistiques de produits"""
    try:
        lieux = crud.get_lieux_avec_stats(db)
        return JSONResponse({'success': True, 'lieux': lieux})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/emplacements-avec-stats")
async def get_emplacements_avec_stats(db: Session = Depends(get_db)):
    """Récupérer tous les emplacements avec leurs statistiques de produits"""
    try:
        emplacements = crud.get_emplacements_avec_stats(db)
        return JSONResponse({'success': True, 'emplacements': emplacements})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.get("/api/produits-fournisseur/{fournisseur}")
async def get_produits_fournisseur(fournisseur: str, db: Session = Depends(get_db)):
    """Récupérer tous les produits d'un fournisseur pour sélection dans bon de commande"""
    try:
        # Récupérer tous les produits du fournisseur
        produits_raw = crud.get_inventaire_by_fournisseur_enrichi(db, fournisseur=fournisseur)
        
        if not produits_raw:
            return JSONResponse({'success': False, 'message': 'Aucun produit trouvé pour ce fournisseur'})
        
        # Normaliser les données des produits
        produits_normalises = []
        for produit_dict in produits_raw:
            produit_normalise = normalize_produit(produit_dict)
            
            # Calculer la quantité recommandée à commander
            quantite = produit_normalise.get('quantite', 0)
            stock_min = produit_normalise.get('stock_min', 0)
            stock_max = produit_normalise.get('stock_max', 100)
            
            # Quantité recommandée = stock_max - stock_actuel (mais minimum 1)
            qte_recommandee = max(1, stock_max - quantite)
            produit_normalise['qte_recommandee'] = qte_recommandee
            
            produits_normalises.append(produit_normalise)
        
        return JSONResponse({
            'success': True, 
            'produits': produits_normalises,
            'count': len(produits_normalises)
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@app.post("/api/generer-bon-commande")
async def generer_bon_commande(request: Request, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_authentication_web)):
    """Générer un bon de commande PDF pour un fournisseur"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import io
        
        data = await request.json()
        fournisseur_nom = data.get('fournisseur')
        date_livraison = data.get('dateLivraison')
        selected_products = data.get('selectedProducts', [])
        
        if not fournisseur_nom:
            raise HTTPException(status_code=400, detail="Nom du fournisseur requis")
        
        if not selected_products:
            raise HTTPException(status_code=400, detail="Aucun produit sélectionné")
        
        # Récupérer tous les produits du fournisseur (même avec quantité 0)
        produits_raw = crud.get_inventaire_enrichi(db, skip=0, limit=10000)  # Récupérer tous les produits
        all_produits_fournisseur = []
        
        for produit_dict in produits_raw:
            if produit_dict.get('fournisseur') == fournisseur_nom:
                quantite = produit_dict.get('quantite', 0)
                stock_min = produit_dict.get('stock_min', 0)
                stock_max = produit_dict.get('stock_max', 100)
                
                # Calcul du seuil d'alerte (30% entre min et max)
                if stock_max > stock_min:
                    seuil_alerte = stock_min + (stock_max - stock_min) * 0.3
                else:
                    seuil_alerte = stock_min
                
                # Inclure TOUS les produits du fournisseur, pas seulement ceux en alerte
                qte_a_commander = max(0, stock_max - quantite)
                produit_dict['qte_a_commander'] = qte_a_commander
                
                # Ajouter le statut pour information
                if quantite < stock_min:
                    produit_dict['statut_stock'] = 'critique'
                elif quantite <= seuil_alerte:
                    produit_dict['statut_stock'] = 'faible'
                elif quantite > stock_max:
                    produit_dict['statut_stock'] = 'surstock'
                else:
                    produit_dict['statut_stock'] = 'normal'
                
                all_produits_fournisseur.append(produit_dict)
        
        if not all_produits_fournisseur:
            raise HTTPException(status_code=404, detail="Aucun produit trouvé pour ce fournisseur")
        
        # Filtrer selon les produits sélectionnés avec leurs quantités personnalisées
        produits_fournisseur = []
        for selected in selected_products:
            index = selected.get('index')
            custom_quantity = selected.get('quantity')  # Quantité en unités de stockage
            est_supplementaire = selected.get('supplementaire', False)
            
            if est_supplementaire:
                # Article supplémentaire - utiliser les données de l'article fourni
                article_data = selected.get('article', {})
                if article_data:
                    produit = article_data.copy()
                    produit['qte_a_commander_stockage'] = custom_quantity
                else:
                    continue  # Ignorer si pas de données d'article
            elif 0 <= index < len(all_produits_fournisseur):
                produit = all_produits_fournisseur[index].copy()
                produit['qte_a_commander_stockage'] = custom_quantity
            else:
                continue  # Ignorer les index invalides
                
            # Convertir en unités de commande
            unite_commande_nom = produit.get('unite_commande')
            if unite_commande_nom:
                # Récupérer l'unité de commande
                unite_commande = crud.get_unite_commande_by_nom(db, nom_unite=unite_commande_nom)
                if unite_commande:
                    facteur_conversion = unite_commande.facteur_conversion or 1.0
                    quantite_unitaire = unite_commande.quantite_unitaire or 1
                    
                    # Calculer la quantité en unités de commande
                    if facteur_conversion > 1:
                        # Ex: 1 boîte = 20 pièces, donc pour 80 pièces = 80/20 = 4 boîtes
                        qte_commande_exacte = custom_quantity / facteur_conversion
                    else:
                        # Ex: 1 pièce = 1 pièce, donc quantité identique
                        qte_commande_exacte = custom_quantity / quantite_unitaire
                    
                    # Optimiser pour ne pas dépasser le stock max
                    qte_commande_arrondie_sup = math.ceil(qte_commande_exacte)
                    qte_commande_arrondie_inf = math.floor(qte_commande_exacte)
                    
                    # Calculer combien de pièces on aurait avec chaque option
                    if facteur_conversion > 1:
                        pieces_avec_sup = qte_commande_arrondie_sup * facteur_conversion
                        pieces_avec_inf = qte_commande_arrondie_inf * facteur_conversion
                    else:
                        pieces_avec_sup = qte_commande_arrondie_sup * quantite_unitaire
                        pieces_avec_inf = qte_commande_arrondie_inf * quantite_unitaire
                    
                    # Récupérer le stock actuel et max du produit
                    stock_actuel = produit.get('quantite', 0)
                    stock_max = produit.get('stock_max', 100)
                    
                    # Choisir la meilleure option
                    if stock_actuel + pieces_avec_sup <= stock_max:
                        # Si arrondir au supérieur ne dépasse pas le max, on prend ça
                        qte_commande = qte_commande_arrondie_sup
                    elif pieces_avec_inf >= custom_quantity * 0.8:  # Si l'arrondi inférieur couvre au moins 80% du besoin
                        # On prend l'arrondi inférieur pour éviter le surplus
                        qte_commande = qte_commande_arrondie_inf
                    else:
                        # Sinon on prend l'arrondi supérieur même si ça dépasse un peu
                        qte_commande = qte_commande_arrondie_sup
                    
                    produit['qte_a_commander'] = qte_commande
                    produit['unite_commande_symbole'] = unite_commande.symbole
                    produit['facteur_conversion'] = facteur_conversion
                    produit['quantite_unitaire'] = quantite_unitaire
                else:
                    # Pas d'unité de commande trouvée, utiliser les pièces
                    produit['qte_a_commander'] = custom_quantity
                    produit['unite_commande_symbole'] = 'pce'
            else:
                # Pas d'unité de commande définie, utiliser les pièces
                produit['qte_a_commander'] = custom_quantity
                produit['unite_commande_symbole'] = 'pce'
            
            produits_fournisseur.append(produit)
        
        # Récupérer les informations du fournisseur
        fournisseur_obj = crud.get_fournisseur_by_nom(db, nom_fournisseur=fournisseur_nom)
        
        # Créer le PDF en mémoire
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, 
                              topMargin=2*cm, bottomMargin=2*cm)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            alignment=TA_LEFT,
            textColor=colors.darkblue
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=12
        )
        
        # Contenu du PDF
        story = []
        
        # En-tête
        story.append(Paragraph("BON DE COMMANDE", title_style))
        story.append(Spacer(1, 10))
        
        # Informations générales
        date_commande = datetime.now().strftime("%d/%m/%Y")
        numero_commande = f"BC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        info_data = [
            ['N° de commande:', numero_commande, 'Date:', date_commande],
            ['Fournisseur:', fournisseur_nom, 'Demandeur:', current_user.nom_complet],
            ['', '', 'Email :', current_user.email],
        ]
        
        # Ajouter le téléphone si disponible
        if current_user.telephone:
            info_data.append(['', '', 'Téléphone :', current_user.telephone])
        
        # Ajouter la date de livraison si spécifiée
        if date_livraison:
            try:
                date_obj = datetime.strptime(date_livraison, '%Y-%m-%d')
                date_livraison_formatted = date_obj.strftime('%d/%m/%Y')
                info_data.append(['Date livraison souhaitée:', date_livraison_formatted, '', ''])
            except ValueError as e:
                logging.warning(f"Format de date invalide pour la livraison: {date_livraison} - {e}")
                pass
        
        # Créer le tableau principal d'informations
        info_table = Table(info_data, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 8))
        
        # Ajouter les informations du fournisseur si disponibles
        if fournisseur_obj:
            story.append(Paragraph("COORDONNÉES FOURNISSEUR", subtitle_style))
            
            fournisseur_data = []
            
            if fournisseur_obj.adresse:
                fournisseur_data.append(['Adresse:', fournisseur_obj.adresse])
            
            # Contact principal
            if fournisseur_obj.contact1_nom or fournisseur_obj.contact1_prenom:
                contact_nom = f"{fournisseur_obj.contact1_prenom or ''} {fournisseur_obj.contact1_nom or ''}".strip()
                if fournisseur_obj.contact1_fonction:
                    contact_nom += f" ({fournisseur_obj.contact1_fonction})"
                fournisseur_data.append(['Contact:', contact_nom])
            
            if fournisseur_obj.contact1_tel_fixe:
                fournisseur_data.append(['Tél. fixe:', fournisseur_obj.contact1_tel_fixe])
            
            if fournisseur_obj.contact1_tel_mobile:
                fournisseur_data.append(['Tél. mobile:', fournisseur_obj.contact1_tel_mobile])
            
            if fournisseur_obj.contact1_email:
                fournisseur_data.append(['Email:', fournisseur_obj.contact1_email])
            
            # Contact secondaire si disponible
            if fournisseur_obj.contact2_nom or fournisseur_obj.contact2_prenom:
                contact2_nom = f"{fournisseur_obj.contact2_prenom or ''} {fournisseur_obj.contact2_nom or ''}".strip()
                if fournisseur_obj.contact2_fonction:
                    contact2_nom += f" ({fournisseur_obj.contact2_fonction})"
                fournisseur_data.append(['Contact 2:', contact2_nom])
                
                if fournisseur_obj.contact2_tel_fixe:
                    fournisseur_data.append(['Tél. fixe 2:', fournisseur_obj.contact2_tel_fixe])
                
                if fournisseur_obj.contact2_tel_mobile:
                    fournisseur_data.append(['Tél. mobile 2:', fournisseur_obj.contact2_tel_mobile])
                
                if fournisseur_obj.contact2_email:
                    fournisseur_data.append(['Email 2:', fournisseur_obj.contact2_email])
            
            if fournisseur_data:
                fournisseur_table = Table(fournisseur_data, colWidths=[4*cm, 13*cm])
                fournisseur_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                story.append(fournisseur_table)
        
        story.append(Spacer(1, 12))
        
        # Tableau des produits
        story.append(Paragraph("PRODUITS À COMMANDER", subtitle_style))
        
        # Ajouter un résumé par secteur si des secteurs sont présents
        secteurs_count = {}
        for produit in produits_fournisseur:
            secteur = produit.get('secteur', '') or 'Non spécifié'
            if secteur not in secteurs_count:
                secteurs_count[secteur] = 0
            secteurs_count[secteur] += 1
        
        if len(secteurs_count) > 1 and any(s != 'Non spécifié' for s in secteurs_count.keys()):
            secteur_info = "Répartition par secteur : " + " | ".join([f"{secteur}: {count} produit{'s' if count > 1 else ''}" for secteur, count in secteurs_count.items() if secteur != 'Non spécifié'])
            if 'Non spécifié' in secteurs_count:
                secteur_info += f" | Non spécifié: {secteurs_count['Non spécifié']} produit{'s' if secteurs_count['Non spécifié'] > 1 else ''}"
            story.append(Paragraph(secteur_info, normal_style))
            story.append(Spacer(1, 5))
        
        # En-têtes du tableau
        table_data = [
            ['Réf. Fournisseur', 'Désignation', 'Secteur', 'Quantité', 'Unité', 'Qté à commander']
        ]
        
        for produit in produits_fournisseur:
            designation = produit.get('designation') or produit.get('produits', '')
            ref_fournisseur = produit.get('reference_fournisseur', '')
            secteur = produit.get('secteur', '') or '-'
            qte_commande = produit.get('qte_a_commander', 0)
            unite_symbole = produit.get('unite_commande_symbole', 'pce')
            qte_stockage = produit.get('qte_a_commander_stockage', 0)
            facteur = produit.get('facteur_conversion', 1.0)
            
            # Colonne conversion
            if facteur > 1:
                conversion_text = f"= {int(qte_commande * facteur)} pce"
            else:
                conversion_text = f"= {qte_stockage} pce"
            
            table_data.append([
                ref_fournisseur or '-',
                Paragraph(designation[:30] + ('...' if len(designation) > 30 else ''), normal_style),
                secteur,
                str(qte_commande),
                unite_symbole,
                conversion_text
            ])
        
        # Créer le tableau
        table = Table(table_data, colWidths=[3.5*cm, 6.5*cm, 2.5*cm, 2*cm, 2*cm, 3*cm])
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            
            # Corps du tableau
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Réf. Fournisseur centré
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Désignation à gauche
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Secteur centré
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Quantité centrée
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Unité centrée
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Conversion centrée
            
            # Bordures
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 15))
        
        # Pied de page avec informations
        footer_text = f"""
        <b>Observations :</b><br/>

        • Merci de confirmer la disponibilité et les délais de livraison<br/><br/>
        """
        
        story.append(Paragraph(footer_text, normal_style))
        
        # Construire le PDF
        doc.build(story)
        
        # Retourner le PDF
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=bon_commande_{fournisseur_nom}_{date_commande.replace('/', '')}.pdf"
            }
        )
        
    except Exception as e:
        logging.error(f"Erreur génération bon de commande: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du PDF: {str(e)}")

@app.get("/table-atelier/{id_table}", response_class=HTMLResponse)
async def table_atelier_detail(request: Request, id_table: str, db: Session = Depends(get_db), current_user: models.Utilisateur = Depends(auth.require_manager_or_admin_web)):
    """Page de détail d'une table d'atelier"""
    try:
        table = crud.get_table_atelier_by_id_table(db, id_table=id_table)
        if table is None:
            return templates.TemplateResponse("404.html", {"request": request, "current_user": current_user}, status_code=404)
        
        # Générer le QR code pour la table
        qr_code_data = generate_qr_code(id_table)
        
        # Récupérer les demandes associées à cette table
        demandes_table = crud.get_demandes_by_id_table(db, id_table=id_table)
        
        # Calculer les statistiques des demandes
        stats_demandes = {
            'total': len(demandes_table),
            'en_attente': len([d for d in demandes_table if d.statut == 'En attente']),
            'approuvees': len([d for d in demandes_table if d.statut == 'Approuvée']),
            'en_cours': len([d for d in demandes_table if d.statut == 'En cours']),
            'terminees': len([d for d in demandes_table if d.statut == 'Terminée']),
            'rejetees': len([d for d in demandes_table if d.statut == 'Rejetée'])
        }
        
        # Statistiques par mois (6 derniers mois)
        from datetime import datetime, timedelta, date
        from collections import defaultdict
        
        six_mois_ago = datetime.now() - timedelta(days=180)
        demandes_recentes = []
        for d in demandes_table:
            if d.date_demande:
                # Convertir en datetime si c'est une date
                if isinstance(d.date_demande, date) and not isinstance(d.date_demande, datetime):
                    date_demande = datetime.combine(d.date_demande, datetime.min.time())
                else:
                    date_demande = d.date_demande
                
                if date_demande >= six_mois_ago:
                    demandes_recentes.append(d)
        
        stats_mensuelles = defaultdict(int)
        for demande in demandes_recentes:
            if demande.date_demande:
                # Convertir en datetime si c'est une date
                if isinstance(demande.date_demande, date) and not isinstance(demande.date_demande, datetime):
                    date_demande = datetime.combine(demande.date_demande, datetime.min.time())
                else:
                    date_demande = demande.date_demande
                
                mois = date_demande.strftime('%Y-%m')
                stats_mensuelles[mois] += 1
        
        # Trier par mois
        mois_labels = []
        mois_values = []
        for i in range(6):
            date_mois = datetime.now() - timedelta(days=30*i)
            mois_key = date_mois.strftime('%Y-%m')
            mois_label = date_mois.strftime('%b %Y')
            mois_labels.insert(0, mois_label)
            mois_values.insert(0, stats_mensuelles.get(mois_key, 0))
        
        # Statistiques par demandeur (top 5)
        demandeurs_count = defaultdict(int)
        for demande in demandes_table:
            demandeurs_count[demande.demandeur] += 1
        
        top_demandeurs = sorted(demandeurs_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Récupérer les demandes prêtes à livrer pour cette table
        demandes_pretes_livraison = crud.get_demandes_pretes_livraison_table(db, id_table=id_table)
        
        return templates.TemplateResponse("table_atelier_detail.html", {
            "request": request,
            "current_user": current_user,
            "table": clean_sqlalchemy_object(table),
            "qr_code": qr_code_data,
            "demandes": [clean_sqlalchemy_object(d) for d in demandes_table[-20:]],  # 20 dernières demandes
            "stats_demandes": stats_demandes,
            "mois_labels": mois_labels,
            "mois_values": mois_values,
            "top_demandeurs": top_demandeurs,
            "demandes_pretes_livraison": demandes_pretes_livraison
        })
    except Exception as e:
        print(f"Erreur dans table_atelier_detail: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("500.html", {"request": request, "current_user": current_user}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)