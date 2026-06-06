"""w12.C LLM opt-in — per-project llm_mode (off|local|cloud).

Local = Ollama on the atelier's machine (confidential allowed).
Cloud = opt-in hosted model (confidential pieces EXCLUDED from prompts).
Off = no LLM call.

Revision ID: g7c4d9e3f1b2
Revises: f6b3c8d2e9a1
Create Date: 2026-06-06 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'g7c4d9e3f1b2'
down_revision = 'f6b3c8d2e9a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('project',
                  sa.Column('llm_mode', sa.String(length=10), nullable=False,
                            server_default='off'))


def downgrade() -> None:
    op.drop_column('project', 'llm_mode')
