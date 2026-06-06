"""w11.B attachments — polymorphic file pointer (upload OR external link)
for any domain object (document, brs, checklist, task, capture, permit).

Revision ID: c3f7e2a8d5b1
Revises: a2b5e8d4c1f7
Create Date: 2026-06-06 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'c3f7e2a8d5b1'
down_revision = 'a2b5e8d4c1f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'attachment',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('owner_kind', sa.String(length=20), nullable=False),
        sa.Column('owner_id', sa.String(length=120), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('url', sa.String(length=2000), nullable=True),
        sa.Column('file_ref', sa.String(length=500), nullable=True),
        sa.Column('provider', sa.String(length=20), nullable=False, server_default='url'),
        sa.Column('mime', sa.String(length=120), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('sha256', sa.String(length=64), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_attachment_owner', 'attachment', ['project_id', 'owner_kind', 'owner_id'])


def downgrade() -> None:
    op.drop_index('ix_attachment_owner', table_name='attachment')
    op.drop_table('attachment')
