from pydantic import BaseModel, ConfigDict, validator, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
import re

# =====================================================
# SCHÉMAS POUR INVENTAIRE (PRODUITS)
# =====================================================

class InventaireBase(BaseModel):
    code: str
    reference_fournisseur: Optional[str] = None
    produits: str
    stock_min: int = 0
    stock_max: int = 100
    prix_unitaire: Decimal = 0
    categorie: Optional[str] = None
    secteur: Optional[str] = None
    reference: str  # Référence QR unique
    quantite: int = 0
    date_entree: Optional[date] = None

class InventaireCreate(InventaireBase):
    # Champs temporaires pour la création (convertis en relations)
    site: Optional[str] = None
    lieu: Optional[str] = None
    emplacement: Optional[str] = None
    fournisseur: Optional[str] = None
    unite_stockage: Optional[str] = None
    unite_commande: Optional[str] = None

class InventaireUpdate(BaseModel):
    code: Optional[str] = None
    reference_fournisseur: Optional[str] = None
    produits: Optional[str] = None
    stock_min: Optional[int] = None
    stock_max: Optional[int] = None
    prix_unitaire: Optional[Decimal] = None
    categorie: Optional[str] = None
    secteur: Optional[str] = None
    quantite: Optional[int] = None
    date_entree: Optional[date] = None
    # Champs temporaires pour la mise à jour (convertis en relations)
    site: Optional[str] = None
    lieu: Optional[str] = None
    emplacement: Optional[str] = None
    fournisseur: Optional[str] = None
    unite_stockage: Optional[str] = None
    unite_commande: Optional[str] = None

class InventaireResponse(InventaireBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    site_id: Optional[int] = None
    lieu_id: Optional[int] = None
    emplacement_id: Optional[int] = None
    fournisseur_id: Optional[int] = None
    unite_stockage_id: Optional[int] = None
    unite_commande_id: Optional[int] = None
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
# SCHÉMAS POUR UNITÉS DE STOCKAGE
# =====================================================

class UniteStockageBase(BaseModel):
    code_unite: str
    nom_unite: str
    symbole: str
    description: Optional[str] = None
    type_unite: Optional[str] = None
    facteur_conversion: Decimal = Decimal('1.0000')
    unite_base: Optional[str] = None
    statut: str = 'Actif'

class UniteStockageCreate(UniteStockageBase):
    pass

class UniteStockageUpdate(BaseModel):
    nom_unite: Optional[str] = None
    symbole: Optional[str] = None
    description: Optional[str] = None
    type_unite: Optional[str] = None
    facteur_conversion: Optional[Decimal] = None
    unite_base: Optional[str] = None
    statut: Optional[str] = None

class UniteStockageResponse(UniteStockageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: date
    created_at: datetime
    updated_at: datetime

# =====================================================
# SCHÉMAS POUR UNITÉS DE COMMANDE
# =====================================================

class UniteCommandeBase(BaseModel):
    code_unite: str
    nom_unite: str
    symbole: str
    description: Optional[str] = None
    type_unite: Optional[str] = None
    quantite_unitaire: int = 1
    facteur_conversion: Decimal = Decimal('1.0000')
    statut: str = 'Actif'

class UniteCommandeCreate(UniteCommandeBase):
    pass

class UniteCommandeUpdate(BaseModel):
    nom_unite: Optional[str] = None
    symbole: Optional[str] = None
    description: Optional[str] = None
    type_unite: Optional[str] = None
    quantite_unitaire: Optional[int] = None
    facteur_conversion: Optional[Decimal] = None
    statut: Optional[str] = None

class UniteCommandeResponse(UniteCommandeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_creation: date
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
    id_demande_base: str
    demandeur: str
    table_atelier: str
    reference_produit: str
    quantite_demandee: int
    statut: str = 'En attente'
    date_demande: date
    commentaires: Optional[str] = None
    
    # Nouveaux champs pour traçabilité améliorée
    id_table: Optional[str] = None
    designation_produit: Optional[str] = None
    unite: Optional[str] = None
    fournisseur: Optional[str] = None
    emplacement: Optional[str] = None

class DemandeCreate(DemandeBase):
    pass

class DemandeUpdate(BaseModel):
    statut: Optional[str] = None
    date_traitement: Optional[datetime] = None
    traite_par: Optional[str] = None
    commentaires: Optional[str] = None
    quantite_demandee: Optional[int] = None

class DemandeResponse(DemandeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date_traitement: Optional[datetime] = None
    traite_par: Optional[str] = None
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
    motif: Optional[str] = None

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
    id_table: Optional[str] = Field(None, min_length=1, max_length=20, description="ID unique de la table")
    nom_table: str = Field(..., min_length=1, max_length=200, description="Nom de la table")
    type_atelier: str = Field(..., min_length=1, max_length=100, description="Type d'atelier")
    emplacement: Optional[str] = Field(None, max_length=200, description="Emplacement de la table")
    responsable: Optional[str] = Field(None, max_length=200, description="Responsable de la table")
    statut: str = Field(default='Actif', max_length=20, description="Statut de la table")
    
    @validator('nom_table')
    def validate_nom_table(cls, v):
        if not v or not v.strip():
            raise ValueError('Le nom ne peut pas être vide ou ne contenir que des espaces')
        return v.strip()
    
    @validator('statut')
    def validate_statut(cls, v):
        valid_statuts = ['Actif', 'Inactif', 'Maintenance', 'Hors service']
        if v not in valid_statuts:
            raise ValueError(f"Le statut doit être l'un des suivants : {', '.join(valid_statuts)}")
        return v
    
    @validator('type_atelier')
    def validate_type_atelier(cls, v):
        valid_types = ['ALU', 'PVC', 'Hybride']
        if v not in valid_types:
            raise ValueError(f"Le type d'atelier doit être l'un des suivants : {', '.join(valid_types)}")
        return v

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

# =====================================================
# SCHÉMAS POUR L'AUTHENTIFICATION
# =====================================================

class UtilisateurBase(BaseModel):
    username: str
    email: str
    nom_complet: str
    telephone: Optional[str] = None  # Nouveau champ téléphone
    role: str = 'utilisateur'
    statut: str = 'actif'

class UtilisateurCreate(UtilisateurBase):
    password: str

class UtilisateurUpdate(BaseModel):
    email: Optional[str] = None
    nom_complet: Optional[str] = None
    telephone: Optional[str] = None  # Nouveau champ téléphone
    role: Optional[str] = None
    statut: Optional[str] = None

class UtilisateurResponse(UtilisateurBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    derniere_connexion: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class UtilisateurLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UtilisateurResponse

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None 