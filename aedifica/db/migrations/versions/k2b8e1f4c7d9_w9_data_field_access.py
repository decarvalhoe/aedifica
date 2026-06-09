"""w9 data-level document access grants

Revision ID: k2b8e1f4c7d9
Revises: j4f7a2c9d8e3
Create Date: 2026-06-09 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'k2b8e1f4c7d9'
down_revision = 'j4f7a2c9d8e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('access_grant') as batch:
        batch.add_column(sa.Column('field_scope', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('access_grant') as batch:
        batch.drop_column('field_scope')
