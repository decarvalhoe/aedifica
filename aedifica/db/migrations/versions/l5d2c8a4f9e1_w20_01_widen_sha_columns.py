"""w20-01 widen sha-bearing columns for algo-prefixed NOMOS hashes

The real `nomos bundle` emitter ships source hashes as "sha256:<64 hex>" (71
chars), which the importer stores verbatim for traceability. Every column that
receives such a value moves from VARCHAR(64) to VARCHAR(80). Additive and
nullable-safe: widening a varchar never rewrites or truncates existing rows.

Revision ID: l5d2c8a4f9e1
Revises: k2b8e1f4c7d9
Create Date: 2026-06-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'l5d2c8a4f9e1'
down_revision = 'k2b8e1f4c7d9'
branch_labels = None
depends_on = None

# (table, column, nullable) — the columns that receive NOMOS source hashes.
_SHA_COLUMNS = (
    ('source', 'sha256', True),
    ('evidence', 'sha256', True),
    ('jurisdiction_knowledge_chunk', 'source_hash', False),
    ('project_knowledge_chunk', 'source_hash', False),
)


def upgrade() -> None:
    for table, column, nullable in _SHA_COLUMNS:
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                column,
                existing_type=sa.String(length=64),
                type_=sa.String(length=80),
                existing_nullable=nullable,
            )


def downgrade() -> None:
    for table, column, nullable in reversed(_SHA_COLUMNS):
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                column,
                existing_type=sa.String(length=80),
                type_=sa.String(length=64),
                existing_nullable=nullable,
            )
