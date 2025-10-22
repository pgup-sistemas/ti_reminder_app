"""Criar tabelas de equipamentos

Revision ID: create_equipment_tables
Revises: a861e2bfb112
Create Date: 2025-10-20 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'create_equipment_tables'
down_revision = 'b91b0d7d62b4'
branch_labels = None
depends_on = None


def upgrade():
    # Criar tabela equipment
    op.create_table('equipment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('brand', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('patrimony', sa.String(length=50), nullable=True),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='disponivel'),
        sa.Column('condition', sa.String(length=20), nullable=False, server_default='bom'),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('warranty_expiry', sa.Date(), nullable=True),
        sa.Column('last_maintenance', sa.Date(), nullable=True),
        sa.Column('next_maintenance', sa.Date(), nullable=True),
        sa.Column('maintenance_alert_sent', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('requires_approval', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('max_loan_days', sa.Integer(), nullable=True, server_default='7'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices para equipment
    op.create_index('ix_equipment_status', 'equipment', ['status'])
    op.create_index('ix_equipment_category', 'equipment', ['category'])
    op.create_index('ix_equipment_patrimony', 'equipment', ['patrimony'])
    
    # Criar tabela equipment_reservation
    op.create_table('equipment_reservation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False, server_default='09:00:00'),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False, server_default='18:00:00'),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('end_datetime', sa.DateTime(), nullable=False),
        sa.Column('expected_return_date', sa.Date(), nullable=False),
        sa.Column('expected_return_time', sa.Time(), nullable=False, server_default='18:00:00'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pendente'),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approval_date', sa.DateTime(), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['approved_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices para equipment_reservation
    op.create_index('ix_equipment_reservation_status', 'equipment_reservation', ['status'])
    op.create_index('ix_equipment_reservation_start_date', 'equipment_reservation', ['start_date'])
    op.create_index('ix_equipment_reservation_end_date', 'equipment_reservation', ['end_date'])
    op.create_index('ix_equipment_reservation_start_datetime', 'equipment_reservation', ['start_datetime'])
    op.create_index('ix_equipment_reservation_end_datetime', 'equipment_reservation', ['end_datetime'])
    op.create_index('ix_equipment_reservation_created_at', 'equipment_reservation', ['created_at'])
    
    # Criar tabela equipment_loan
    op.create_table('equipment_loan',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('loan_date', sa.DateTime(), nullable=False),
        sa.Column('expected_return_date', sa.DateTime(), nullable=False),
        sa.Column('actual_return_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ativo'),
        sa.Column('condition_at_loan', sa.String(length=20), nullable=True),
        sa.Column('condition_at_return', sa.String(length=20), nullable=True),
        sa.Column('received_by_id', sa.Integer(), nullable=True),
        sa.Column('return_notes', sa.Text(), nullable=True),
        sa.Column('reservation_id', sa.Integer(), nullable=True),
        sa.Column('sla_status', sa.String(length=20), nullable=True, server_default='normal'),
        sa.Column('sla_deadline', sa.DateTime(), nullable=True),
        sa.Column('return_reminder_sent', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['received_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['reservation_id'], ['equipment_reservation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices para equipment_loan
    op.create_index('ix_equipment_loan_status', 'equipment_loan', ['status'])
    op.create_index('ix_equipment_loan_user_id', 'equipment_loan', ['user_id'])
    op.create_index('ix_equipment_loan_equipment_id', 'equipment_loan', ['equipment_id'])


def downgrade():
    # Remover índices de equipment_loan
    op.drop_index('ix_equipment_loan_equipment_id', table_name='equipment_loan')
    op.drop_index('ix_equipment_loan_user_id', table_name='equipment_loan')
    op.drop_index('ix_equipment_loan_status', table_name='equipment_loan')
    
    # Remover tabela equipment_loan
    op.drop_table('equipment_loan')
    
    # Remover índices de equipment_reservation
    op.drop_index('ix_equipment_reservation_created_at', table_name='equipment_reservation')
    op.drop_index('ix_equipment_reservation_end_datetime', table_name='equipment_reservation')
    op.drop_index('ix_equipment_reservation_start_datetime', table_name='equipment_reservation')
    op.drop_index('ix_equipment_reservation_end_date', table_name='equipment_reservation')
    op.drop_index('ix_equipment_reservation_start_date', table_name='equipment_reservation')
    op.drop_index('ix_equipment_reservation_status', table_name='equipment_reservation')
    
    # Remover tabela equipment_reservation
    op.drop_table('equipment_reservation')
    
    # Remover índices de equipment
    op.drop_index('ix_equipment_patrimony', table_name='equipment')
    op.drop_index('ix_equipment_category', table_name='equipment')
    op.drop_index('ix_equipment_status', table_name='equipment')
    
    # Remover tabela equipment
    op.drop_table('equipment')
