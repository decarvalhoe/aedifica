"""w19-03 lens-scoped retrieval chunk scaffold

Revision ID: j4f7a2c9d8e3
Revises: i9e6f2a4c3d1
Create Date: 2026-06-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'j4f7a2c9d8e3'
down_revision = 'i9e6f2a4c3d1'
branch_labels = None
depends_on = None


def _postgres_upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE jurisdiction_knowledge_chunk (
            id SERIAL PRIMARY KEY,
            country VARCHAR(8) NOT NULL DEFAULT 'CH',
            canton VARCHAR(8),
            commune VARCHAR(120),
            chunk_id VARCHAR(160) NOT NULL,
            text TEXT NOT NULL,
            source_hash VARCHAR(64) NOT NULL,
            source_path VARCHAR(500) NOT NULL,
            span JSONB,
            facets JSONB NOT NULL DEFAULT '{}'::jsonb,
            trust_tier VARCHAR(20) DEFAULT 'unverified',
            provenance VARCHAR(40) DEFAULT 'official',
            embedding vector(1536),
            created_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_jurisdiction_chunk_scope UNIQUE (country, canton, commune, chunk_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE project_knowledge_chunk (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES project(id),
            chunk_id VARCHAR(160) NOT NULL,
            text TEXT NOT NULL,
            source_hash VARCHAR(64) NOT NULL,
            source_path VARCHAR(500) NOT NULL,
            span JSONB,
            facets JSONB NOT NULL DEFAULT '{}'::jsonb,
            trust_tier VARCHAR(20) DEFAULT 'unverified',
            provenance VARCHAR(40) DEFAULT 'user_promoted',
            embedding vector(1536),
            created_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_project_chunk_scope UNIQUE (project_id, chunk_id)
        )
        """
    )
    op.execute("ALTER TABLE project_knowledge_chunk ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY project_knowledge_chunk_project_isolation
        ON project_knowledge_chunk
        USING (project_id = NULLIF(current_setting('aedifica.project_id', true), '')::integer)
        WITH CHECK (project_id = NULLIF(current_setting('aedifica.project_id', true), '')::integer)
        """
    )


def _sqlite_upgrade() -> None:
    op.create_table(
        'jurisdiction_knowledge_chunk',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('country', sa.String(length=8), nullable=False, server_default='CH'),
        sa.Column('canton', sa.String(length=8), nullable=True),
        sa.Column('commune', sa.String(length=120), nullable=True),
        sa.Column('chunk_id', sa.String(length=160), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('source_path', sa.String(length=500), nullable=False),
        sa.Column('span', sa.JSON(), nullable=True),
        sa.Column('facets', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('trust_tier', sa.String(length=20), nullable=True, server_default='unverified'),
        sa.Column('provenance', sa.String(length=40), nullable=True, server_default='official'),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('country', 'canton', 'commune', 'chunk_id', name='uq_jurisdiction_chunk_scope'),
    )
    op.create_table(
        'project_knowledge_chunk',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('chunk_id', sa.String(length=160), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('source_path', sa.String(length=500), nullable=False),
        sa.Column('span', sa.JSON(), nullable=True),
        sa.Column('facets', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('trust_tier', sa.String(length=20), nullable=True, server_default='unverified'),
        sa.Column('provenance', sa.String(length=40), nullable=True, server_default='user_promoted'),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('project_id', 'chunk_id', name='uq_project_chunk_scope'),
    )


def upgrade() -> None:
    if op.get_bind().dialect.name == 'postgresql':
        _postgres_upgrade()
    else:
        _sqlite_upgrade()


def downgrade() -> None:
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("DROP POLICY IF EXISTS project_knowledge_chunk_project_isolation ON project_knowledge_chunk")
    op.drop_table('project_knowledge_chunk')
    op.drop_table('jurisdiction_knowledge_chunk')
