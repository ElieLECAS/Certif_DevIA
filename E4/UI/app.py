from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import requests
import os
from datetime import datetime
import qrcode
import io
import base64
from PIL import Image
import json

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration de l'API
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8010')

class APIClient:
    """Client pour communiquer avec l'API FastAPI"""
    
    def __init__(self, base_url):
        self.base_url = base_url
    
    def get(self, endpoint, params=None):
        """Effectuer une requête GET"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API GET {endpoint}: {e}")
            return None
    
    def post(self, endpoint, data=None):
        """Effectuer une requête POST"""
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data)
            if response.status_code == 422:
                print(f"Erreur 422 pour POST {endpoint}")
                print(f"Données envoyées: {data}")
                print(f"Réponse d'erreur: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API POST {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Détails de l'erreur: {e.response.text}")
            return None
    
    def put(self, endpoint, data=None):
        """Effectuer une requête PUT"""
        try:
            response = requests.put(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API PUT {endpoint}: {e}")
            return None
    
    def delete(self, endpoint):
        """Effectuer une requête DELETE"""
        try:
            response = requests.delete(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API DELETE {endpoint}: {e}")
            return None

# Instance du client API
api_client = APIClient(API_BASE_URL)

# =====================================================
# ROUTES PRINCIPALES - MÊME STRUCTURE QUE STREAMLIT
# =====================================================

@app.route('/')
def index():
    """Page d'accueil avec menu principal - équivalent à la sidebar Streamlit"""
    return render_template('index.html')

# =====================================================
# ACTIONS PRINCIPALES
# =====================================================

@app.route('/magasin')
def magasin():
    """Page Magasin - Vue d'ensemble du stock"""
    produits_raw = api_client.get('/inventaire/')
    fournisseurs_raw = api_client.get('/fournisseurs/')
    
    if produits_raw is None:
        produits = []
        flash('Erreur lors du chargement de l\'inventaire', 'error')
    else:
        # Normaliser les données des produits
        produits = [normalize_produit(p.copy()) for p in produits_raw]
    
    if fournisseurs_raw is None:
        fournisseurs = []
    else:
        # L'API retourne un objet avec une propriété 'value' contenant le tableau
        fournisseurs = fournisseurs_raw.get('value', []) if isinstance(fournisseurs_raw, dict) else fournisseurs_raw
    
    # Filtrer par fournisseur si spécifié
    fournisseur_filtre = request.args.get('fournisseur')
    if fournisseur_filtre and fournisseur_filtre != 'tous':
        produits = [p for p in produits if p.get('fournisseur') == fournisseur_filtre]
    
    # Calculer les statistiques comme dans Streamlit
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
    
    return render_template('magasin.html', produits=produits, stats=stats, fournisseurs=fournisseurs, fournisseur_filtre=fournisseur_filtre)

@app.route('/historique-mouvements')
def historique_mouvements():
    """Page Historique des mouvements"""
    historique = api_client.get('/historique/')
    fournisseurs_raw = api_client.get('/fournisseurs/')
    produits_raw = api_client.get('/inventaire/')  # Récupérer les produits pour le lien référence → fournisseur
    
    if historique is None:
        historique = []
        flash('Erreur lors du chargement de l\'historique', 'error')
    
    if fournisseurs_raw is None:
        fournisseurs = []
    else:
        # L'API retourne un objet avec une propriété 'value' contenant le tableau
        fournisseurs = fournisseurs_raw.get('value', []) if isinstance(fournisseurs_raw, dict) else fournisseurs_raw
    
    # Créer un dictionnaire de référence → fournisseur pour le filtrage
    reference_to_fournisseur = {}
    if produits_raw:
        for produit in produits_raw:
            reference = produit.get('reference')
            fournisseur = produit.get('fournisseur')
            if reference and fournisseur:
                reference_to_fournisseur[reference] = fournisseur
    
    # Traiter les données pour l'affichage
    for mouvement in historique:
        # S'assurer que les champs nécessaires existent
        if 'date_mouvement' in mouvement:
            mouvement['date'] = mouvement['date_mouvement']
        elif 'date' not in mouvement:
            mouvement['date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Ajouter le fournisseur basé sur la référence
        reference = mouvement.get('reference')
        if reference and reference in reference_to_fournisseur:
            mouvement['fournisseur'] = reference_to_fournisseur[reference]
        else:
            mouvement['fournisseur'] = 'Non défini'
        
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
    
    # Filtrer par fournisseur si spécifié
    fournisseur_filtre = request.args.get('fournisseur')
    if fournisseur_filtre and fournisseur_filtre != 'tous':
        historique = [h for h in historique if h.get('fournisseur') == fournisseur_filtre]
    
    return render_template('historique_mouvements.html', historique=historique, fournisseurs=fournisseurs, fournisseur_filtre=fournisseur_filtre)

@app.route('/alertes-stock')
def alertes_stock():
    """Page Alertes de stock"""
    produits = api_client.get('/inventaire/')
    fournisseurs_raw = api_client.get('/fournisseurs/')
    
    if produits is None:
        produits = []
        flash('Erreur lors du chargement de l\'inventaire', 'error')
    
    if fournisseurs_raw is None:
        fournisseurs = []
    else:
        # L'API retourne un objet avec une propriété 'value' contenant le tableau
        fournisseurs = fournisseurs_raw.get('value', []) if isinstance(fournisseurs_raw, dict) else fournisseurs_raw
    
    # Calculer les alertes comme dans Streamlit
    produits_avec_alertes = []
    
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
            produit_alerte = produit.copy()
            produit_alerte['statut'] = statut
            produit_alerte['seuil_alerte'] = int(seuil_alerte)
            
            # Ajouter des alias pour la compatibilité avec le template
            if 'produits' in produit_alerte and 'designation' not in produit_alerte:
                produit_alerte['designation'] = produit_alerte['produits']
            
            # S'assurer que les champs manquants ont des valeurs par défaut
            produit_alerte['fournisseur'] = produit_alerte.get('fournisseur') or 'Non défini'
            produit_alerte['emplacement'] = produit_alerte.get('emplacement') or 'Non défini'
            produit_alerte['site'] = produit_alerte.get('site') or 'Non défini'
            produit_alerte['lieu'] = produit_alerte.get('lieu') or 'Non défini'
            
            produits_avec_alertes.append(produit_alerte)
    
    # Filtrer par fournisseur si spécifié
    fournisseur_filtre = request.args.get('fournisseur')
    if fournisseur_filtre and fournisseur_filtre != 'tous':
        produits_avec_alertes = [p for p in produits_avec_alertes if p.get('fournisseur') == fournisseur_filtre]
    
    return render_template('alertes_stock.html', produits=produits_avec_alertes, fournisseurs=fournisseurs, fournisseur_filtre=fournisseur_filtre)

# =====================================================
# DEMANDES
# =====================================================

@app.route('/demande-materiel')
def demande_materiel():
    """Page Demande de matériel - équivalent Streamlit"""
    # Charger les tables d'atelier pour l'identification
    tables = api_client.get('/tables-atelier/') or []
    produits = api_client.get('/inventaire/') or []
    
    return render_template('demande_materiel.html', tables=tables, produits=produits)

@app.route('/gestion-demandes')
def gestion_demandes():
    """Page Gestion des demandes"""
    demandes_list = api_client.get('/demandes/')
    
    if demandes_list is None:
        demandes_list = []
        flash('Erreur lors du chargement des demandes', 'error')
    
    return render_template('gestion_demandes.html', demandes=demandes_list)

# =====================================================
# MOUVEMENTS
# =====================================================

@app.route('/entree-stock', methods=['GET', 'POST'])
def entree_stock():
    """Page Entrée de stock"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Construire le motif avec utilisateur et commentaires
        motif_parts = []
        if data.get('utilisateur'):
            motif_parts.append(f"Utilisateur: {data['utilisateur']}")
        if data.get('commentaires'):
            motif_parts.append(f"Commentaires: {data['commentaires']}")
        motif = " | ".join(motif_parts) if motif_parts else None
        
        mouvement_data = {
            'reference_produit': data['reference'],
            'nature': 'Entrée',
            'quantite': int(data['quantite']),
            'motif': motif
        }
        
        result = api_client.post('/mouvements-stock/', mouvement_data)
        
        if result and result.get('success'):
            return jsonify({'success': True, 'message': 'Entrée enregistrée avec succès'})
        else:
            error_message = result.get('message', 'Erreur lors de l\'enregistrement') if result else 'Erreur lors de l\'enregistrement'
            return jsonify({'success': False, 'message': error_message})
    
    return render_template('entree_stock.html')

@app.route('/sortie-stock', methods=['GET', 'POST'])
def sortie_stock():
    """Page Sortie de stock"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Construire le motif avec utilisateur et commentaires
        motif_parts = []
        if data.get('utilisateur'):
            motif_parts.append(f"Utilisateur: {data['utilisateur']}")
        if data.get('commentaires'):
            motif_parts.append(f"Commentaires: {data['commentaires']}")
        motif = " | ".join(motif_parts) if motif_parts else None
        
        mouvement_data = {
            'reference_produit': data['reference'],
            'nature': 'Sortie',
            'quantite': int(data['quantite']),
            'motif': motif
        }
        
        result = api_client.post('/mouvements-stock/', mouvement_data)
        
        if result and result.get('success'):
            return jsonify({'success': True, 'message': 'Sortie enregistrée avec succès'})
        else:
            error_message = result.get('message', 'Erreur lors de l\'enregistrement') if result else 'Erreur lors de l\'enregistrement'
            return jsonify({'success': False, 'message': error_message})
    
    return render_template('sortie_stock.html')

@app.route('/regule-stock', methods=['GET', 'POST'])
def regule_stock():
    """Page Régule - Ajustement d'inventaire"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Construire le motif avec utilisateur et commentaires
        motif_parts = []
        if data.get('utilisateur'):
            motif_parts.append(f"Utilisateur: {data['utilisateur']}")
        if data.get('commentaires'):
            motif_parts.append(f"Commentaires: {data['commentaires']}")
        motif = " | ".join(motif_parts) if motif_parts else None
        
        mouvement_data = {
            'reference_produit': data['reference'],
            'nature': 'Ajustement',
            'quantite': int(data['quantite']),  # Pour ajustement, c'est la nouvelle quantité totale
            'motif': motif
        }
        
        result = api_client.post('/mouvements-stock/', mouvement_data)
        
        if result and result.get('success'):
            return jsonify({'success': True, 'message': 'Ajustement enregistré avec succès'})
        else:
            error_message = result.get('message', 'Erreur lors de l\'enregistrement') if result else 'Erreur lors de l\'enregistrement'
            return jsonify({'success': False, 'message': error_message})
    
    return render_template('regule_stock.html')

@app.route('/preparer-inventaire')
def preparer_inventaire():
    """Page Préparer l'inventaire"""
    listes = api_client.get('/listes-inventaire/') or []
    produits = api_client.get('/inventaire/') or []
    
    return render_template('preparer_inventaire.html', listes=listes, produits=produits)

# =====================================================
# ADMINISTRATION
# =====================================================

@app.route('/gestion-produits')
def gestion_produits():
    """Page Gestion des produits"""
    produits_raw = api_client.get('/inventaire/') or []
    # Normaliser les données des produits
    produits = [normalize_produit(p.copy()) for p in produits_raw]
    
    fournisseurs = api_client.get('/fournisseurs/') or []
    sites = api_client.get('/sites/') or []
    lieux = api_client.get('/lieux/') or []
    emplacements = api_client.get('/emplacements-hierarchy/') or []
    
    return render_template('gestion_produits.html', produits=produits, 
                         fournisseurs=fournisseurs, sites=sites, lieux=lieux, emplacements=emplacements)

@app.route('/api/import-produits', methods=['POST'])
def import_produits():
    """Importer des produits depuis un fichier Excel"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Aucun fichier fourni'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'})
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'message': 'Format de fichier non supporté. Utilisez Excel (.xlsx ou .xls)'})
        
        # Récupérer l'option de gestion des doublons
        gestion_doublons = request.form.get('gestion_doublons', 'ignorer')  # 'ignorer' ou 'mettre_a_jour'
        
        # Lire le fichier Excel
        import pandas as pd
        import io
        
        # Lire le fichier Excel
        df = pd.read_excel(io.BytesIO(file.read()))
        
        # Vérifier les colonnes requises
        colonnes_requises = ['Désignation']
        colonnes_manquantes = [col for col in colonnes_requises if col not in df.columns]
        if colonnes_manquantes:
            return jsonify({
                'success': False, 
                'message': f'Colonnes manquantes: {", ".join(colonnes_manquantes)}'
            })
        
        # Statistiques d'importation
        stats = {
            'total_lignes': len(df),
            'produits_crees': 0,
            'produits_ignores': 0,  # Produits déjà existants
            'produits_mis_a_jour': 0,  # Produits existants mis à jour
            'fournisseurs_crees': 0,
            'sites_crees': 0,
            'lieux_crees': 0,
            'emplacements_crees': 0,
            'erreurs': []
        }
        
        # Caches pour éviter les doublons
        fournisseurs_cache = {}
        sites_cache = {}
        lieux_cache = {}
        emplacements_cache = {}
        
        # Traiter chaque ligne
        for index, row in df.iterrows():
            try:
                ligne_num = index + 2  # +2 car index commence à 0 et ligne 1 = en-têtes
                
                # Petite pause pour éviter les conflits de timestamp
                import time
                time.sleep(0.001)  # 1ms de pause
                
                # Extraire les données de base
                designation = str(row.get('Désignation', '')).strip()
                if not designation or designation == 'nan':
                    stats['erreurs'].append(f"Ligne {ligne_num}: Désignation manquante")
                    continue
                
                # Vérifier si le produit existe déjà avant de continuer le traitement
                fournisseur_nom = str(row.get('Fournisseur Standard', '')).strip() if pd.notna(row.get('Fournisseur Standard')) else None
                if fournisseur_nom and fournisseur_nom == 'nan':
                    fournisseur_nom = None
                
                reference_fournisseur = str(row.get('Référence fournisseur', '')).strip() if pd.notna(row.get('Référence fournisseur')) else None
                if reference_fournisseur and reference_fournisseur == 'nan':
                    reference_fournisseur = None
                
                # Vérifier l'existence du produit par référence fournisseur
                produit_existant = None
                if reference_fournisseur:
                    produit_existant = produit_existe_par_reference_fournisseur(reference_fournisseur, fournisseur_nom)
                
                if produit_existant:
                    if gestion_doublons == 'ignorer':
                        stats['produits_ignores'] += 1
                        print(f"Ligne {ligne_num}: Produit avec référence fournisseur '{reference_fournisseur}' déjà existant - ignoré")
                        continue
                    elif gestion_doublons == 'mettre_a_jour':
                        # On va mettre à jour le produit existant
                        print(f"Ligne {ligne_num}: Produit avec référence fournisseur '{reference_fournisseur}' déjà existant - mise à jour")
                        mode_mise_a_jour = True
                        produit_id = produit_existant.get('id')
                    else:
                        stats['produits_ignores'] += 1
                        continue
                else:
                    mode_mise_a_jour = False
                    produit_id = None
                
                # Données du produit
                produit_data = {
                    'designation': designation,
                    'reference_fournisseur': reference_fournisseur,
                    'unite_stockage': str(row.get('Unité de stockage', '')).strip() if pd.notna(row.get('Unité de stockage')) else None,
                    'unite_commande': str(row.get('Unité Commande', '')).strip() if pd.notna(row.get('Unité Commande')) else None,
                    'stock_min': int(row.get('Min', 0)) if pd.notna(row.get('Min')) else 0,
                    'stock_max': int(row.get('Max', 100)) if pd.notna(row.get('Max')) else 100,
                    'prix_unitaire': float(row.get('Prix', 0)) if pd.notna(row.get('Prix')) else 0.0,
                    'categorie': str(row.get('Catégorie', '')).strip() if pd.notna(row.get('Catégorie')) else None,
                    'secteur': str(row.get('Secteur', '')).strip() if pd.notna(row.get('Secteur')) else None,
                    'quantite': int(row.get('Quantité', 0)) if pd.notna(row.get('Quantité')) else 0
                }
                
                # Traiter le fournisseur
                if fournisseur_nom:
                    if fournisseur_nom not in fournisseurs_cache:
                        # Vérifier si le fournisseur existe
                        fournisseurs_existants = api_client.get('/fournisseurs/') or []
                        fournisseur_existe = any(f.get('nom_fournisseur') == fournisseur_nom for f in fournisseurs_existants)
                        
                        if not fournisseur_existe:
                            # Créer le fournisseur
                            from datetime import datetime
                            id_fournisseur = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}{index}"
                            
                            fournisseur_data = {
                                'id_fournisseur': id_fournisseur,
                                'nom_fournisseur': fournisseur_nom,
                                'adresse': '',
                                'contact1_nom': '',
                                'contact1_prenom': '',
                                'contact1_fonction': '',
                                'contact1_tel_fixe': '',
                                'contact1_tel_mobile': '',
                                'contact1_email': '',
                                'contact2_nom': '',
                                'contact2_prenom': '',
                                'contact2_fonction': '',
                                'contact2_tel_fixe': '',
                                'contact2_tel_mobile': '',
                                'contact2_email': '',
                                'statut': 'Actif'
                            }
                            
                            result = api_client.post('/fournisseurs/', fournisseur_data)
                            if result and 'id' in result:
                                stats['fournisseurs_crees'] += 1
                                fournisseurs_cache[fournisseur_nom] = True
                            else:
                                error_detail = result.get('message', 'Erreur inconnue') if result else 'Pas de réponse de l\'API'
                                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création fournisseur {fournisseur_nom} - {error_detail}")
                        else:
                            fournisseurs_cache[fournisseur_nom] = True
                    
                    produit_data['fournisseur'] = fournisseur_nom
                
                # Traiter la hiérarchie Site → Lieu → Emplacement
                site_nom = str(row.get('Site', '')).strip() if pd.notna(row.get('Site')) else None
                lieu_nom = str(row.get('Lieu', '')).strip() if pd.notna(row.get('Lieu')) else None
                emplacement_nom = str(row.get('Emplacement', '')).strip() if pd.notna(row.get('Emplacement')) else None
                
                site_id = None
                lieu_id = None
                
                # Traiter le site
                if site_nom and site_nom != 'nan':
                    if site_nom not in sites_cache:
                        # Vérifier si le site existe
                        sites_existants = api_client.get('/sites/') or []
                        site_existant = next((s for s in sites_existants if s.get('nom_site') == site_nom), None)
                        
                        if not site_existant:
                            # Créer le site avec un code unique (max 20 caractères)
                            from datetime import datetime
                            import random
                            import string
                            import time
                            # Utiliser un timestamp plus court + suffixe aléatoire
                            timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
                            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
                            code_site = f"S{timestamp}{random_suffix}"  # S + 12 + 4 = 17 caractères max
                            
                            site_data = {
                                'code_site': code_site,
                                'nom_site': site_nom,
                                'adresse': '',
                                'ville': '',
                                'code_postal': '',
                                'pays': 'France',
                                'responsable': '',
                                'telephone': '',
                                'email': '',
                                'statut': 'Actif'
                            }
                            
                            result = api_client.post('/sites/', site_data)
                            if result and 'id' in result:
                                stats['sites_crees'] += 1
                                sites_cache[site_nom] = result['id']
                                site_id = result['id']
                            else:
                                error_detail = result.get('message', 'Erreur inconnue') if result else 'Pas de réponse de l\'API'
                                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création site {site_nom} - {error_detail}")
                        else:
                            sites_cache[site_nom] = site_existant['id']
                            site_id = site_existant['id']
                    else:
                        site_id = sites_cache[site_nom]
                    
                    produit_data['site'] = site_nom
                
                # Traiter le lieu
                if lieu_nom and lieu_nom != 'nan':
                    if site_id:
                        lieu_key = f"{site_id}_{lieu_nom}"
                        if lieu_key not in lieux_cache:
                            # Vérifier si le lieu existe
                            lieux_existants = api_client.get('/lieux/') or []
                            lieu_existant = next((l for l in lieux_existants if l.get('nom_lieu') == lieu_nom and l.get('site_id') == site_id), None)
                            
                            if not lieu_existant:
                                # Créer le lieu avec un code unique
                                from datetime import datetime
                                import random
                                import string
                                import time
                                # Utiliser un timestamp plus court + suffixe aléatoire (max 20 caractères)
                                timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
                                random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
                                code_lieu = f"L{timestamp}{random_suffix}"  # L + 12 + 4 = 17 caractères max
                                
                                lieu_data = {
                                    'code_lieu': code_lieu,
                                    'nom_lieu': lieu_nom,
                                    'site_id': site_id,
                                    'type_lieu': '',
                                    'niveau': '',
                                    'surface': None,
                                    'responsable': '',
                                    'statut': 'Actif'
                                }
                                
                                result = api_client.post('/lieux/', lieu_data)
                                if result and 'id' in result:
                                    stats['lieux_crees'] += 1
                                    lieux_cache[lieu_key] = result['id']
                                    lieu_id = result['id']
                                else:
                                    error_detail = result.get('message', 'Erreur inconnue') if result else 'Pas de réponse de l\'API'
                                    stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création lieu {lieu_nom} - {error_detail}")
                            else:
                                lieux_cache[lieu_key] = lieu_existant['id']
                                lieu_id = lieu_existant['id']
                        else:
                            lieu_id = lieux_cache[lieu_key]
                        
                        produit_data['lieu'] = lieu_nom
                    else:
                        # Si pas de site_id, on ne peut pas créer le lieu
                        stats['erreurs'].append(f"Ligne {ligne_num}: Impossible de créer le lieu {lieu_nom} - site manquant")
                
                # Traiter l'emplacement
                if emplacement_nom and emplacement_nom != 'nan':
                    # S'assurer qu'on a un lieu_id valide
                    if lieu_id:
                        emplacement_key = f"{lieu_id}_{emplacement_nom}"
                        if emplacement_key not in emplacements_cache:
                            # Vérifier si l'emplacement existe
                            emplacements_existants = api_client.get('/emplacements-hierarchy/') or []
                            emplacement_existant = next((e for e in emplacements_existants if e.get('nom_emplacement') == emplacement_nom and e.get('lieu_id') == lieu_id), None)
                            
                            if not emplacement_existant:
                                # Créer l'emplacement avec un code unique
                                from datetime import datetime
                                import random
                                import string
                                import time
                                # Utiliser un timestamp plus court + suffixe aléatoire (max 20 caractères)
                                timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
                                random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
                                code_emplacement = f"E{timestamp}{random_suffix}"  # E + 12 + 4 = 17 caractères max
                                
                                emplacement_data = {
                                    'code_emplacement': code_emplacement,
                                    'nom_emplacement': emplacement_nom,
                                    'lieu_id': lieu_id,
                                    'type_emplacement': '',
                                    'position': '',
                                    'capacite_max': 100,
                                    'temperature_min': None,
                                    'temperature_max': None,
                                    'humidite_max': None,
                                    'conditions_speciales': '',
                                    'responsable': '',
                                    'statut': 'Actif'
                                }
                                
                                result = api_client.post('/emplacements/', emplacement_data)
                                if result and 'id' in result:
                                    stats['emplacements_crees'] += 1
                                    emplacements_cache[emplacement_key] = result['id']
                                    print(f"DEBUG: Emplacement créé avec succès: {emplacement_nom} (ID: {result.get('id')}) pour lieu_id: {lieu_id}")
                                else:
                                    error_detail = result.get('message', 'Erreur inconnue') if result else 'Pas de réponse de l\'API'
                                    error_msg = f"Ligne {ligne_num}: Erreur création emplacement {emplacement_nom} pour lieu_id {lieu_id} - {error_detail}"
                                    stats['erreurs'].append(error_msg)
                                    print(f"DEBUG: {error_msg}")
                            else:
                                emplacements_cache[emplacement_key] = emplacement_existant['id']
                        
                        produit_data['emplacement'] = emplacement_nom
                    else:
                        # Si pas de lieu_id, on ne peut pas créer l'emplacement
                        stats['erreurs'].append(f"Ligne {ligne_num}: Impossible de créer l'emplacement {emplacement_nom} - lieu manquant")
                
                # Créer ou mettre à jour le produit
                if mode_mise_a_jour and produit_id:
                    # Mise à jour du produit existant
                    produit_final = {}
                    
                    # Seulement mettre à jour les champs non vides
                    if produit_data.get('reference_fournisseur'):
                        produit_final['reference_fournisseur'] = produit_data.get('reference_fournisseur')
                    if produit_data.get('unite_stockage'):
                        produit_final['unite_stockage'] = produit_data.get('unite_stockage')
                    if produit_data.get('unite_commande'):
                        produit_final['unite_commande'] = produit_data.get('unite_commande')
                    if produit_data.get('stock_min') is not None:
                        produit_final['stock_min'] = produit_data.get('stock_min', 0)
                    if produit_data.get('stock_max') is not None:
                        produit_final['stock_max'] = produit_data.get('stock_max', 100)
                    if produit_data.get('site'):
                        produit_final['site'] = produit_data.get('site')
                    if produit_data.get('lieu'):
                        produit_final['lieu'] = produit_data.get('lieu')
                    if produit_data.get('emplacement'):
                        produit_final['emplacement'] = produit_data.get('emplacement')
                    if produit_data.get('fournisseur'):
                        produit_final['fournisseur'] = produit_data.get('fournisseur')
                    if produit_data.get('prix_unitaire') is not None:
                        produit_final['prix_unitaire'] = produit_data.get('prix_unitaire', 0.0)
                    if produit_data.get('categorie'):
                        produit_final['categorie'] = produit_data.get('categorie')
                    if produit_data.get('secteur'):
                        produit_final['secteur'] = produit_data.get('secteur')
                    # Note: On ne met pas à jour la quantité lors de l'importation pour éviter d'écraser le stock
                    
                    result = api_client.put(f'/inventaire/{produit_id}', produit_final)
                    if result:
                        stats['produits_mis_a_jour'] += 1
                    else:
                        error_detail = result.get('message', 'Erreur inconnue') if result else 'Pas de réponse de l\'API'
                        stats['erreurs'].append(f"Ligne {ligne_num}: Erreur mise à jour produit {designation} - {error_detail}")
                else:
                    # Création d'un nouveau produit
                    # Générer un code QR automatique
                    import random
                    import string
                    qr_code = ''.join(random.choices(string.digits, k=10))
                    
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
                    
                    result = api_client.post('/inventaire/', produit_final)
                    if result and 'id' in result:
                        stats['produits_crees'] += 1
                    else:
                        error_detail = result.get('message', 'Erreur inconnue') if result else 'Pas de réponse de l\'API'
                        stats['erreurs'].append(f"Ligne {ligne_num}: Erreur création produit {designation} - {error_detail}")
                    
            except Exception as e:
                stats['erreurs'].append(f"Ligne {ligne_num}: Erreur - {str(e)}")
        
        # Préparer le message de résultat
        message = f"Importation terminée:\n"
        message += f"• {stats['produits_crees']} produits créés\n"
        if stats['produits_mis_a_jour'] > 0:
            message += f"• {stats['produits_mis_a_jour']} produits mis à jour\n"
        if stats['produits_ignores'] > 0:
            message += f"• {stats['produits_ignores']} produits ignorés (déjà existants)\n"
        message += f"• {stats['fournisseurs_crees']} fournisseurs créés\n"
        message += f"• {stats['sites_crees']} sites créés\n"
        message += f"• {stats['lieux_crees']} lieux créés\n"
        message += f"• {stats['emplacements_crees']} emplacements créés\n"
        
        if stats['erreurs']:
            message += f"\n{len(stats['erreurs'])} erreurs:\n"
            message += "\n".join(stats['erreurs'][:10])  # Limiter à 10 erreurs
            if len(stats['erreurs']) > 10:
                message += f"\n... et {len(stats['erreurs']) - 10} autres erreurs"
        
        return jsonify({
            'success': True,
            'message': message,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur lors de l\'importation: {str(e)}'})

@app.route('/api/produits', methods=['POST'])
def creer_produit():
    """Créer un nouveau produit"""
    try:
        data = request.get_json()
        print(f"Données reçues: {data}")  # Debug
        
        # Validation des champs requis
        if not data.get('designation'):
            return jsonify({'success': False, 'message': 'La désignation est requise'})
        
        # Vérifier si un produit avec cette référence fournisseur existe déjà
        reference_fournisseur = data.get('reference_fournisseur')
        fournisseur = data.get('fournisseur')
        
        # Seulement vérifier si une référence fournisseur est fournie
        if reference_fournisseur and reference_fournisseur.strip():
            produit_existant = produit_existe_par_reference_fournisseur(reference_fournisseur, fournisseur)
            if produit_existant:
                if fournisseur:
                    message = f"Un produit avec la référence fournisseur '{reference_fournisseur}' existe déjà chez le fournisseur '{fournisseur}'"
                else:
                    message = f"Un produit avec la référence fournisseur '{reference_fournisseur}' existe déjà"
                return jsonify({'success': False, 'message': message})
        
        # Générer un code QR automatique à 10 chiffres
        import random
        import string
        qr_code = ''.join(random.choices(string.digits, k=10))
        
        # Préparer les données pour l'API selon le nouveau schéma
        produit_data = {
            'code': qr_code,  # Code QR généré automatiquement
            'reference': qr_code,  # Référence QR unique
            'reference_fournisseur': data.get('reference_fournisseur', '') or None,
            'produits': data.get('designation', ''),  # Utiliser désignation
            'unite_stockage': data.get('unite_stockage', '') or None,
            'unite_commande': data.get('unite_commande', '') or None,
            'stock_min': int(data.get('seuil_alerte', 0)) if data.get('seuil_alerte') else 0,
            'stock_max': int(data.get('stock_max', 100)) if data.get('stock_max') else 100,
            'site': data.get('site', '') or None,
            'lieu': data.get('lieu', '') or None,
            'emplacement': data.get('emplacement', '') or None,
            'fournisseur': data.get('fournisseur', '') or None,
            'prix_unitaire': float(data.get('prix_unitaire', 0)) if data.get('prix_unitaire') else 0.0,
            'categorie': data.get('categorie', '') or None,
            'secteur': data.get('secteur', '') or None,
            'quantite': int(data.get('quantite', 0)) if data.get('quantite') else 0
        }
        
        # Ajouter la description si fournie
        if data.get('description'):
            produit_data['produits'] = f"{data.get('designation')} - {data.get('description')}"
        
        print(f"Données envoyées à l'API: {produit_data}")  # Debug
        
        result = api_client.post('/inventaire/', produit_data)
        print(f"Résultat API: {result}")  # Debug
        
        if result:
            return jsonify({'success': True, 'message': 'Produit créé avec succès', 'produit': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création du produit'})
            
    except Exception as e:
        print(f"Erreur dans creer_produit: {str(e)}")  # Debug
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/produits/<int:produit_id>', methods=['PUT'])
def modifier_produit(produit_id):
    """Modifier un produit existant"""
    try:
        data = request.get_json()
        
        # Préparer les données pour l'API (seulement les champs modifiés)
        produit_data = {}
        
        # Note: La référence QR ne peut pas être modifiée
        
        if data.get('reference_fournisseur') is not None:
            produit_data['reference_fournisseur'] = data.get('reference_fournisseur')
            
        if data.get('designation'):
            if data.get('description'):
                produit_data['produits'] = f"{data.get('designation')} - {data.get('description')}"
            else:
                produit_data['produits'] = data.get('designation')
                
        if data.get('unite_stockage') is not None:
            produit_data['unite_stockage'] = data.get('unite_stockage')
            
        if data.get('unite_commande') is not None:
            produit_data['unite_commande'] = data.get('unite_commande')
                
        if data.get('seuil_alerte') is not None:
            produit_data['stock_min'] = int(data.get('seuil_alerte'))
            
        if data.get('stock_max') is not None:
            produit_data['stock_max'] = int(data.get('stock_max'))
            
        if data.get('site') is not None:
            produit_data['site'] = data.get('site')
            
        if data.get('lieu') is not None:
            produit_data['lieu'] = data.get('lieu')
            
        if data.get('emplacement') is not None:
            produit_data['emplacement'] = data.get('emplacement')
            
        if data.get('fournisseur') is not None:
            produit_data['fournisseur'] = data.get('fournisseur')
            
        if data.get('prix_unitaire') is not None:
            produit_data['prix_unitaire'] = float(data.get('prix_unitaire')) if data.get('prix_unitaire') else 0
            
        if data.get('categorie') is not None:
            produit_data['categorie'] = data.get('categorie')
            
        if data.get('secteur') is not None:
            produit_data['secteur'] = data.get('secteur')
        
        result = api_client.put(f'/inventaire/{produit_id}', produit_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Produit modifié avec succès', 'produit': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification du produit'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/produits/<int:produit_id>', methods=['DELETE'])
def supprimer_produit(produit_id):
    """Supprimer un produit"""
    try:
        result = api_client.delete(f'/inventaire/{produit_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Produit supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression du produit'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/produits/<reference>')
def get_produit_by_reference(reference):
    """Récupérer un produit par sa référence pour modification"""
    try:
        produit = api_client.get(f'/inventaire/reference/{reference}')
        
        if produit:
            return jsonify({'success': True, 'produit': produit})
        else:
            return jsonify({'success': False, 'message': 'Produit non trouvé'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/historique/reference/<reference>')
def historique_by_reference(reference):
    """Récupérer l'historique des mouvements d'un produit par référence"""
    try:
        historique = api_client.get(f'/historique/reference/{reference}')
        
        if historique:
            return jsonify(historique)
        else:
            return jsonify([])
            
    except Exception as e:
        return jsonify([])

@app.route('/mouvement-stock', methods=['POST'])
def mouvement_stock_api():
    """Effectuer un mouvement de stock depuis la page de détail"""
    try:
        data = request.get_json()
        
        # Mapper les natures pour l'API
        nature_mapping = {
            'entree': 'Entrée',
            'sortie': 'Sortie', 
            'inventaire': 'Ajustement'
        }
        
        mouvement_data = {
            'reference_produit': data.get('reference'),
            'nature': nature_mapping.get(data.get('nature'), data.get('nature')),
            'quantite': int(data.get('quantite')),
            'motif': f"Utilisateur: {data.get('utilisateur')}" + (f" | {data.get('commentaires')}" if data.get('commentaires') else "")
        }
        
        result = api_client.post('/mouvements-stock/', mouvement_data)
        
        if result and result.get('success'):
            return jsonify(result)
        else:
            error_message = result.get('message', 'Erreur lors de l\'enregistrement') if result else 'Erreur lors de l\'enregistrement'
            return jsonify({'success': False, 'message': error_message})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/gestion-tables')
def gestion_tables():
    """Page Gestion des tables d'atelier"""
    tables = api_client.get('/tables-atelier/') or []
    
    return render_template('gestion_tables.html', tables=tables)

@app.route('/gestion-fournisseurs')
def gestion_fournisseurs():
    """Page Gestion des fournisseurs"""
    fournisseurs = api_client.get('/fournisseurs/') or []
    print(f"Fournisseurs récupérés: {fournisseurs}")  # Debug
    
    return render_template('gestion_fournisseurs.html', fournisseurs=fournisseurs)

@app.route('/gestion-emplacements')
def gestion_emplacements():
    """Page Gestion de la hiérarchie Site > Lieu > Emplacement"""
    sites = api_client.get('/sites/') or []
    lieux = api_client.get('/lieux/') or []
    emplacements = api_client.get('/emplacements-hierarchy/') or []
    
    return render_template('gestion_emplacements.html', 
                         sites=sites, 
                         lieux=lieux, 
                         emplacements=emplacements)

# =====================================================
# ROUTES UTILITAIRES (COMPATIBILITÉ)
# =====================================================

@app.route('/scanner')
def scanner():
    """Page de scanner QR code"""
    return render_template('scanner.html')

@app.route('/inventaire')
def inventaire():
    """Redirection vers magasin pour compatibilité"""
    return redirect(url_for('magasin'))

@app.route('/produit/<reference>')
def produit_detail(reference):
    """Page de détail d'un produit"""
    produit = api_client.get(f'/inventaire/reference/{reference}')
    
    if produit is None:
        flash('Produit non trouvé', 'error')
        return redirect(url_for('magasin'))
    
    # Générer le QR code
    qr_code_data = generate_qr_code(reference)
    
    return render_template('produit_detail.html', produit=produit, qr_code=qr_code_data)

@app.route('/api/produit/<reference>')
def api_produit(reference):
    """API endpoint pour récupérer un produit par référence (pour le scanner)"""
    produit = api_client.get(f'/inventaire/reference/{reference}')
    
    if produit:
        return jsonify(produit)
    else:
        return jsonify({'error': 'Produit non trouvé'}), 404

# Compatibilité avec les anciennes routes
@app.route('/demandes')
def demandes():
    """Redirection vers gestion des demandes"""
    return redirect(url_for('gestion_demandes'))

@app.route('/nouvelle-demande')
def nouvelle_demande():
    """Redirection vers demande de matériel"""
    return redirect(url_for('demande_materiel'))

@app.route('/stock-faible')
def stock_faible():
    """Redirection vers alertes de stock"""
    return redirect(url_for('alertes_stock'))

@app.route('/mouvement-stock')
def mouvement_stock():
    """Page de sélection du type de mouvement"""
    return render_template('mouvement_stock_menu.html')

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
# FONCTIONS HELPER POUR LES TEMPLATES
# =====================================================

def get_stock_status(produit):
    """Détermine le statut du stock d'un produit"""
    quantite = produit.get('quantite', 0)
    # Normaliser les noms de champs entre API et templates
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
    
    return produit

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

# Enregistrer les fonctions helper pour les templates
app.jinja_env.globals.update(
    get_stock_status=get_stock_status,
    get_status_class=get_status_class,
    get_stock_status_text=get_stock_status_text,
    normalize_produit=normalize_produit,
    moment=moment
)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/api/fournisseurs', methods=['POST'])
def creer_fournisseur():
    """Créer un nouveau fournisseur"""
    try:
        data = request.get_json()
        
        # Générer un ID fournisseur automatique
        import random
        import string
        from datetime import datetime
        id_fournisseur = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Préparer les données pour l'API selon le schéma FournisseurCreate
        fournisseur_data = {
            'id_fournisseur': id_fournisseur,
            'nom_fournisseur': data.get('nom_fournisseur', ''),
            'adresse': data.get('adresse', ''),
            
            # Contact 1
            'contact1_nom': data.get('contact1_nom', ''),
            'contact1_prenom': data.get('contact1_prenom', ''),
            'contact1_fonction': data.get('contact1_fonction', ''),
            'contact1_tel_fixe': data.get('contact1_tel_fixe', ''),
            'contact1_tel_mobile': data.get('contact1_tel_mobile', ''),
            'contact1_email': data.get('contact1_email', ''),
            
            # Contact 2
            'contact2_nom': data.get('contact2_nom', ''),
            'contact2_prenom': data.get('contact2_prenom', ''),
            'contact2_fonction': data.get('contact2_fonction', ''),
            'contact2_tel_fixe': data.get('contact2_tel_fixe', ''),
            'contact2_tel_mobile': data.get('contact2_tel_mobile', ''),
            'contact2_email': data.get('contact2_email', ''),
            
            'statut': data.get('statut', 'Actif')
        }
        
        result = api_client.post('/fournisseurs/', fournisseur_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Fournisseur créé avec succès', 'fournisseur': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création du fournisseur'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/fournisseurs/<int:fournisseur_id>', methods=['PUT'])
def modifier_fournisseur(fournisseur_id):
    """Modifier un fournisseur existant"""
    try:
        data = request.get_json()
        
        # Préparer les données pour l'API (seulement les champs modifiés)
        fournisseur_data = {}
        
        if data.get('nom_fournisseur'):
            fournisseur_data['nom_fournisseur'] = data.get('nom_fournisseur')
            
        if data.get('adresse') is not None:
            fournisseur_data['adresse'] = data.get('adresse')
        
        # Contact 1
        if data.get('contact1_nom') is not None:
            fournisseur_data['contact1_nom'] = data.get('contact1_nom')
        if data.get('contact1_prenom') is not None:
            fournisseur_data['contact1_prenom'] = data.get('contact1_prenom')
        if data.get('contact1_fonction') is not None:
            fournisseur_data['contact1_fonction'] = data.get('contact1_fonction')
        if data.get('contact1_tel_fixe') is not None:
            fournisseur_data['contact1_tel_fixe'] = data.get('contact1_tel_fixe')
        if data.get('contact1_tel_mobile') is not None:
            fournisseur_data['contact1_tel_mobile'] = data.get('contact1_tel_mobile')
        if data.get('contact1_email') is not None:
            fournisseur_data['contact1_email'] = data.get('contact1_email')
        
        # Contact 2
        if data.get('contact2_nom') is not None:
            fournisseur_data['contact2_nom'] = data.get('contact2_nom')
        if data.get('contact2_prenom') is not None:
            fournisseur_data['contact2_prenom'] = data.get('contact2_prenom')
        if data.get('contact2_fonction') is not None:
            fournisseur_data['contact2_fonction'] = data.get('contact2_fonction')
        if data.get('contact2_tel_fixe') is not None:
            fournisseur_data['contact2_tel_fixe'] = data.get('contact2_tel_fixe')
        if data.get('contact2_tel_mobile') is not None:
            fournisseur_data['contact2_tel_mobile'] = data.get('contact2_tel_mobile')
        if data.get('contact2_email') is not None:
            fournisseur_data['contact2_email'] = data.get('contact2_email')
            
        if data.get('statut') is not None:
            fournisseur_data['statut'] = data.get('statut')
        
        result = api_client.put(f'/fournisseurs/{fournisseur_id}', fournisseur_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Fournisseur modifié avec succès', 'fournisseur': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification du fournisseur'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/fournisseurs/<int:fournisseur_id>', methods=['DELETE'])
def supprimer_fournisseur(fournisseur_id):
    """Supprimer un fournisseur"""
    try:
        result = api_client.delete(f'/fournisseurs/{fournisseur_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Fournisseur supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression du fournisseur'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/fournisseurs/<int:fournisseur_id>')
def get_fournisseur_by_id(fournisseur_id):
    """Récupérer un fournisseur par son ID"""
    try:
        result = api_client.get(f'/fournisseurs/{fournisseur_id}')
        
        if result:
            return jsonify({'success': True, 'fournisseur': result})
        else:
            return jsonify({'success': False, 'message': 'Fournisseur non trouvé'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# =====================================================
# ROUTES API POUR LA HIÉRARCHIE SITE > LIEU > EMPLACEMENT
# =====================================================

# SITES
@app.route('/api/sites', methods=['POST'])
def creer_site():
    """Créer un nouveau site"""
    try:
        data = request.get_json()
        
        # Générer un code site automatique (max 20 caractères)
        import random
        import string
        from datetime import datetime
        timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
        code_site = f"S{timestamp}{random_suffix}"  # S + 12 + 4 = 17 caractères max
        
        site_data = {
            'code_site': code_site,
            'nom_site': data.get('nom_site', ''),
            'adresse': data.get('adresse', ''),
            'ville': data.get('ville', ''),
            'code_postal': data.get('code_postal', ''),
            'pays': data.get('pays', 'France'),
            'responsable': data.get('responsable', ''),
            'telephone': data.get('telephone', ''),
            'email': data.get('email', ''),
            'statut': data.get('statut', 'Actif')
        }
        
        result = api_client.post('/sites/', site_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Site créé avec succès', 'site': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création du site'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/sites/<int:site_id>', methods=['PUT'])
def modifier_site(site_id):
    """Modifier un site existant"""
    try:
        data = request.get_json()
        
        site_data = {}
        if data.get('nom_site'):
            site_data['nom_site'] = data.get('nom_site')
        if data.get('adresse') is not None:
            site_data['adresse'] = data.get('adresse')
        if data.get('ville') is not None:
            site_data['ville'] = data.get('ville')
        if data.get('code_postal') is not None:
            site_data['code_postal'] = data.get('code_postal')
        if data.get('pays') is not None:
            site_data['pays'] = data.get('pays')
        if data.get('responsable') is not None:
            site_data['responsable'] = data.get('responsable')
        if data.get('telephone') is not None:
            site_data['telephone'] = data.get('telephone')
        if data.get('email') is not None:
            site_data['email'] = data.get('email')
        if data.get('statut') is not None:
            site_data['statut'] = data.get('statut')
        
        result = api_client.put(f'/sites/{site_id}', site_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Site modifié avec succès', 'site': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification du site'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/sites/<int:site_id>', methods=['DELETE'])
def supprimer_site(site_id):
    """Supprimer un site"""
    try:
        result = api_client.delete(f'/sites/{site_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Site supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression du site'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# LIEUX
@app.route('/api/lieux', methods=['POST'])
def creer_lieu():
    """Créer un nouveau lieu"""
    try:
        data = request.get_json()
        
        # Générer un code lieu automatique
        from datetime import datetime
        timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 12 caractères
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 caractères
        code_lieu = f"L{timestamp}{random_suffix}"  # L + 12 + 4 = 17 caractères max
        
        lieu_data = {
            'code_lieu': code_lieu,
            'nom_lieu': data.get('nom_lieu', ''),
            'site_id': int(data.get('site_id')),
            'type_lieu': data.get('type_lieu', ''),
            'niveau': data.get('niveau', ''),
            'surface': float(data.get('surface', 0)) if data.get('surface') else None,
            'responsable': data.get('responsable', ''),
            'statut': data.get('statut', 'Actif')
        }
        
        result = api_client.post('/lieux/', lieu_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Lieu créé avec succès', 'lieu': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création du lieu'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/lieux/<int:lieu_id>', methods=['PUT'])
def modifier_lieu(lieu_id):
    """Modifier un lieu existant"""
    try:
        data = request.get_json()
        
        lieu_data = {}
        if data.get('nom_lieu'):
            lieu_data['nom_lieu'] = data.get('nom_lieu')
        if data.get('site_id') is not None:
            lieu_data['site_id'] = int(data.get('site_id'))
        if data.get('type_lieu') is not None:
            lieu_data['type_lieu'] = data.get('type_lieu')
        if data.get('niveau') is not None:
            lieu_data['niveau'] = data.get('niveau')
        if data.get('surface') is not None:
            lieu_data['surface'] = float(data.get('surface')) if data.get('surface') else None
        if data.get('responsable') is not None:
            lieu_data['responsable'] = data.get('responsable')
        if data.get('statut') is not None:
            lieu_data['statut'] = data.get('statut')
        
        result = api_client.put(f'/lieux/{lieu_id}', lieu_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Lieu modifié avec succès', 'lieu': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification du lieu'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/lieux/<int:lieu_id>', methods=['DELETE'])
def supprimer_lieu(lieu_id):
    """Supprimer un lieu"""
    try:
        result = api_client.delete(f'/lieux/{lieu_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Lieu supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression du lieu'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/lieux/site/<int:site_id>')
def get_lieux_by_site(site_id):
    """Récupérer les lieux d'un site"""
    try:
        result = api_client.get(f'/lieux/site/{site_id}')
        
        if result is not None:
            return jsonify({'success': True, 'lieux': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la récupération des lieux'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# EMPLACEMENTS
@app.route('/api/emplacements', methods=['POST'])
def creer_emplacement():
    """Créer un nouvel emplacement"""
    try:
        data = request.get_json()
        
        # Générer un code emplacement automatique si non fourni
        code_emplacement = data.get('code_emplacement')
        if not code_emplacement:
            from datetime import datetime
            import random
            import string
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]  # Microseconde tronquée
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            code_emplacement = f"EMP{timestamp}{random_suffix}"
        
        emplacement_data = {
            'code_emplacement': code_emplacement,
            'nom_emplacement': data.get('nom_emplacement', ''),
            'lieu_id': int(data.get('lieu_id')),
            'type_emplacement': data.get('type_emplacement', ''),
            'position': data.get('position', ''),
            'capacite_max': int(data.get('capacite_max', 100)),
            'temperature_min': float(data.get('temperature_min')) if data.get('temperature_min') else None,
            'temperature_max': float(data.get('temperature_max')) if data.get('temperature_max') else None,
            'humidite_max': float(data.get('humidite_max')) if data.get('humidite_max') else None,
            'conditions_speciales': data.get('conditions_speciales', ''),
            'responsable': data.get('responsable', ''),
            'statut': data.get('statut', 'Actif')
        }
        
        result = api_client.post('/emplacements/', emplacement_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Emplacement créé avec succès', 'emplacement': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création de l\'emplacement'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/emplacements/<int:emplacement_id>', methods=['PUT'])
def modifier_emplacement(emplacement_id):
    """Modifier un emplacement existant"""
    try:
        data = request.get_json()
        
        emplacement_data = {}
        if data.get('nom_emplacement'):
            emplacement_data['nom_emplacement'] = data.get('nom_emplacement')
        if data.get('lieu_id') is not None:
            emplacement_data['lieu_id'] = int(data.get('lieu_id'))
        if data.get('type_emplacement') is not None:
            emplacement_data['type_emplacement'] = data.get('type_emplacement')
        if data.get('position') is not None:
            emplacement_data['position'] = data.get('position')
        if data.get('capacite_max') is not None:
            emplacement_data['capacite_max'] = int(data.get('capacite_max'))
        if data.get('temperature_min') is not None:
            emplacement_data['temperature_min'] = float(data.get('temperature_min')) if data.get('temperature_min') else None
        if data.get('temperature_max') is not None:
            emplacement_data['temperature_max'] = float(data.get('temperature_max')) if data.get('temperature_max') else None
        if data.get('humidite_max') is not None:
            emplacement_data['humidite_max'] = float(data.get('humidite_max')) if data.get('humidite_max') else None
        if data.get('conditions_speciales') is not None:
            emplacement_data['conditions_speciales'] = data.get('conditions_speciales')
        if data.get('responsable') is not None:
            emplacement_data['responsable'] = data.get('responsable')
        if data.get('statut') is not None:
            emplacement_data['statut'] = data.get('statut')
        
        result = api_client.put(f'/emplacements/{emplacement_id}', emplacement_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Emplacement modifié avec succès', 'emplacement': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification de l\'emplacement'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/emplacements/<int:emplacement_id>', methods=['DELETE'])
def supprimer_emplacement(emplacement_id):
    """Supprimer un emplacement"""
    try:
        result = api_client.delete(f'/emplacements/{emplacement_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Emplacement supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression de l\'emplacement'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/emplacements/lieu/<int:lieu_id>')
def get_emplacements_by_lieu(lieu_id):
    """Récupérer les emplacements d'un lieu"""
    try:
        result = api_client.get(f'/emplacements/lieu/{lieu_id}')
        
        if result is not None:
            return jsonify({'success': True, 'emplacements': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la récupération des emplacements'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# =====================================================
# FONCTIONS HELPER POUR ÉVITER LES DOUBLONS
# =====================================================

def produit_existe_par_reference_fournisseur(reference_fournisseur, fournisseur=None):
    """Vérifier si un produit existe déjà par référence fournisseur et fournisseur"""
    try:
        # Si pas de référence fournisseur, on ne peut pas vérifier l'unicité
        if not reference_fournisseur or reference_fournisseur.strip() == '':
            return None
            
        produits_existants = api_client.get('/inventaire/') or []
        
        for produit in produits_existants:
            produit_ref_fournisseur = produit.get('reference_fournisseur', '').strip()
            
            # Comparer les références fournisseur (insensible à la casse)
            if produit_ref_fournisseur.lower() == reference_fournisseur.strip().lower():
                # Si un fournisseur est spécifié, vérifier aussi le fournisseur
                if fournisseur:
                    produit_fournisseur = produit.get('fournisseur', '').strip().lower()
                    if produit_fournisseur == fournisseur.strip().lower():
                        return produit
                else:
                    # Si pas de fournisseur spécifié, considérer comme doublon
                    return produit
        
        return None
    except Exception as e:
        print(f"Erreur lors de la vérification d'existence du produit: {e}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 