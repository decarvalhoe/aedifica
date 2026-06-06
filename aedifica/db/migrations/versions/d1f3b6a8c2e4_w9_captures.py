"""w9 operating layer: capture notes (friction / photos / regulation alerts)

Revision ID: d1f3b6a8c2e4
Revises: c9e1b3a5d7f2
Create Date: 2026-06-06 15:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'd1f3b6a8c2e4'
down_revision = 'c9e1b3a5d7f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'capture_note',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False, server_default='observation'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author', sa.String(length=200), nullable=True),
        sa.Column('source_ref', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('capture_note')
