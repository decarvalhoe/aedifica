"""w10 multi-actor: external user (linked to intervenant) + invite token

External users (client / mandataire / entreprise) are invited as scoped guests on a
project. We store a link to their intervenant row and a one-shot invite token used to
seed their password.

Revision ID: a2b5e8d4c1f7
Revises: f1a4c8e2d6b9
Create Date: 2026-06-06 17:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'a2b5e8d4c1f7'
down_revision = 'f1a4c8e2d6b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('user') as batch:
        batch.add_column(sa.Column('linked_intervenant_id', sa.Integer(), sa.ForeignKey('intervenant.id'), nullable=True))
        batch.add_column(sa.Column('invite_token', sa.String(length=96), nullable=True))
        batch.create_unique_constraint('uq_user_invite_token', ['invite_token'])


def downgrade() -> None:
    with op.batch_alter_table('user') as batch:
        batch.drop_constraint('uq_user_invite_token', type_='unique')
        batch.drop_column('invite_token')
        batch.drop_column('linked_intervenant_id')
