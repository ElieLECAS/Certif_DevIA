from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# =====================================================
# SCHÉMAS POUR INVENTAIRE (PRODUITS)
# =====================================================

class InventaireBase(BaseModel):
    code: str
    reference_fournisseur: Optional[str] = None
    produits: str
    unite_stockage: Optional[str] = None
    unite_commande: Optional[str] = None
    stock_min: int = 0
    stock_max: int = 100
    site: Optional[str] = None
    lieu: Optional[str] = None
    emplacement: Optional[str] = None
    fournisseur: Optional[str] = None
    prix_unitaire: Decimal = 0
    categorie: Optional[str] = None
    secteur: Optional[str] = None
    reference: str  # Référence QR unique
    quantite: int = 0
    date_entree: Optional[date] = None

class InventaireCreate(InventaireBase):
    pass

class InventaireUpdate(BaseModel):
    code: Optional[str] = None
    reference_fournisseur: Optional[str] = None
    produits: Optional[str] = None
    unite_stockage: Optional[str] = None
    unite_commande: Optional[str] = None
    stock_min: Optional[int] = None
    stock_max: Optional[int] = None
    site: Optional[str] = None
    lieu: Optional[str] = None
    emplacement: Optional[str] = None
    fournisseur: Optional[str] = None
    prix_unitaire: Optional[Decimal] = None
    categorie: Optional[str] = None
    secteur: Optional[str] = None
    quantite: Optional[int] = None
    date_entree: Optional[date] = None

class InventaireResponse(InventaireBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime

# =====================================================
# SCHÉMAS POUR FOURNISSEURS
# =====================================================

class FournisseurBase(BaseModel):
    id_fournisseur: str
    nom_fournisseur: str
    adresse: Optional[str] = None
    
    # Contact 1
    contact1_nom: Optional[str] = None
    contact1_prenom: Optional[str] = None
    contact1_fonction: Optional[str] = None
    contact1_tel_fixe: Optional[str] = None
    contact1_tel_mobile: Optional[str] = None
    contact1_email: Optional[str] = None
    
    # Contact 2
    contact2_nom: Optional[str] = None
    contact2_prenom: Optional[str] = None
    contact2_fonction: Optional[str] = None
    contact2_tel_fixe: Optional[str] = None
    contact2_tel_mobile: Optional[str] = None
    contact2_email: Optional[str] = None
    
    statut: str = 'Actif'

class FournisseurCreate(FournisseurBase):
    pass

class FournisseurUpdate(BaseModel):
    nom_fournisseur: Optional[str] = None
    adresse: Optional[str] = None
    
    # Contact 1
    contact1_nom: Optional[str] = None
    contact1_prenom: Optional[str] = None
    contact1_fonction: Optional[str] = None
    contact1_tel_fixe: Optional[str] = None
    contact1_tel_mobile: Optional[str] = None
    contact1_email: Optional[str] = None
    
    # Contact 2
    contact2_nom: Optional[str] = None
    contact2_prenom: Optional[str] = None
    contact2_fonction: Optional[str] = None
    contact2_tel_fixe: Optional[str] = None
    contact2_tel_mobile: Optional[str] = None
    contact2_email: Optional[str] = None
    
    statut: Optional[str] = None

class FournisseurResponse(FournisseurBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: date
    nb_produits: int
    valeur_stock_total: Decimal
    created_at: datetime
    updated_at: datetime

# =====================================================
# SCHÉMAS POUR LA HIÉRARCHIE SITE > LIEU > EMPLACEMENT
# =====================================================

# SITES
class SiteBase(BaseModel):
    code_site: str
    nom_site: str
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    pays: str = 'France'
    responsable: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    statut: str = 'Actif'

class SiteCreate(SiteBase):
    pass

class SiteUpdate(BaseModel):
    nom_site: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    pays: Optional[str] = None
    responsable: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    statut: Optional[str] = None

class SiteResponse(SiteBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: date
    created_at: datetime
    updated_at: datetime

# LIEUX
class LieuBase(BaseModel):
    code_lieu: str
    nom_lieu: str
    site_id: int
    type_lieu: Optional[str] = None
    niveau: Optional[str] = None
    surface: Optional[Decimal] = None
    responsable: Optional[str] = None
    statut: str = 'Actif'

class LieuCreate(LieuBase):
    pass

class LieuUpdate(BaseModel):
    nom_lieu: Optional[str] = None
    site_id: Optional[int] = None
    type_lieu: Optional[str] = None
    niveau: Optional[str] = None
    surface: Optional[Decimal] = None
    responsable: Optional[str] = None
    statut: Optional[str] = None

class LieuResponse(LieuBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: date
    created_at: datetime
    updated_at: datetime

# EMPLACEMENTS
class EmplacementBase(BaseModel):
    code_emplacement: str
    nom_emplacement: str
    lieu_id: int
    type_emplacement: Optional[str] = None
    position: Optional[str] = None
    capacite_max: int = 100
    temperature_min: Optional[Decimal] = None
    temperature_max: Optional[Decimal] = None
    humidite_max: Optional[Decimal] = None
    conditions_speciales: Optional[str] = None
    responsable: Optional[str] = None
    statut: str = 'Actif'

class EmplacementCreate(BaseModel):
    nom_emplacement: str
    lieu_id: int
    type_emplacement: Optional[str] = None
    position: Optional[str] = None
    capacite_max: int = 100
    temperature_min: Optional[Decimal] = None
    temperature_max: Optional[Decimal] = None
    humidite_max: Optional[Decimal] = None
    conditions_speciales: Optional[str] = None
    responsable: Optional[str] = None
    statut: str = 'Actif'

class EmplacementUpdate(BaseModel):
    nom_emplacement: Optional[str] = None
    lieu_id: Optional[int] = None
    type_emplacement: Optional[str] = None
    position: Optional[str] = None
    capacite_max: Optional[int] = None
    temperature_min: Optional[Decimal] = None
    temperature_max: Optional[Decimal] = None
    humidite_max: Optional[Decimal] = None
    conditions_speciales: Optional[str] = None
    responsable: Optional[str] = None
    statut: Optional[str] = None

class EmplacementResponse(EmplacementBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: date
    nb_produits: int = 0
    taux_occupation: Decimal = Decimal('0.00')
    created_at: datetime
    updated_at: datetime

# SCHÉMAS AVEC RELATIONS POUR L'AFFICHAGE HIÉRARCHIQUE
class EmplacementWithHierarchy(EmplacementResponse):
    lieu_nom: Optional[str] = None
    site_nom: Optional[str] = None
    chemin_complet: Optional[str] = None  # Site > Lieu > Emplacement

class LieuWithSite(LieuResponse):
    site_nom: Optional[str] = None
    nb_emplacements: Optional[int] = None

class SiteWithStats(SiteResponse):
    nb_lieux: Optional[int] = None
    nb_emplacements: Optional[int] = None

# =====================================================
# SCHÉMAS POUR DEMANDES
# =====================================================

class DemandeBase(BaseModel):
    id_demande: str
    date_demande: datetime
    demandeur: str
    produits_demandes: str  # JSON stocké comme texte
    motif: Optional[str] = None
    statut: str = 'En attente'

class DemandeCreate(DemandeBase):
    pass

class DemandeUpdate(BaseModel):
    statut: Optional[str] = None
    date_traitement: Optional[datetime] = None
    traite_par: Optional[str] = None
    commentaires: Optional[str] = None

class DemandeResponse(DemandeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_traitement: Optional[datetime] = None
    traite_par: Optional[str] = None
    commentaires: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# =====================================================
# SCHÉMAS POUR HISTORIQUE
# =====================================================

class HistoriqueBase(BaseModel):
    date_mouvement: datetime
    reference: Optional[str] = None
    produit: str
    nature: str  # Entrée, Sortie, Ajustement
    quantite_mouvement: int
    quantite_avant: int
    quantite_apres: int

class HistoriqueCreate(HistoriqueBase):
    pass

class HistoriqueResponse(HistoriqueBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime

# =====================================================
# SCHÉMAS POUR TABLES D'ATELIER
# =====================================================

class TableAtelierBase(BaseModel):
    id_table: str
    nom_table: str
    type_atelier: str
    emplacement: str
    responsable: str
    statut: str = 'Actif'

class TableAtelierCreate(TableAtelierBase):
    pass

class TableAtelierUpdate(BaseModel):
    nom_table: Optional[str] = None
    type_atelier: Optional[str] = None
    emplacement: Optional[str] = None
    responsable: Optional[str] = None
    statut: Optional[str] = None

class TableAtelierResponse(TableAtelierBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: date
    created_at: datetime
    updated_at: datetime

# =====================================================
# SCHÉMAS POUR LISTES D'INVENTAIRE
# =====================================================

class ListeInventaireBase(BaseModel):
    id_liste: str
    nom_liste: str
    date_creation: datetime
    statut: str = 'En préparation'
    cree_par: str = 'Utilisateur'

class ListeInventaireCreate(ListeInventaireBase):
    pass

class ListeInventaireUpdate(BaseModel):
    nom_liste: Optional[str] = None
    statut: Optional[str] = None

class ListeInventaireResponse(ListeInventaireBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nb_produits: int
    created_at: datetime
    updated_at: datetime

# =====================================================
# SCHÉMAS POUR PRODUITS DES LISTES D'INVENTAIRE
# =====================================================

class ProduitListeInventaireBase(BaseModel):
    id_liste: str
    reference_produit: str
    nom_produit: str
    emplacement: Optional[str] = None
    quantite_theorique: int
    quantite_comptee: Optional[int] = None
    categorie: Optional[str] = None
    fournisseur: Optional[str] = None
    date_ajout: datetime

class ProduitListeInventaireCreate(ProduitListeInventaireBase):
    pass

class ProduitListeInventaireUpdate(BaseModel):
    quantite_comptee: Optional[int] = None

class ProduitListeInventaireResponse(ProduitListeInventaireBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime

# =====================================================
# SCHÉMAS POUR LES MOUVEMENTS DE STOCK
# =====================================================

class MouvementStockCreate(BaseModel):
    reference_produit: str
    nature: str  # 'Entrée', 'Sortie', 'Ajustement'
    quantite: int
    motif: Optional[str] = None

class MouvementStockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    message: str
    nouveau_stock: Optional[int] = None 