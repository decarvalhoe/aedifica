"""Aedifica product persistence layer (SQL).

SQLAlchemy 2.0 models + session factory for the deployed multi-project product.
The trust contract is enforced at the DB layer: a ``sourced`` regulatory claim
cannot be flushed without source refs. See docs/architecture/adr-0002-product-architecture.md.

Importing this package requires the ``product`` optional dependencies
(SQLAlchemy). The offline engine (pilot/ + aedifica core) stays stdlib-only.
"""
from __future__ import annotations

from .base import Base
from .models import (
    Approval,
    Claim,
    CommunePack,
    Evidence,
    IngestionJob,
    JurisdictionKnowledgeChunk,
    LedgerEntry,
    Org,
    Project,
    ProjectKnowledgeChunk,
    RegulatoryRoute,
    Report,
    Source,
    TrustInvariantError,
    User,
)
from .session import DEFAULT_URL, make_engine, make_session_factory

__all__ = [
    "Base",
    "Org",
    "User",
    "Project",
    "Source",
    "Evidence",
    "JurisdictionKnowledgeChunk",
    "ProjectKnowledgeChunk",
    "Claim",
    "Report",
    "LedgerEntry",
    "Approval",
    "RegulatoryRoute",
    "CommunePack",
    "IngestionJob",
    "TrustInvariantError",
    "make_engine",
    "make_session_factory",
    "DEFAULT_URL",
]
