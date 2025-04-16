"""Merge migrations

Revision ID: 8b32b6f540b9
Revises: downgrade_form_type, e70088943a26
Create Date: 2025-04-12 17:03:07.914617

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b32b6f540b9'
down_revision = ('downgrade_form_type', 'e70088943a26')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
