"""add system_config table

Revision ID: c5f8a9d3e7b2
Revises: b7468aedbb2a
Create Date: 2025-10-24 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c5f8a9d3e7b2'
down_revision = 'b7468aedbb2a'
branch_labels = None
depends_on = None


def upgrade():
    # Criar tabela system_config
    op.create_table('system_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(length=20), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category', 'key', name='unique_config_key')
    )
    
    # Criar indices para melhor performance
    op.create_index(op.f('ix_system_config_category'), 'system_config', ['category'], unique=False)
    op.create_index(op.f('ix_system_config_key'), 'system_config', ['key'], unique=False)


def downgrade():
    # Remover indices
    op.drop_index(op.f('ix_system_config_key'), table_name='system_config')
    op.drop_index(op.f('ix_system_config_category'), table_name='system_config')
    
    # Remover tabela
    op.drop_table('system_config')
