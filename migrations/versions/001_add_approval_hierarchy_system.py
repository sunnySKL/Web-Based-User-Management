"""Add approval hierarchy system

Revision ID: 001
Revises: 
Create Date: 2024-02-23 17:47:30.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create approval_logs table
    op.create_table('approval_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('approver_email', sa.String(length=100), nullable=False),
        sa.Column('approver_role', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['academic_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop approval_logs table
    op.drop_table('approval_logs')
