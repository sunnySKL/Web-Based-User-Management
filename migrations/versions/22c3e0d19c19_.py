"""empty message

Revision ID: 22c3e0d19c19
Revises: 548dfa51b8d7, add_cougar_id_to_user
Create Date: 2025-04-22 02:37:06.540094

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22c3e0d19c19'
down_revision = ('548dfa51b8d7', 'add_cougar_id_to_user')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
