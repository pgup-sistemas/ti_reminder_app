"""add time fields to equipment loan

Revision ID: 123456789abc
Revises: 202eb034c231
Create Date: 2023-04-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '123456789abc'
down_revision = '202eb034c231'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona a coluna loan_time com valor padrão para registros existentes
    op.add_column('equipment_loan', sa.Column('loan_time', sa.Time(), nullable=False, server_default='09:00:00'))
    
    # Adiciona a coluna expected_return_time com valor padrão para registros existentes
    op.add_column('equipment_loan', sa.Column('expected_return_time', sa.Time(), nullable=False, server_default='18:00:00'))
    
    # Remove o valor padrão após a migração dos dados
    op.alter_column('equipment_loan', 'loan_time', server_default=None)
    op.alter_column('equipment_loan', 'expected_return_time', server_default=None)

def downgrade():
    # Remove as colunas adicionadas
    op.drop_column('equipment_loan', 'expected_return_time')
    op.drop_column('equipment_loan', 'loan_time')
