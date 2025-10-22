"""merge_multiple_heads

Revision ID: 6ce8d31e8b5e
Revises: add_maintenance_alert_sent, add_time_fields_res, add_user_timestamp_fields, create_equipment_tables
Create Date: 2025-10-22 15:05:34.376380

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ce8d31e8b5e'
down_revision = ('add_maintenance_alert_sent', 'add_time_fields_res', 'add_user_timestamp_fields', 'create_equipment_tables')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
