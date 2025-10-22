"""add time fields to equipment reservation

Revision ID: add_time_fields_res
Revises: 123456789abc
Create Date: 2025-10-20 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_time_fields_res'
down_revision = '123456789abc'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar colunas de tempo à tabela equipment_reservation
    op.add_column('equipment_reservation', sa.Column('start_time', sa.Time(), nullable=True))
    op.add_column('equipment_reservation', sa.Column('end_time', sa.Time(), nullable=True))
    op.add_column('equipment_reservation', sa.Column('start_datetime', sa.DateTime(), nullable=True))
    op.add_column('equipment_reservation', sa.Column('end_datetime', sa.DateTime(), nullable=True))
    op.add_column('equipment_reservation', sa.Column('expected_return_time', sa.Time(), nullable=True))
    
    # Atualizar registros existentes com valores padrão
    op.execute("""
        UPDATE equipment_reservation 
        SET start_time = '09:00:00'::time 
        WHERE start_time IS NULL
    """)
    
    op.execute("""
        UPDATE equipment_reservation 
        SET end_time = '18:00:00'::time 
        WHERE end_time IS NULL
    """)
    
    op.execute("""
        UPDATE equipment_reservation 
        SET expected_return_time = '18:00:00'::time 
        WHERE expected_return_time IS NULL
    """)
    
    # Criar start_datetime combinando start_date e start_time
    op.execute("""
        UPDATE equipment_reservation 
        SET start_datetime = (start_date + start_time::time)::timestamp
        WHERE start_datetime IS NULL AND start_date IS NOT NULL
    """)
    
    # Criar end_datetime combinando end_date e end_time
    op.execute("""
        UPDATE equipment_reservation 
        SET end_datetime = (end_date + end_time::time)::timestamp
        WHERE end_datetime IS NULL AND end_date IS NOT NULL
    """)
    
    # Tornar colunas NOT NULL após preencher valores
    op.alter_column('equipment_reservation', 'start_time', nullable=False)
    op.alter_column('equipment_reservation', 'end_time', nullable=False)
    op.alter_column('equipment_reservation', 'start_datetime', nullable=False)
    op.alter_column('equipment_reservation', 'end_datetime', nullable=False)
    op.alter_column('equipment_reservation', 'expected_return_time', nullable=False)
    
    # Criar índices para melhor performance
    op.create_index('ix_equipment_reservation_start_datetime', 'equipment_reservation', ['start_datetime'])
    op.create_index('ix_equipment_reservation_end_datetime', 'equipment_reservation', ['end_datetime'])


def downgrade():
    # Remover índices
    op.drop_index('ix_equipment_reservation_end_datetime', table_name='equipment_reservation')
    op.drop_index('ix_equipment_reservation_start_datetime', table_name='equipment_reservation')
    
    # Remover colunas
    op.drop_column('equipment_reservation', 'expected_return_time')
    op.drop_column('equipment_reservation', 'end_datetime')
    op.drop_column('equipment_reservation', 'start_datetime')
    op.drop_column('equipment_reservation', 'end_time')
    op.drop_column('equipment_reservation', 'start_time')
