"""w12.E atelier benchmark — quarterly snapshots of learned ratios
(duration_by_phase, cost_factor) so they survive single-project noise.

Revision ID: f6b3c8d2e9a1
Revises: e5a7b3c1d9f2
Create Date: 2026-06-06 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'f6b3c8d2e9a1'
down_revision = 'e5a7b3c1d9f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'atelier_benchmark',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('org.id'), nullable=False),
        sa.Column('period_label', sa.String(length=20), nullable=False),
        sa.Column('n_projects', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('n_tasks_done', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_ratios_json', sa.Text(), nullable=False),
        sa.Column('cost_factor', sa.Float(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('frozen_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_atelier_benchmark_org_date', 'atelier_benchmark', ['org_id', 'frozen_at'])


def downgrade() -> None:
    op.drop_index('ix_atelier_benchmark_org_date', table_name='atelier_benchmark')
    op.drop_table('atelier_benchmark')
