"""Add unite_stockage and unite_commande tables

Revision ID: 001
Revises: 000
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = '000'  # Dépend de la migration 000
branch_labels = None
depends_on = None


def upgrade():
    # Create unite_stockage table
    op.create_table('unites_stockage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code_unite', sa.String(length=20), nullable=False),
        sa.Column('nom_unite', sa.String(length=100), nullable=False),
        sa.Column('symbole', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type_unite', sa.String(length=50), nullable=True),
        sa.Column('facteur_conversion', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('unite_base', sa.String(length=20), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('date_creation', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unites_stockage_id'), 'unites_stockage', ['id'], unique=False)
    op.create_index(op.f('ix_unites_stockage_code_unite'), 'unites_stockage', ['code_unite'], unique=True)
    op.create_index(op.f('ix_unites_stockage_nom_unite'), 'unites_stockage', ['nom_unite'], unique=False)

    # Create unite_commande table
    op.create_table('unites_commande',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code_unite', sa.String(length=20), nullable=False),
        sa.Column('nom_unite', sa.String(length=100), nullable=False),
        sa.Column('symbole', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type_unite', sa.String(length=50), nullable=True),
        sa.Column('quantite_unitaire', sa.Integer(), nullable=True),
        sa.Column('facteur_conversion', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('date_creation', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unites_commande_id'), 'unites_commande', ['id'], unique=False)
    op.create_index(op.f('ix_unites_commande_code_unite'), 'unites_commande', ['code_unite'], unique=True)
    op.create_index(op.f('ix_unites_commande_nom_unite'), 'unites_commande', ['nom_unite'], unique=False)

    # Add foreign key columns to inventaire table (table exists from migration 000)
    op.add_column('inventaire', sa.Column('unite_stockage_id', sa.Integer(), nullable=True))
    op.add_column('inventaire', sa.Column('unite_commande_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraints
    op.create_foreign_key('fk_inventaire_unite_stockage', 'inventaire', 'unites_stockage', ['unite_stockage_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_inventaire_unite_commande', 'inventaire', 'unites_commande', ['unite_commande_id'], ['id'], ondelete='SET NULL')
    
    # Create indexes for foreign keys
    op.create_index(op.f('ix_inventaire_unite_stockage_id'), 'inventaire', ['unite_stockage_id'], unique=False)
    op.create_index(op.f('ix_inventaire_unite_commande_id'), 'inventaire', ['unite_commande_id'], unique=False)

    # Remove old text columns (unite_stockage and unite_commande) from inventaire table
    op.drop_column('inventaire', 'unite_stockage')
    op.drop_column('inventaire', 'unite_commande')

    # Insert some default units
    # Unités de stockage communes
    op.execute("""
        INSERT INTO unites_stockage (code_unite, nom_unite, symbole, description, type_unite, facteur_conversion, unite_base, statut) VALUES
        ('KG', 'Kilogramme', 'kg', 'Unité de poids', 'Poids', 1.0000, 'kg', 'Actif'),
        ('G', 'Gramme', 'g', 'Unité de poids', 'Poids', 0.0010, 'kg', 'Actif'),
        ('L', 'Litre', 'L', 'Unité de volume', 'Volume', 1.0000, 'L', 'Actif'),
        ('ML', 'Millilitre', 'mL', 'Unité de volume', 'Volume', 0.0010, 'L', 'Actif'),
        ('M', 'Mètre', 'm', 'Unité de longueur', 'Longueur', 1.0000, 'm', 'Actif'),
        ('CM', 'Centimètre', 'cm', 'Unité de longueur', 'Longueur', 0.0100, 'm', 'Actif'),
        ('PCS', 'Pièces', 'pcs', 'Unité de quantité', 'Quantité', 1.0000, 'pcs', 'Actif'),
        ('U', 'Unité', 'u', 'Unité de quantité', 'Quantité', 1.0000, 'u', 'Actif');
    """)

    # Unités de commande communes
    op.execute("""
        INSERT INTO unites_commande (code_unite, nom_unite, symbole, description, type_unite, quantite_unitaire, facteur_conversion, statut) VALUES
        ('CARTON', 'Carton', 'carton', 'Conditionnement en carton', 'Conditionnement', 1, 1.0000, 'Actif'),
        ('PALETTE', 'Palette', 'palette', 'Conditionnement en palette', 'Conditionnement', 1, 1.0000, 'Actif'),
        ('SAC', 'Sac', 'sac', 'Conditionnement en sac', 'Conditionnement', 1, 1.0000, 'Actif'),
        ('BIDON', 'Bidon', 'bidon', 'Conditionnement en bidon', 'Conditionnement', 1, 1.0000, 'Actif'),
        ('BOITE', 'Boîte', 'boîte', 'Conditionnement en boîte', 'Conditionnement', 1, 1.0000, 'Actif'),
        ('LOT', 'Lot', 'lot', 'Conditionnement par lot', 'Lot', 1, 1.0000, 'Actif'),
        ('PACK', 'Pack', 'pack', 'Conditionnement en pack', 'Pack', 1, 1.0000, 'Actif'),
        ('ROULEAU', 'Rouleau', 'rouleau', 'Conditionnement en rouleau', 'Conditionnement', 1, 1.0000, 'Actif');
    """)


def downgrade():
    # Add back the old text columns
    op.add_column('inventaire', sa.Column('unite_stockage', sa.String(length=20), nullable=True))
    op.add_column('inventaire', sa.Column('unite_commande', sa.String(length=50), nullable=True))
    
    # Drop foreign key constraints and indexes
    op.drop_index(op.f('ix_inventaire_unite_commande_id'), table_name='inventaire')
    op.drop_index(op.f('ix_inventaire_unite_stockage_id'), table_name='inventaire')
    op.drop_constraint('fk_inventaire_unite_commande', 'inventaire', type_='foreignkey')
    op.drop_constraint('fk_inventaire_unite_stockage', 'inventaire', type_='foreignkey')
    
    # Drop foreign key columns
    op.drop_column('inventaire', 'unite_commande_id')
    op.drop_column('inventaire', 'unite_stockage_id')
    
    # Drop unite tables
    op.drop_index(op.f('ix_unites_commande_nom_unite'), table_name='unites_commande')
    op.drop_index(op.f('ix_unites_commande_code_unite'), table_name='unites_commande')
    op.drop_index(op.f('ix_unites_commande_id'), table_name='unites_commande')
    op.drop_table('unites_commande')
    
    op.drop_index(op.f('ix_unites_stockage_nom_unite'), table_name='unites_stockage')
    op.drop_index(op.f('ix_unites_stockage_code_unite'), table_name='unites_stockage')
    op.drop_index(op.f('ix_unites_stockage_id'), table_name='unites_stockage')
    op.drop_table('unites_stockage') 