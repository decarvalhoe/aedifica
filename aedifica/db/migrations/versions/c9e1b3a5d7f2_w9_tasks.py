"""w9 operating layer: tasks + dependencies (multi-project pilotage)

Revision ID: c9e1b3a5d7f2
Revises: a7d2e4f1c3b5
Create Date: 2026-06-06 14:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'c9e1b3a5d7f2'
down_revision = 'a7d2e4f1c3b5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'task',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('priority', sa.String(length=8), nullable=False, server_default='p2'),
        sa.Column('status', sa.String(length=12), nullable=False, server_default='todo'),
        sa.Column('assignee_user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('estimate_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('due_date', sa.String(length=20), nullable=True),
        sa.Column('is_quick_win', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('phase_code', sa.String(length=8), nullable=True),
        sa.Column('checklist_item_id', sa.Integer(), sa.ForeignKey('checklist_item.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('done_at', sa.String(length=40), nullable=True),
    )
    op.create_table(
        'task_dependency',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('task.id'), nullable=False),
        sa.Column('blocked_by_id', sa.Integer(), sa.ForeignKey('task.id'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('task_dependency')
    op.drop_table('task')
