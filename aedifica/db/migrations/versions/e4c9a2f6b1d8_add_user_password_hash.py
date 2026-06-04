"""add_user_password_hash

Revision ID: e4c9a2f6b1d8
Revises: d3e8f1a2b4c6
Create Date: 2026-06-04 10:20:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'e4c9a2f6b1d8'
down_revision = 'd3e8f1a2b4c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password_hash')
