"""Initial tables creation

Revision ID: 000
Revises: 
Create Date: 2024-01-01 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create sites table
    op.create_table('sites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code_site', sa.String(length=20), nullable=False),
        sa.Column('nom_site', sa.String(length=200), nullable=False),
        sa.Column('adresse', sa.Text(), nullable=True),
        sa.Column('ville', sa.String(length=100), nullable=True),
        sa.Column('code_postal', sa.String(length=10), nullable=True),
        sa.Column('pays', sa.String(length=100), nullable=True),
        sa.Column('responsable', sa.String(length=200), nullable=True),
        sa.Column('telephone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('date_creation', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sites_id'), 'sites', ['id'], unique=False)
    op.create_index(op.f('ix_sites_code_site'), 'sites', ['code_site'], unique=True)
    op.create_index(op.f('ix_sites_nom_site'), 'sites', ['nom_site'], unique=False)

    # Create lieux table
    op.create_table('lieux',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code_lieu', sa.String(length=20), nullable=False),
        sa.Column('nom_lieu', sa.String(length=200), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('type_lieu', sa.String(length=100), nullable=True),
        sa.Column('niveau', sa.String(length=50), nullable=True),
        sa.Column('surface', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('responsable', sa.String(length=200), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('date_creation', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lieux_id'), 'lieux', ['id'], unique=False)
    op.create_index(op.f('ix_lieux_code_lieu'), 'lieux', ['code_lieu'], unique=True)
    op.create_index(op.f('ix_lieux_nom_lieu'), 'lieux', ['nom_lieu'], unique=False)

    # Create emplacements table
    op.create_table('emplacements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code_emplacement', sa.String(length=20), nullable=False),
        sa.Column('nom_emplacement', sa.String(length=200), nullable=False),
        sa.Column('lieu_id', sa.Integer(), nullable=False),
        sa.Column('type_emplacement', sa.String(length=100), nullable=True),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('capacite_max', sa.Integer(), nullable=True),
        sa.Column('temperature_min', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('temperature_max', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('humidite_max', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('conditions_speciales', sa.Text(), nullable=True),
        sa.Column('responsable', sa.String(length=200), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('date_creation', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('nb_produits', sa.Integer(), nullable=True),
        sa.Column('taux_occupation', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lieu_id'], ['lieux.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emplacements_id'), 'emplacements', ['id'], unique=False)
    op.create_index(op.f('ix_emplacements_code_emplacement'), 'emplacements', ['code_emplacement'], unique=True)
    op.create_index(op.f('ix_emplacements_nom_emplacement'), 'emplacements', ['nom_emplacement'], unique=False)

    # Create fournisseurs table
    op.create_table('fournisseurs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_fournisseur', sa.String(length=20), nullable=False),
        sa.Column('nom_fournisseur', sa.String(length=200), nullable=False),
        sa.Column('adresse', sa.Text(), nullable=True),
        sa.Column('contact1_nom', sa.String(length=100), nullable=True),
        sa.Column('contact1_prenom', sa.String(length=100), nullable=True),
        sa.Column('contact1_fonction', sa.String(length=100), nullable=True),
        sa.Column('contact1_tel_fixe', sa.String(length=20), nullable=True),
        sa.Column('contact1_tel_mobile', sa.String(length=20), nullable=True),
        sa.Column('contact1_email', sa.String(length=200), nullable=True),
        sa.Column('contact2_nom', sa.String(length=100), nullable=True),
        sa.Column('contact2_prenom', sa.String(length=100), nullable=True),
        sa.Column('contact2_fonction', sa.String(length=100), nullable=True),
        sa.Column('contact2_tel_fixe', sa.String(length=20), nullable=True),
        sa.Column('contact2_tel_mobile', sa.String(length=20), nullable=True),
        sa.Column('contact2_email', sa.String(length=200), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('date_creation', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('nb_produits', sa.Integer(), nullable=True),
        sa.Column('valeur_stock_total', sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fournisseurs_id'), 'fournisseurs', ['id'], unique=False)
    op.create_index(op.f('ix_fournisseurs_id_fournisseur'), 'fournisseurs', ['id_fournisseur'], unique=True)
    op.create_index(op.f('ix_fournisseurs_nom_fournisseur'), 'fournisseurs', ['nom_fournisseur'], unique=False)

    # Create inventaire table (WITHOUT unite foreign keys for now)
    op.create_table('inventaire',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('reference_fournisseur', sa.String(length=100), nullable=True),
        sa.Column('produits', sa.String(length=500), nullable=False),
        sa.Column('stock_min', sa.Integer(), nullable=True),
        sa.Column('stock_max', sa.Integer(), nullable=True),
        sa.Column('site_id', sa.Integer(), nullable=True),
        sa.Column('lieu_id', sa.Integer(), nullable=True),
        sa.Column('emplacement_id', sa.Integer(), nullable=True),
        sa.Column('fournisseur_id', sa.Integer(), nullable=True),
        sa.Column('prix_unitaire', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('categorie', sa.String(length=100), nullable=True),
        sa.Column('secteur', sa.String(length=100), nullable=True),
        sa.Column('reference', sa.String(length=20), nullable=False),
        sa.Column('quantite', sa.Integer(), nullable=True),
        sa.Column('date_entree', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        # Old text columns for unite (will be replaced by foreign keys in 001 migration)
        sa.Column('unite_stockage', sa.String(length=20), nullable=True),
        sa.Column('unite_commande', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lieu_id'], ['lieux.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['emplacement_id'], ['emplacements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['fournisseur_id'], ['fournisseurs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventaire_id'), 'inventaire', ['id'], unique=False)
    op.create_index(op.f('ix_inventaire_reference'), 'inventaire', ['reference'], unique=True)
    op.create_index(op.f('ix_inventaire_site_id'), 'inventaire', ['site_id'], unique=False)
    op.create_index(op.f('ix_inventaire_lieu_id'), 'inventaire', ['lieu_id'], unique=False)
    op.create_index(op.f('ix_inventaire_emplacement_id'), 'inventaire', ['emplacement_id'], unique=False)
    op.create_index(op.f('ix_inventaire_fournisseur_id'), 'inventaire', ['fournisseur_id'], unique=False)

    # Create demandes table
    op.create_table('demandes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_demande', sa.String(length=50), nullable=False),
        sa.Column('date_demande', sa.TIMESTAMP(), nullable=False),
        sa.Column('demandeur', sa.String(length=200), nullable=False),
        sa.Column('motif', sa.Text(), nullable=True),
        sa.Column('statut', sa.String(length=50), nullable=True),
        sa.Column('date_traitement', sa.TIMESTAMP(), nullable=True),
        sa.Column('traite_par', sa.String(length=200), nullable=True),
        sa.Column('commentaires', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_demandes_id'), 'demandes', ['id'], unique=False)
    op.create_index(op.f('ix_demandes_id_demande'), 'demandes', ['id_demande'], unique=True)
    op.create_index(op.f('ix_demandes_date_demande'), 'demandes', ['date_demande'], unique=False)
    op.create_index(op.f('ix_demandes_demandeur'), 'demandes', ['demandeur'], unique=False)
    op.create_index(op.f('ix_demandes_statut'), 'demandes', ['statut'], unique=False)

    # Create historique table
    op.create_table('historique',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_mouvement', sa.TIMESTAMP(), nullable=False),
        sa.Column('reference', sa.String(length=20), nullable=True),
        sa.Column('produit', sa.String(length=500), nullable=False),
        sa.Column('nature', sa.String(length=50), nullable=False),
        sa.Column('quantite_mouvement', sa.Integer(), nullable=False),
        sa.Column('quantite_avant', sa.Integer(), nullable=False),
        sa.Column('quantite_apres', sa.Integer(), nullable=False),
        sa.Column('motif', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_historique_id'), 'historique', ['id'], unique=False)
    op.create_index(op.f('ix_historique_date_mouvement'), 'historique', ['date_mouvement'], unique=False)
    op.create_index(op.f('ix_historique_reference'), 'historique', ['reference'], unique=False)
    op.create_index(op.f('ix_historique_nature'), 'historique', ['nature'], unique=False)

    # Create tables_atelier table
    op.create_table('tables_atelier',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_table', sa.String(length=20), nullable=False),
        sa.Column('nom_table', sa.String(length=200), nullable=False),
        sa.Column('type_atelier', sa.String(length=100), nullable=False),
        sa.Column('emplacement', sa.String(length=200), nullable=True),
        sa.Column('responsable', sa.String(length=200), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('date_creation', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tables_atelier_id'), 'tables_atelier', ['id'], unique=False)
    op.create_index(op.f('ix_tables_atelier_id_table'), 'tables_atelier', ['id_table'], unique=True)
    op.create_index(op.f('ix_tables_atelier_type_atelier'), 'tables_atelier', ['type_atelier'], unique=False)
    op.create_index(op.f('ix_tables_atelier_responsable'), 'tables_atelier', ['responsable'], unique=False)

    # Create listes_inventaire table
    op.create_table('listes_inventaire',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_liste', sa.String(length=20), nullable=False),
        sa.Column('nom_liste', sa.String(length=300), nullable=False),
        sa.Column('date_creation', sa.TIMESTAMP(), nullable=False),
        sa.Column('statut', sa.String(length=50), nullable=True),
        sa.Column('nb_produits', sa.Integer(), nullable=True),
        sa.Column('cree_par', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_listes_inventaire_id'), 'listes_inventaire', ['id'], unique=False)
    op.create_index(op.f('ix_listes_inventaire_id_liste'), 'listes_inventaire', ['id_liste'], unique=True)
    op.create_index(op.f('ix_listes_inventaire_statut'), 'listes_inventaire', ['statut'], unique=False)

    # Create produits_listes_inventaire table
    op.create_table('produits_listes_inventaire',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_liste', sa.String(length=20), nullable=False),
        sa.Column('reference_produit', sa.String(length=20), nullable=False),
        sa.Column('nom_produit', sa.String(length=500), nullable=False),
        sa.Column('emplacement', sa.String(length=100), nullable=True),
        sa.Column('quantite_theorique', sa.Integer(), nullable=False),
        sa.Column('quantite_comptee', sa.Integer(), nullable=True),
        sa.Column('categorie', sa.String(length=100), nullable=True),
        sa.Column('fournisseur', sa.String(length=200), nullable=True),
        sa.Column('date_ajout', sa.TIMESTAMP(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['id_liste'], ['listes_inventaire.id_liste'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_produits_listes_inventaire_id'), 'produits_listes_inventaire', ['id'], unique=False)
    op.create_index(op.f('ix_produits_listes_inventaire_reference_produit'), 'produits_listes_inventaire', ['reference_produit'], unique=False)

    # Create utilisateurs table
    op.create_table('utilisateurs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('nom_complet', sa.String(length=200), nullable=False),
        sa.Column('telephone', sa.String(length=20), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('derniere_connexion', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_utilisateurs_id'), 'utilisateurs', ['id'], unique=False)
    op.create_index(op.f('ix_utilisateurs_username'), 'utilisateurs', ['username'], unique=True)
    op.create_index(op.f('ix_utilisateurs_email'), 'utilisateurs', ['email'], unique=True)


def downgrade():
    # Drop all tables in reverse order
    op.drop_index(op.f('ix_utilisateurs_email'), table_name='utilisateurs')
    op.drop_index(op.f('ix_utilisateurs_username'), table_name='utilisateurs')
    op.drop_index(op.f('ix_utilisateurs_id'), table_name='utilisateurs')
    op.drop_table('utilisateurs')
    
    op.drop_index(op.f('ix_produits_listes_inventaire_reference_produit'), table_name='produits_listes_inventaire')
    op.drop_index(op.f('ix_produits_listes_inventaire_id'), table_name='produits_listes_inventaire')
    op.drop_table('produits_listes_inventaire')
    
    op.drop_index(op.f('ix_listes_inventaire_statut'), table_name='listes_inventaire')
    op.drop_index(op.f('ix_listes_inventaire_id_liste'), table_name='listes_inventaire')
    op.drop_index(op.f('ix_listes_inventaire_id'), table_name='listes_inventaire')
    op.drop_table('listes_inventaire')
    
    op.drop_index(op.f('ix_tables_atelier_responsable'), table_name='tables_atelier')
    op.drop_index(op.f('ix_tables_atelier_type_atelier'), table_name='tables_atelier')
    op.drop_index(op.f('ix_tables_atelier_id_table'), table_name='tables_atelier')
    op.drop_index(op.f('ix_tables_atelier_id'), table_name='tables_atelier')
    op.drop_table('tables_atelier')
    
    op.drop_index(op.f('ix_historique_nature'), table_name='historique')
    op.drop_index(op.f('ix_historique_reference'), table_name='historique')
    op.drop_index(op.f('ix_historique_date_mouvement'), table_name='historique')
    op.drop_index(op.f('ix_historique_id'), table_name='historique')
    op.drop_table('historique')
    
    op.drop_index(op.f('ix_demandes_statut'), table_name='demandes')
    op.drop_index(op.f('ix_demandes_demandeur'), table_name='demandes')
    op.drop_index(op.f('ix_demandes_date_demande'), table_name='demandes')
    op.drop_index(op.f('ix_demandes_id_demande'), table_name='demandes')
    op.drop_index(op.f('ix_demandes_id'), table_name='demandes')
    op.drop_table('demandes')
    
    op.drop_index(op.f('ix_inventaire_fournisseur_id'), table_name='inventaire')
    op.drop_index(op.f('ix_inventaire_emplacement_id'), table_name='inventaire')
    op.drop_index(op.f('ix_inventaire_lieu_id'), table_name='inventaire')
    op.drop_index(op.f('ix_inventaire_site_id'), table_name='inventaire')
    op.drop_index(op.f('ix_inventaire_reference'), table_name='inventaire')
    op.drop_index(op.f('ix_inventaire_id'), table_name='inventaire')
    op.drop_table('inventaire')
    
    op.drop_index(op.f('ix_fournisseurs_nom_fournisseur'), table_name='fournisseurs')
    op.drop_index(op.f('ix_fournisseurs_id_fournisseur'), table_name='fournisseurs')
    op.drop_index(op.f('ix_fournisseurs_id'), table_name='fournisseurs')
    op.drop_table('fournisseurs')
    
    op.drop_index(op.f('ix_emplacements_nom_emplacement'), table_name='emplacements')
    op.drop_index(op.f('ix_emplacements_code_emplacement'), table_name='emplacements')
    op.drop_index(op.f('ix_emplacements_id'), table_name='emplacements')
    op.drop_table('emplacements')
    
    op.drop_index(op.f('ix_lieux_nom_lieu'), table_name='lieux')
    op.drop_index(op.f('ix_lieux_code_lieu'), table_name='lieux')
    op.drop_index(op.f('ix_lieux_id'), table_name='lieux')
    op.drop_table('lieux')
    
    op.drop_index(op.f('ix_sites_nom_site'), table_name='sites')
    op.drop_index(op.f('ix_sites_code_site'), table_name='sites')
    op.drop_index(op.f('ix_sites_id'), table_name='sites')
    op.drop_table('sites') 