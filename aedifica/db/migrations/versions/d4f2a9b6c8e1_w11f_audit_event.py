"""w11.F AAA — append-only audit log of org/project security events
(invites, revocations, access grants, token rotations, password resets).

Revision ID: d4f2a9b6c8e1
Revises: c3f7e2a8d5b1
Create Date: 2026-06-06 19:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'd4f2a9b6c8e1'
down_revision = 'c3f7e2a8d5b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_event',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('org.id'), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=True),
        sa.Column('event_type', sa.String(length=40), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('actor_name', sa.String(length=200), nullable=False),
        sa.Column('actor_role', sa.String(length=20), nullable=False),
        sa.Column('target_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('target_summary', sa.Text(), nullable=False),
        sa.Column('meta_json', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_audit_event_org', 'audit_event', ['org_id', 'timestamp'])
    op.create_index('ix_audit_event_project', 'audit_event', ['project_id', 'timestamp'])


def downgrade() -> None:
    op.drop_index('ix_audit_event_project', table_name='audit_event')
    op.drop_index('ix_audit_event_org', table_name='audit_event')
    op.drop_table('audit_event')
