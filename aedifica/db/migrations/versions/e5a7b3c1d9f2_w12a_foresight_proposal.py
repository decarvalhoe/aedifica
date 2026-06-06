"""w12.A foresight — proposal table for deterministic IA propositions
(duration / cost / risk / reuse / rebalance / next_step). Decision-bound.

Revision ID: e5a7b3c1d9f2
Revises: d4f2a9b6c8e1
Create Date: 2026-06-06 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'e5a7b3c1d9f2'
down_revision = 'd4f2a9b6c8e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'proposal',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('kind', sa.String(length=40), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('detail', sa.Text(), nullable=False),
        sa.Column('basis_json', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0'),
        sa.Column('apply_payload_json', sa.Text(), nullable=True),
        sa.Column('proposed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by', sa.String(length=200), nullable=True),
        sa.Column('decision', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('decision_basis', sa.Text(), nullable=True),
    )
    op.create_index('ix_proposal_project_decision', 'proposal', ['project_id', 'decision'])


def downgrade() -> None:
    op.drop_index('ix_proposal_project_decision', table_name='proposal')
    op.drop_table('proposal')
