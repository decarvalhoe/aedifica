"""w19-02 facet-aware trust fields for claims and sources

Revision ID: i9e6f2a4c3d1
Revises: h8d5e1f3a2c9
Create Date: 2026-06-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'i9e6f2a4c3d1'
down_revision = 'h8d5e1f3a2c9'
branch_labels = None
depends_on = None


def _add_facet_columns(table_name: str) -> None:
    with op.batch_alter_table(table_name) as batch:
        batch.add_column(sa.Column('trust_tier', sa.String(length=20), nullable=True, server_default='unverified'))
        batch.add_column(sa.Column('provenance', sa.String(length=40), nullable=True, server_default='official'))
        batch.add_column(sa.Column('facets', sa.JSON(), nullable=True, server_default=sa.text("'{}'")))


def _drop_facet_columns(table_name: str) -> None:
    with op.batch_alter_table(table_name) as batch:
        batch.drop_column('facets')
        batch.drop_column('provenance')
        batch.drop_column('trust_tier')


def upgrade() -> None:
    _add_facet_columns('source')
    _add_facet_columns('claim')


def downgrade() -> None:
    _drop_facet_columns('claim')
    _drop_facet_columns('source')
