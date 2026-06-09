"""w16 — collaborator_scope: fine-grained per-surface ACL for internal members/viewers.

Externals keep their own scoping via AccessGrant + ExternalView. Owners
are always full-write. Members/viewers fall back to their role default
unless a scope row tightens (or in rare cases loosens) access.

Revision ID: h8d5e1f3a2c9
Revises: g7c4d9e3f1b2
Create Date: 2026-06-07 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'h8d5e1f3a2c9'
down_revision = 'g7c4d9e3f1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'collaborator_scope',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('org.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=True),
        sa.Column('surface', sa.String(length=30), nullable=True),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.UniqueConstraint('user_id', 'project_id', 'surface', name='uq_scope_triple'),
    )
    op.create_index('ix_collab_scope_user', 'collaborator_scope', ['user_id', 'project_id'])


def downgrade() -> None:
    op.drop_index('ix_collab_scope_user', table_name='collaborator_scope')
    op.drop_table('collaborator_scope')
