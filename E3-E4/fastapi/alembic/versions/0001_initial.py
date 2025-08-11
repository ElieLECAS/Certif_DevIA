"""Initial schema

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2025-08-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_staff', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('nom', sa.String(), nullable=True),
        sa.Column('prenom', sa.String(), nullable=True),
        sa.Column('telephone', sa.String(), nullable=True),
        sa.Column('adresse', sa.Text(), nullable=True),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('client_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, server_default=sa.text("'nouveau'")),
        sa.Column('history', sa.JSON(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # client_users
    op.create_table(
        'client_users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_client_only', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('active_conversation_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['active_conversation_id'], ['conversations.id']),
        sa.UniqueConstraint('user_id', name='uq_client_users_user_id'),
    )

    # commandes
    op.create_table(
        'commandes',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('numero_commande', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date_commande', sa.DateTime(), nullable=True),
        sa.Column('date_livraison', sa.DateTime(), nullable=True),
        sa.Column('statut', sa.String(), nullable=True, server_default=sa.text("'en_cours'")),
        sa.Column('montant_ht', sa.Float(), nullable=False),
        sa.Column('montant_ttc', sa.Float(), nullable=False),
        sa.Column('produits', sa.JSON(), nullable=True),
        sa.Column('adresse_livraison', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_commandes_numero_commande', 'commandes', ['numero_commande'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_commandes_numero_commande', table_name='commandes')
    op.drop_table('commandes')
    op.drop_table('client_users')
    op.drop_table('conversations')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')


