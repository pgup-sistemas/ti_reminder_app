"""add security fields to user

Revision ID: security_fields_001
Revises: 6ce8d31e8b5e
Create Date: 2025-01-23 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'security_fields_001'
down_revision = '6ce8d31e8b5e'
branch_labels = None
depends_on = None


def upgrade():
    """
    Adiciona campos de segurança e auditoria à tabela user.
    """
    # Adicionar campos de segurança se não existirem
    try:
        op.add_column('user', sa.Column('login_attempts', sa.Integer(), nullable=False, server_default='0'))
    except:
        pass
    
    try:
        op.add_column('user', sa.Column('locked_until', sa.DateTime(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('user', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('user', sa.Column('last_failed_login', sa.DateTime(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('user', sa.Column('last_password_reset', sa.DateTime(), nullable=True))
    except:
        pass


def downgrade():
    """
    Remove campos de segurança e auditoria da tabela user.
    """
    op.drop_column('user', 'last_password_reset')
    op.drop_column('user', 'last_failed_login')
    op.drop_column('user', 'password_changed_at')
    op.drop_column('user', 'locked_until')
    op.drop_column('user', 'login_attempts')
