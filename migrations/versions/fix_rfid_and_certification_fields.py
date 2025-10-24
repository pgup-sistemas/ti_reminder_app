"""Fix RFID fields and certification awarded_at

Revision ID: fix_rfid_cert_fields
Revises: 
Create Date: 2025-10-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_rfid_cert_fields'
down_revision = 'security_fields_001'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos RFID ao Equipment
    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rfid_last_scan', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('rfid_last_location', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('rfid_reader_id', sa.String(length=50), nullable=True))

    # A coluna awarded_at já existe no banco, não precisa renomear


def downgrade():
    # Remover campos RFID do Equipment
    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.drop_column('rfid_reader_id')
        batch_op.drop_column('rfid_last_location')
        batch_op.drop_column('rfid_last_scan')
