"""merge heads

Revision ID: 8d7c3b307536
Revises: 001, 8b32b6f540b9, b9963af2a63b
Create Date: 2025-04-21 00:30:04.239743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d7c3b307536'
down_revision = ('001', '8b32b6f540b9', 'b9963af2a63b')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
