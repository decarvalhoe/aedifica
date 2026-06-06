"""w9 operating layer: BRS register + SIA checklist

Revision ID: a7d2e4f1c3b5
Revises: f5a1c7e9b2d0
Create Date: 2026-06-06 13:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'a7d2e4f1c3b5'
down_revision = 'f5a1c7e9b2d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'brs_entry',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('kind', sa.String(length=30), nullable=False, server_default='requirement'),
        sa.Column('channel', sa.String(length=20), nullable=False, server_default='other'),
        sa.Column('emitter_intervenant_id', sa.Integer(), sa.ForeignKey('intervenant.id'), nullable=True),
        sa.Column('emitter_label', sa.String(length=200), nullable=True),
        sa.Column('source_ref', sa.String(length=500), nullable=True),
        sa.Column('supersedes_id', sa.Integer(), sa.ForeignKey('brs_entry.id'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        'checklist_item',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('phase_code', sa.String(length=8), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='todo'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_retroactive', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('checklist_item')
    op.drop_table('brs_entry')
