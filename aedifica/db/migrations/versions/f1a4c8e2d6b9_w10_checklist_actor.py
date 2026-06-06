"""w10 multi-actor: checklist_item.actor + responsible_intervenant_id

Each SIA checklist step gets a responsible actor (mo | architecte | mandataire |
entreprise) and an optional specific intervenant. This is the spine of the per-actor
checklists (client devoirs, mandataire devoirs) and of external-blocker detection.

Revision ID: f1a4c8e2d6b9
Revises: d1f3b6a8c2e4
Create Date: 2026-06-06 17:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'f1a4c8e2d6b9'
down_revision = 'd1f3b6a8c2e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('checklist_item') as batch:
        batch.add_column(sa.Column('actor', sa.String(length=20), nullable=False, server_default='architecte'))
        batch.add_column(sa.Column('responsible_intervenant_id', sa.Integer(), sa.ForeignKey('intervenant.id'), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('checklist_item') as batch:
        batch.drop_column('responsible_intervenant_id')
        batch.drop_column('actor')
