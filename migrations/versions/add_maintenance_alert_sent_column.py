"""Adicionar coluna maintenance_alert_sent na tabela equipment

Revision ID: add_maintenance_alert_sent
Revises: 8d56434892fd
Create Date: 2025-10-17 21:52:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_maintenance_alert_sent'
down_revision = '8d56434892fd'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar coluna maintenance_alert_sent à tabela equipment
    op.add_column('equipment', sa.Column('maintenance_alert_sent', sa.Boolean(), nullable=True, default=False))


def downgrade():
    # Remover coluna maintenance_alert_sent da tabela equipment
    op.drop_column('equipment', 'maintenance_alert_sent')