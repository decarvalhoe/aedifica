"""project_regulatory_inputs

Per-project regulatory inputs (AED-211): permit dossier, compliance inputs and
brief risks become project-scoped so reports run on the project's own data
instead of a global fixture.

Revision ID: c2f7a1b9d3e4
Revises: bd0bea40e23d
Create Date: 2026-06-03 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'c2f7a1b9d3e4'
down_revision = 'bd0bea40e23d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('permit_dossier', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('compliance_inputs', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('brief_risks', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('brief_risks')
        batch_op.drop_column('compliance_inputs')
        batch_op.drop_column('permit_dossier')
