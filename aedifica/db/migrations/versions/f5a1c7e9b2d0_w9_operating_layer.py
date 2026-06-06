"""w9 operating layer: intervenants, documents, access

Revision ID: f5a1c7e9b2d0
Revises: e4c9a2f6b1d8
Create Date: 2026-06-06 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'f5a1c7e9b2d0'
down_revision = 'e4c9a2f6b1d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'intervenant_group',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('intervenant_group.id'), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('kind', sa.String(length=60), nullable=False, server_default='group'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        'intervenant',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('intervenant_group.id'), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=120), nullable=True),
        sa.Column('organization', sa.String(length=200), nullable=True),
        sa.Column('email', sa.String(length=254), nullable=True),
        sa.Column('phone', sa.String(length=40), nullable=True),
        sa.Column('is_responsible', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        'document',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('official_name', sa.String(length=300), nullable=False),
        sa.Column('category', sa.String(length=80), nullable=False, server_default='general'),
        sa.Column('validation_level', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('confidential', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validated_at', sa.String(length=40), nullable=True),
        sa.Column('validated_by', sa.String(length=200), nullable=True),
    )
    op.create_table(
        'document_version',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('document.id'), nullable=False),
        sa.Column('label', sa.String(length=40), nullable=False),
        sa.Column('file_ref', sa.String(length=500), nullable=True),
        sa.Column('sha256', sa.String(length=64), nullable=True),
        sa.Column('source', sa.String(length=40), nullable=False, server_default='manual'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        'access_grant',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('document.id'), nullable=False),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('intervenant_group.id'), nullable=True),
        sa.Column('intervenant_id', sa.Integer(), sa.ForeignKey('intervenant.id'), nullable=True),
        sa.Column('level', sa.String(length=20), nullable=False, server_default='read'),
    )


def downgrade() -> None:
    op.drop_table('access_grant')
    op.drop_table('document_version')
    op.drop_table('document')
    op.drop_table('intervenant')
    op.drop_table('intervenant_group')
