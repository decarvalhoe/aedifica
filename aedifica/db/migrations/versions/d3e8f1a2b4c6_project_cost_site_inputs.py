"""project_cost_site_inputs

Per-project cost and site inputs (AED-218 / AED-219): cost/tender and
site/handover reports become project-scoped, mirroring the regulatory inputs
added in c2f7a1b9d3e4.

Revision ID: d3e8f1a2b4c6
Revises: c2f7a1b9d3e4
Create Date: 2026-06-03 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'd3e8f1a2b4c6'
down_revision = 'c2f7a1b9d3e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cost_inputs', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('site_inputs', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('site_inputs')
        batch_op.drop_column('cost_inputs')
