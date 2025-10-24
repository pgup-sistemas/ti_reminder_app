"""add secure config and config change log

Revision ID: b7468aedbb2a
Revises: fix_rfid_cert_fields
Create Date: 2025-10-24 09:38:21.797117

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7468aedbb2a'
down_revision = 'fix_rfid_cert_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'secure_config',
        sa.Column('key', sa.String(length=120), nullable=False),
        sa.Column('value', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('key')
    )

    op.create_table(
        'config_change_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=64), nullable=True),
        sa.Column('field', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['actor_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('config_change_log')
    op.drop_table('secure_config')
