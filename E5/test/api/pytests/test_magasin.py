import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_db
from database import Base
from models import Inventaire, Fournisseur, Site, Lieu, Emplacement
import schemas

# Configuration de la base de données de test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db():
    """Fixture pour la base de données de test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_fournisseurs(db):
    """Créer des fournisseurs de test"""
    fournisseurs = [
        Fournisseur(
            id_fournisseur="FURN001",
            nom_fournisseur="Fournisseur A",
            adresse="123 Rue Test",
            contact1_tel_fixe="0123456789",
            contact1_email="test@fournisseur-a.com",
            statut="Actif"
        ),
        Fournisseur(
            id_fournisseur="FURN002", 
            nom_fournisseur="Fournisseur B",
            adresse="456 Avenue Test",
            contact1_tel_fixe="0987654321",
            contact1_email="test@fournisseur-b.com",
            statut="Actif"
        ),
        Fournisseur(
            id_fournisseur="FURN003",
            nom_fournisseur="Fournisseur C",
            adresse="789 Boulevard Test",
            contact1_tel_fixe="0555666777",
            contact1_email="test@fournisseur-c.com",
            statut="Inactif"
        )
    ]
    
    for fournisseur in fournisseurs:
        db.add(fournisseur)
    db.commit()
    
    for fournisseur in fournisseurs:
        db.refresh(fournisseur)
    
    return fournisseurs

@pytest.fixture
def sample_sites_lieux_emplacements(db):
    """Créer des sites, lieux et emplacements de test"""
    # Sites
    site1 = Site(code_site="SITE001", nom_site="Site Principal", adresse="123 Site Rue", statut="Actif")
    site2 = Site(code_site="SITE002", nom_site="Site Secondaire", adresse="456 Site Avenue", statut="Actif")
    
    db.add(site1)
    db.add(site2)
    db.commit()
    db.refresh(site1)
    db.refresh(site2)
    
    # Lieux
    lieu1 = Lieu(code_lieu="LIEU001", nom_lieu="Entrepôt A", site_id=site1.id, statut="Actif")
    lieu2 = Lieu(code_lieu="LIEU002", nom_lieu="Entrepôt B", site_id=site1.id, statut="Actif")
    lieu3 = Lieu(code_lieu="LIEU003", nom_lieu="Entrepôt C", site_id=site2.id, statut="Actif")
    
    db.add(lieu1)
    db.add(lieu2)
    db.add(lieu3)
    db.commit()
    db.refresh(lieu1)
    db.refresh(lieu2)
    db.refresh(lieu3)
    
    # Emplacements
    emplacement1 = Emplacement(code_emplacement="EMP001", nom_emplacement="Étagère A1", lieu_id=lieu1.id, statut="Actif")
    emplacement2 = Emplacement(code_emplacement="EMP002", nom_emplacement="Étagère A2", lieu_id=lieu1.id, statut="Actif")
    emplacement3 = Emplacement(code_emplacement="EMP003", nom_emplacement="Étagère B1", lieu_id=lieu2.id, statut="Actif")
    emplacement4 = Emplacement(code_emplacement="EMP004", nom_emplacement="Étagère C1", lieu_id=lieu3.id, statut="Actif")
    
    db.add(emplacement1)
    db.add(emplacement2)
    db.add(emplacement3)
    db.add(emplacement4)
    db.commit()
    
    for emp in [emplacement1, emplacement2, emplacement3, emplacement4]:
        db.refresh(emp)
    
    return {
        'sites': [site1, site2],
        'lieux': [lieu1, lieu2, lieu3],
        'emplacements': [emplacement1, emplacement2, emplacement3, emplacement4]
    }

@pytest.fixture
def sample_produits(db, sample_fournisseurs, sample_sites_lieux_emplacements):
    """Créer des produits de test avec différents statuts de stock"""
    produits = [
        # Stock critique (quantité < stock_min)
        Inventaire(
            code="1234567890",
            reference="1234567890",
            reference_fournisseur="REF001",
            produits="Produit Stock Critique",
            quantite=2,
            stock_min=10,
            stock_max=50,
            prix_unitaire=15.50,
            fournisseur="Fournisseur A",
            site="Site Principal",
            lieu="Entrepôt A",
            emplacement="Étagère A1",
            categorie="Électronique",
            secteur="IT"
        ),
        # Stock faible (quantité <= seuil_alerte)
        Inventaire(
            code="2345678901",
            reference="2345678901",
            reference_fournisseur="REF002",
            produits="Produit Stock Faible",
            quantite=12,
            stock_min=10,
            stock_max=50,
            prix_unitaire=25.00,
            fournisseur="Fournisseur A",
            site="Site Principal",
            lieu="Entrepôt A",
            emplacement="Étagère A2",
            categorie="Mécanique",
            secteur="Production"
        ),
        # Stock normal
        Inventaire(
            code="3456789012",
            reference="3456789012",
            reference_fournisseur="REF003",
            produits="Produit Stock Normal",
            quantite=30,
            stock_min=10,
            stock_max=50,
            prix_unitaire=8.75,
            fournisseur="Fournisseur B",
            site="Site Principal",
            lieu="Entrepôt B",
            emplacement="Étagère B1",
            categorie="Consommables",
            secteur="Maintenance"
        ),
        # Surstock (quantité > stock_max)
        Inventaire(
            code="4567890123",
            reference="4567890123",
            reference_fournisseur="REF004",
            produits="Produit Surstock",
            quantite=75,
            stock_min=10,
            stock_max=50,
            prix_unitaire=12.30,
            fournisseur="Fournisseur B",
            site="Site Secondaire",
            lieu="Entrepôt C",
            emplacement="Étagère C1",
            categorie="Outils",
            secteur="Atelier"
        ),
        # Produit sans fournisseur
        Inventaire(
            code="5678901234",
            reference="5678901234",
            reference_fournisseur="REF005",
            produits="Produit Sans Fournisseur",
            quantite=20,
            stock_min=5,
            stock_max=40,
            prix_unitaire=5.00,
            fournisseur=None,
            site="Site Principal",
            lieu="Entrepôt A",
            emplacement="Étagère A1",
            categorie="Divers",
            secteur="Général"
        )
    ]
    
    for produit in produits:
        db.add(produit)
    db.commit()
    
    for produit in produits:
        db.refresh(produit)
    
    return produits

class TestPageMagasin:
    """Tests pour la page magasin"""
    
    def test_magasin_page_loads(self, sample_produits):
        """Test que la page magasin se charge correctement"""
        response = client.get("/magasin")
        assert response.status_code == 200
        assert "Magasin" in response.text
        assert "Stock critique" in response.text
    
    def test_magasin_displays_stats(self, sample_produits):
        """Test que les statistiques sont affichées correctement"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier que les stats sont présentes
        assert "stock-critique" in response.text or "Stock critique" in response.text
        assert "stock-faible" in response.text or "Bientôt rupture" in response.text
        assert "stock-normal" in response.text or "Stock normal" in response.text
        assert "surstock" in response.text or "Surstock" in response.text
        assert "Valeur totale" in response.text
    
    def test_magasin_displays_products(self, sample_produits):
        """Test que les produits sont affichés"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier que les produits sont présents
        assert "Produit Stock Critique" in response.text
        assert "Produit Stock Faible" in response.text
        assert "Produit Stock Normal" in response.text
        assert "Produit Surstock" in response.text
        assert "Produit Sans Fournisseur" in response.text
    
    def test_magasin_displays_product_details(self, sample_produits):
        """Test que les détails des produits sont affichés"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier les références
        assert "1234567890" in response.text
        assert "2345678901" in response.text
        
        # Vérifier les références fournisseur
        assert "REF001" in response.text
        assert "REF002" in response.text
        
        # Vérifier les fournisseurs
        assert "Fournisseur A" in response.text
        assert "Fournisseur B" in response.text
        
        # Vérifier les emplacements
        assert "Étagère A1" in response.text
        assert "Étagère B1" in response.text
    
    def test_magasin_filter_by_fournisseur(self, sample_produits):
        """Test du filtre par fournisseur"""
        # Test avec Fournisseur A
        response = client.get("/magasin?fournisseur=Fournisseur A")
        assert response.status_code == 200
        assert "Produit Stock Critique" in response.text
        assert "Produit Stock Faible" in response.text
        assert "Produit Stock Normal" not in response.text  # Ce produit est du Fournisseur B
        
        # Test avec Fournisseur B
        response = client.get("/magasin?fournisseur=Fournisseur B")
        assert response.status_code == 200
        assert "Produit Stock Normal" in response.text
        assert "Produit Surstock" in response.text
        assert "Produit Stock Critique" not in response.text  # Ce produit est du Fournisseur A
    
    def test_magasin_filter_tous_fournisseurs(self, sample_produits):
        """Test du filtre 'tous les fournisseurs'"""
        response = client.get("/magasin?fournisseur=tous")
        assert response.status_code == 200
        
        # Tous les produits doivent être visibles
        assert "Produit Stock Critique" in response.text
        assert "Produit Stock Faible" in response.text
        assert "Produit Stock Normal" in response.text
        assert "Produit Surstock" in response.text
        assert "Produit Sans Fournisseur" in response.text
    
    def test_magasin_displays_fournisseur_filter_options(self, sample_produits):
        """Test que les options du filtre fournisseur sont présentes"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier la présence du select de filtre
        assert "fournisseurFilter" in response.text
        assert "Tous les fournisseurs" in response.text
        assert "Fournisseur A" in response.text
        assert "Fournisseur B" in response.text
    
    def test_magasin_search_functionality_elements(self, sample_produits):
        """Test que les éléments de recherche sont présents"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier la présence des éléments de recherche
        assert "searchInput" in response.text
        assert "Rechercher par nom, code ou référence" in response.text
        assert "performSearch" in response.text
    
    def test_magasin_status_filters_elements(self, sample_produits):
        """Test que les filtres de statut sont présents"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier la présence des filtres de statut
        assert "filterProducts" in response.text
        assert "Tous" in response.text
        assert "Critique" in response.text
        assert "Faible" in response.text
        assert "Normal" in response.text
        assert "Surstock" in response.text
    
    def test_magasin_action_buttons(self, sample_produits):
        """Test que les boutons d'action sont présents"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier les boutons d'action
        assert "Détails" in response.text
        assert "refreshData" in response.text
        assert "showQuickAdd" in response.text
    
    def test_magasin_product_links(self, sample_produits):
        """Test que les liens vers les détails des produits sont corrects"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier les liens vers les détails
        assert "/produit/1234567890" in response.text
        assert "/produit/2345678901" in response.text
        assert "/produit/3456789012" in response.text
    
    def test_magasin_empty_state(self, db):
        """Test de l'état vide (aucun produit)"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier l'affichage de l'état vide
        assert "Aucun produit trouvé" in response.text or "inventaire est vide" in response.text
    
    def test_magasin_javascript_functions(self, sample_produits):
        """Test que les fonctions JavaScript sont présentes"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier la présence des fonctions JavaScript
        assert "function filterProducts" in response.text
        assert "function filterByFournisseur" in response.text
        assert "function refreshData" in response.text
        assert "function showQuickAdd" in response.text
        assert "function clearSearch" in response.text
        assert "function performSearch" in response.text

class TestMagasinCRUD:
    """Tests pour les opérations CRUD liées au magasin"""
    
    def test_get_inventaire_crud(self, sample_produits):
        """Test de la fonction CRUD get_inventaire"""
        from crud import get_inventaire
        
        db = TestingSessionLocal()
        try:
            produits = get_inventaire(db)
            assert len(produits) == 5
            
            # Vérifier que tous les produits sont récupérés
            noms_produits = [p.produits for p in produits]
            assert "Produit Stock Critique" in noms_produits
            assert "Produit Stock Faible" in noms_produits
            assert "Produit Stock Normal" in noms_produits
            assert "Produit Surstock" in noms_produits
            assert "Produit Sans Fournisseur" in noms_produits
        finally:
            db.close()
    
    def test_get_inventaire_by_fournisseur_crud(self, sample_produits):
        """Test de la fonction CRUD get_inventaire_by_fournisseur"""
        from crud import get_inventaire_by_fournisseur
        
        db = TestingSessionLocal()
        try:
            # Test Fournisseur A
            produits_a = get_inventaire_by_fournisseur(db, "Fournisseur A")
            assert len(produits_a) == 2
            noms_a = [p.produits for p in produits_a]
            assert "Produit Stock Critique" in noms_a
            assert "Produit Stock Faible" in noms_a
            
            # Test Fournisseur B
            produits_b = get_inventaire_by_fournisseur(db, "Fournisseur B")
            assert len(produits_b) == 2
            noms_b = [p.produits for p in produits_b]
            assert "Produit Stock Normal" in noms_b
            assert "Produit Surstock" in noms_b
        finally:
            db.close()
    
    def test_get_fournisseurs_actifs_crud(self, sample_produits):
        """Test de la fonction CRUD get_fournisseurs_actifs"""
        from crud import get_fournisseurs_actifs
        
        db = TestingSessionLocal()
        try:
            fournisseurs_actifs = get_fournisseurs_actifs(db)
            
            # Vérifier que les fournisseurs actifs sont récupérés
            noms_fournisseurs = [f['nom_fournisseur'] for f in fournisseurs_actifs]
            assert "Fournisseur A" in noms_fournisseurs
            assert "Fournisseur B" in noms_fournisseurs
            
            # Vérifier la structure des données
            for fournisseur in fournisseurs_actifs:
                assert 'nom_fournisseur' in fournisseur
                assert 'nom' in fournisseur
                assert fournisseur['nom_fournisseur'] == fournisseur['nom']
        finally:
            db.close()
    
    def test_get_inventaire_by_reference_crud(self, sample_produits):
        """Test de la fonction CRUD get_inventaire_by_reference"""
        from crud import get_inventaire_by_reference
        
        db = TestingSessionLocal()
        try:
            # Test avec une référence existante
            produit = get_inventaire_by_reference(db, "1234567890")
            assert produit is not None
            assert produit.produits == "Produit Stock Critique"
            assert produit.reference == "1234567890"
            
            # Test avec une référence inexistante
            produit_inexistant = get_inventaire_by_reference(db, "9999999999")
            assert produit_inexistant is None
        finally:
            db.close()
    
    def test_search_inventaire_crud(self, sample_produits):
        """Test de la fonction CRUD search_inventaire"""
        from crud import search_inventaire
        
        db = TestingSessionLocal()
        try:
            # Recherche par nom de produit
            resultats_nom = search_inventaire(db, "Critique")
            assert len(resultats_nom) == 1
            assert resultats_nom[0].produits == "Produit Stock Critique"
            
            # Recherche par référence
            resultats_ref = search_inventaire(db, "1234567890")
            assert len(resultats_ref) == 1
            assert resultats_ref[0].reference == "1234567890"
            
            # Recherche par fournisseur
            resultats_fournisseur = search_inventaire(db, "Fournisseur A")
            assert len(resultats_fournisseur) == 2
            
            # Recherche par catégorie
            resultats_categorie = search_inventaire(db, "Électronique")
            assert len(resultats_categorie) == 1
            assert resultats_categorie[0].categorie == "Électronique"
        finally:
            db.close()

class TestMagasinStatistics:
    """Tests pour les statistiques du magasin"""
    
    def test_calculate_stock_stats(self, sample_produits):
        """Test de la fonction calculate_stock_stats"""
        from main import calculate_stock_stats, normalize_produit, clean_sqlalchemy_object
        
        db = TestingSessionLocal()
        try:
            from crud import get_inventaire
            produits_raw = get_inventaire(db)
            produits = [normalize_produit(clean_sqlalchemy_object(p)) for p in produits_raw]
            
            stats = calculate_stock_stats(produits)
            
            # Vérifier la structure des statistiques
            assert 'total_produits' in stats
            assert 'stock_critique' in stats
            assert 'stock_faible' in stats
            assert 'stock_normal' in stats
            assert 'surstock' in stats
            assert 'valeur_totale' in stats
            
            # Vérifier les valeurs
            assert stats['total_produits'] == 5
            assert stats['stock_critique'] == 1  # Produit Stock Critique
            assert stats['stock_faible'] == 1    # Produit Stock Faible
            assert stats['stock_normal'] == 2    # Produit Stock Normal + Produit Sans Fournisseur
            assert stats['surstock'] == 1       # Produit Surstock
            
            # Vérifier la valeur totale
            expected_value = (2 * 15.50) + (12 * 25.00) + (30 * 8.75) + (75 * 12.30) + (20 * 5.00)
            assert abs(stats['valeur_totale'] - expected_value) < 0.01
        finally:
            db.close()
    
    def test_get_stock_status(self, sample_produits):
        """Test de la fonction get_stock_status"""
        from main import get_stock_status
        
        # Test stock critique
        produit_critique = {
            'quantite': 5,
            'stock_min': 10,
            'stock_max': 50
        }
        assert get_stock_status(produit_critique) == 'critique'
        
        # Test stock faible
        produit_faible = {
            'quantite': 12,
            'stock_min': 10,
            'stock_max': 50
        }
        assert get_stock_status(produit_faible) == 'faible'
        
        # Test stock normal
        produit_normal = {
            'quantite': 30,
            'stock_min': 10,
            'stock_max': 50
        }
        assert get_stock_status(produit_normal) == 'normal'
        
        # Test surstock
        produit_surstock = {
            'quantite': 75,
            'stock_min': 10,
            'stock_max': 50
        }
        assert get_stock_status(produit_surstock) == 'surstock'

class TestMagasinHelperFunctions:
    """Tests pour les fonctions helper du magasin"""
    
    def test_normalize_produit(self):
        """Test de la fonction normalize_produit"""
        from main import normalize_produit
        
        # Test avec un produit complet
        produit = {
            'produits': 'Test Produit - Description',
            'stock_min': 10,
            'fournisseur': 'Test Fournisseur',
            'emplacement': 'Test Emplacement',
            'site': 'Test Site',
            'lieu': 'Test Lieu'
        }
        
        result = normalize_produit(produit)
        
        assert result['seuil_alerte'] == 10
        assert result['designation'] == 'Test Produit - Description'
        assert result['nom'] == 'Test Produit'
        assert result['fournisseur'] == 'Test Fournisseur'
        assert result['emplacement'] == 'Test Emplacement'
        assert result['site'] == 'Test Site'
        assert result['lieu'] == 'Test Lieu'
    
    def test_normalize_produit_with_missing_fields(self):
        """Test de normalize_produit avec des champs manquants"""
        from main import normalize_produit
        
        # Test avec des champs manquants
        produit = {
            'produits': 'Test Produit Simple'
        }
        
        result = normalize_produit(produit)
        
        assert result['fournisseur'] == 'Non défini'
        assert result['emplacement'] == 'Non défini'
        assert result['site'] == 'Non défini'
        assert result['lieu'] == 'Non défini'
        assert result['designation'] == 'Test Produit Simple'
    
    def test_clean_sqlalchemy_object(self):
        """Test de la fonction clean_sqlalchemy_object"""
        from main import clean_sqlalchemy_object
        from datetime import datetime
        from decimal import Decimal
        
        # Créer un objet simulé avec différents types de données
        class MockObject:
            def __init__(self):
                self.id = 1
                self.name = "Test"
                self.created_at = datetime(2023, 1, 1, 12, 0, 0)
                self.price = Decimal('15.50')
                self._private_attr = "should_be_ignored"
        
        obj = MockObject()
        result = clean_sqlalchemy_object(obj)
        
        assert result['id'] == 1
        assert result['name'] == "Test"
        assert result['created_at'] == "2023-01-01T12:00:00"
        assert result['price'] == 15.50
        assert '_private_attr' not in result

class TestMagasinAPI:
    """Tests pour les endpoints API utilisés par le magasin"""
    
    def test_api_produit_endpoint(self, sample_produits):
        """Test de l'endpoint API /api/produit/{reference}"""
        response = client.get("/api/produit/1234567890")
        assert response.status_code == 200
        
        data = response.json()
        assert data['reference'] == "1234567890"
        assert data['produits'] == "Produit Stock Critique"
        assert data['quantite'] == 2
    
    def test_api_produit_not_found(self, sample_produits):
        """Test de l'endpoint API avec une référence inexistante"""
        response = client.get("/api/produit/9999999999")
        assert response.status_code == 404
        # Vérifier que c'est bien une réponse JSON d'erreur
        if response.headers.get("content-type", "").startswith("application/json"):
            assert "Produit non trouvé" in response.json()['detail']
        else:
            # Si c'est du HTML, vérifier que c'est une page 404
            assert "404" in response.text or "Produit non trouvé" in response.text
    
    def test_api_fournisseurs_actifs(self, sample_produits):
        """Test de l'endpoint API /api/fournisseurs-actifs"""
        response = client.get("/api/fournisseurs-actifs")
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert 'fournisseurs' in data
        
        noms_fournisseurs = [f['nom_fournisseur'] for f in data['fournisseurs']]
        assert "Fournisseur A" in noms_fournisseurs
        assert "Fournisseur B" in noms_fournisseurs

class TestMagasinEdgeCases:
    """Tests pour les cas limites du magasin"""
    
    def test_magasin_with_special_characters(self, db):
        """Test avec des caractères spéciaux dans les noms"""
        produit = Inventaire(
            code="SPEC123456",
            reference="SPEC123456",
            produits="Produit Spécial & Caractères #@!",
            quantite=10,
            stock_min=5,
            stock_max=20,
            fournisseur="Fournisseur Spécial & Co",
            emplacement="Étagère Spéciale #1"
        )
        
        db.add(produit)
        db.commit()
        
        response = client.get("/magasin")
        assert response.status_code == 200
        assert "Produit Spécial &amp; Caractères" in response.text
    
    def test_magasin_with_zero_quantities(self, db):
        """Test avec des quantités nulles"""
        produit = Inventaire(
            code="ZERO123456",
            reference="ZERO123456",
            produits="Produit Quantité Zéro",
            quantite=0,
            stock_min=5,
            stock_max=20,
            fournisseur="Fournisseur Test"
        )
        
        db.add(produit)
        db.commit()
        
        response = client.get("/magasin")
        assert response.status_code == 200
        assert "Produit Quantité Zéro" in response.text
    
    def test_magasin_with_negative_values(self, db):
        """Test avec des valeurs négatives (cas d'erreur)"""
        produit = Inventaire(
            code="NEG123456",
            reference="NEG123456",
            produits="Produit Valeurs Négatives",
            quantite=-5,
            stock_min=5,
            stock_max=20,
            prix_unitaire=-10.00,
            fournisseur="Fournisseur Test"
        )
        
        db.add(produit)
        db.commit()
        
        response = client.get("/magasin")
        assert response.status_code == 200
        # La page doit se charger même avec des valeurs négatives
        assert "Produit Valeurs Négatives" in response.text

class TestMagasinAdditionalTests:
    """Tests supplémentaires pour la page magasin"""
    
    def test_magasin_route_basic_additional(self, sample_produits):
        """Test de base supplémentaire pour la route magasin"""
        # Test que la route magasin existe et fonctionne
        response = client.get("/magasin")
        assert response.status_code == 200
        assert "Magasin" in response.text

    def test_magasin_with_filter_additional(self, sample_produits):
        """Test de la route magasin avec filtre fournisseur (test supplémentaire)"""
        response = client.get("/magasin?fournisseur=TestFournisseur")
        assert response.status_code == 200

    def test_magasin_stats_calculation_detailed(self, sample_produits):
        """Test détaillé du calcul des statistiques de stock"""
        from main import calculate_stock_stats, normalize_produit, clean_sqlalchemy_object
        
        db = TestingSessionLocal()
        try:
            from crud import get_inventaire
            produits_raw = get_inventaire(db)
            produits = [normalize_produit(clean_sqlalchemy_object(p)) for p in produits_raw]
            
            stats = calculate_stock_stats(produits)
            
            # Vérifications détaillées
            assert 'total_produits' in stats
            assert 'stock_critique' in stats
            assert 'stock_faible' in stats
            assert 'stock_normal' in stats
            assert 'surstock' in stats
            assert 'valeur_totale' in stats
            
            # Vérifier que les totaux sont cohérents
            total_categories = (stats['stock_critique'] + stats['stock_faible'] + 
                              stats['stock_normal'] + stats['surstock'])
            assert total_categories == stats['total_produits']
            
        finally:
            db.close()

    def test_get_stock_status_function_extended(self, db):
        """Test étendu de la fonction get_stock_status"""
        from main import get_stock_status
        
        # Test stock critique
        produit_critique = {'quantite': 5, 'stock_min': 10, 'stock_max': 50}
        assert get_stock_status(produit_critique) == 'critique'
        
        # Test stock faible (seuil d'alerte = 10 + (50-10)*0.3 = 22)
        produit_faible = {'quantite': 15, 'stock_min': 10, 'stock_max': 50}
        assert get_stock_status(produit_faible) == 'faible'
        
        # Test stock normal
        produit_normal = {'quantite': 30, 'stock_min': 10, 'stock_max': 50}
        assert get_stock_status(produit_normal) == 'normal'
        
        # Test surstock
        produit_surstock = {'quantite': 75, 'stock_min': 10, 'stock_max': 50}
        assert get_stock_status(produit_surstock) == 'surstock'
        
        # Test cas limites
        produit_limite_min = {'quantite': 10, 'stock_min': 10, 'stock_max': 50}
        assert get_stock_status(produit_limite_min) == 'faible'
        
        produit_limite_max = {'quantite': 50, 'stock_min': 10, 'stock_max': 50}
        assert get_stock_status(produit_limite_max) == 'normal'

    def test_normalize_produit_function_extended(self, db):
        """Test étendu de la fonction normalize_produit"""
        from main import normalize_produit
        
        # Test avec un produit complet
        produit = {
            'produits': 'Vis M6 - Acier inoxydable',
            'stock_min': 20,
            'fournisseur': 'Visserie Pro',
            'emplacement': 'A1-B2',
            'site': 'Atelier Principal',
            'lieu': 'Zone Stockage'
        }
        
        result = normalize_produit(produit)
        
        assert result['seuil_alerte'] == 20
        assert result['designation'] == 'Vis M6 - Acier inoxydable'
        assert result['nom'] == 'Vis M6'
        assert result['fournisseur'] == 'Visserie Pro'
        assert result['emplacement'] == 'A1-B2'
        assert result['site'] == 'Atelier Principal'
        assert result['lieu'] == 'Zone Stockage'
        
        # Test avec des champs manquants
        produit_minimal = {'produits': 'Produit Simple'}
        result_minimal = normalize_produit(produit_minimal)
        
        assert result_minimal['fournisseur'] == 'Non défini'
        assert result_minimal['emplacement'] == 'Non défini'
        assert result_minimal['site'] == 'Non défini'
        assert result_minimal['lieu'] == 'Non défini'
        
        # Test avec produit sans tiret
        produit_sans_tiret = {'produits': 'Produit Sans Tiret'}
        result_sans_tiret = normalize_produit(produit_sans_tiret)
        assert result_sans_tiret['nom'] == 'Produit Sans Tiret'

    def test_clean_sqlalchemy_object_function_extended(self, db):
        """Test étendu de la fonction clean_sqlalchemy_object"""
        from main import clean_sqlalchemy_object
        from datetime import datetime, date
        from decimal import Decimal
        
        # Créer un objet mock avec différents types de données
        class MockSQLAlchemyObject:
            def __init__(self):
                self.id = 1
                self.nom = "Test Produit"
                self.date_creation = datetime(2023, 12, 1, 10, 30, 0)
                self.date_simple = date(2023, 12, 1)
                self.prix = Decimal('15.50')
                self.quantite = 10
                self.valeur_none = None
                self._sa_instance_state = "should_be_ignored"
                self._private_attr = "private"
        
        obj = MockSQLAlchemyObject()
        result = clean_sqlalchemy_object(obj)
        
        # Vérifications
        assert result['id'] == 1
        assert result['nom'] == "Test Produit"
        assert result['date_creation'] == "2023-12-01T10:30:00"
        assert result['date_simple'] == "2023-12-01"
        assert result['prix'] == 15.50
        assert result['quantite'] == 10
        assert result['valeur_none'] is None
        assert '_sa_instance_state' not in result
        assert '_private_attr' not in result

    def test_magasin_empty_inventory_detailed(self, db):
        """Test détaillé de la page magasin avec un inventaire vide"""
        from unittest.mock import patch
        
        with patch('crud.get_inventaire') as mock_get_inventaire, \
             patch('crud.get_fournisseurs_actifs') as mock_get_fournisseurs:
            
            # Configuration des mocks pour retourner des listes vides
            mock_get_inventaire.return_value = []
            mock_get_fournisseurs.return_value = []
            
            response = client.get("/magasin")
            assert response.status_code == 200
            # Vérifier que la page gère correctement l'absence de produits
            assert "Magasin" in response.text

    def test_magasin_performance_large_inventory(self, db):
        """Test de performance de la page magasin avec un grand inventaire"""
        from unittest.mock import Mock, patch
        import time
        
        with patch('crud.get_inventaire') as mock_get_inventaire, \
             patch('crud.get_fournisseurs_actifs') as mock_get_fournisseurs:
            
            # Créer une liste de 500 produits mock
            mock_produits = []
            for i in range(500):
                mock_produit = Mock()
                mock_produit.__dict__ = {
                    'id': i,
                    'produits': f'Produit Performance {i}',
                    'quantite': i % 50,
                    'stock_min': 10,
                    'stock_max': 40,
                    'prix_unitaire': 10.0 + (i % 20),
                    'fournisseur': f'Fournisseur {i % 10}',
                    'site': f'Site {i % 3}',
                    'lieu': f'Lieu {i % 5}',
                    'emplacement': f'Emplacement {i % 20}'
                }
                mock_produits.append(mock_produit)
            
            mock_get_inventaire.return_value = mock_produits
            mock_get_fournisseurs.return_value = []
            
            # Mesurer le temps de réponse
            start_time = time.time()
            response = client.get("/magasin")
            end_time = time.time()
            
            assert response.status_code == 200
            # La page devrait se charger en moins de 5 secondes même avec 500 produits
            assert (end_time - start_time) < 5.0
            assert "Magasin" in response.text

    def test_magasin_api_endpoints_integration(self, sample_produits):
        """Test d'intégration des endpoints API utilisés par la page magasin"""
        # Test endpoint produit
        response = client.get("/api/produit/1234567890")
        assert response.status_code == 200
        
        data = response.json()
        assert data['reference'] == "1234567890"
        assert data['produits'] == "Produit Stock Critique"
        
        # Test endpoint fournisseurs actifs
        response = client.get("/api/fournisseurs-actifs")
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert 'fournisseurs' in data

    def test_magasin_error_handling_detailed(self, db):
        """Test détaillé de la gestion d'erreurs dans la page magasin"""
        from unittest.mock import patch
        
        with patch('crud.get_inventaire') as mock_get_inventaire, \
             patch('crud.get_fournisseurs_actifs') as mock_get_fournisseurs:
            # Simuler une erreur de base de données
            mock_get_inventaire.side_effect = Exception("Erreur de connexion à la base de données")
            mock_get_fournisseurs.return_value = []
            
            # Le test doit capturer l'exception car elle est propagée
            try:
                response = client.get("/magasin")
                # Si la page gère l'erreur gracieusement
                assert response.status_code in [200, 500]
            except Exception as e:
                # Si l'exception est propagée (comportement attendu)
                assert "Erreur de connexion à la base de données" in str(e)

    def test_magasin_filter_edge_cases(self, sample_produits):
        """Test des cas limites pour le filtrage de la page magasin"""
        # Test avec un fournisseur inexistant
        response = client.get("/magasin?fournisseur=FournisseurInexistant")
        assert response.status_code == 200
        
        # Test avec caractères spéciaux dans le filtre
        response = client.get("/magasin?fournisseur=Fournisseur%20%26%20Co")
        assert response.status_code == 200
        
        # Test avec filtre vide
        response = client.get("/magasin?fournisseur=")
        assert response.status_code == 200

    def test_magasin_data_consistency(self, sample_produits):
        """Test de cohérence des données affichées dans la page magasin"""
        response = client.get("/magasin")
        assert response.status_code == 200
        
        # Vérifier que les données essentielles sont présentes
        assert "Stock critique" in response.text or "stock-critique" in response.text
        assert "Fournisseur A" in response.text
        assert "1234567890" in response.text  # Référence du produit test

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 