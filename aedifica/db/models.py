"""Aedifica product data model (SQLAlchemy 2.0).

Mirrors the engine's domain objects as a multi-project, multi-tenant SQL schema.
The trust contract is enforced at flush time: a ``sourced`` regulatory claim
without source refs is rejected before it can persist.
"""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from .base import Base


class TrustInvariantError(ValueError):
    """Raised when a persisted claim would violate the trust contract."""


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


_TS = lambda: mapped_column(DateTime(timezone=True), default=_utcnow)  # noqa: E731


class Org(Base):
    __tablename__ = "org"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[_dt.datetime] = _TS()
    users: Mapped[list["User"]] = relationship(back_populates="org", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="org", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("org_id", "email"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("org.id"))
    email: Mapped[str] = mapped_column(String(254))
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(40), default="member")
    api_token: Mapped[str | None] = mapped_column(String(96), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[_dt.datetime] = _TS()
    org: Mapped[Org] = relationship(back_populates="users")


class Project(Base):
    __tablename__ = "project"
    __table_args__ = (UniqueConstraint("org_id", "project_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("org.id"))
    project_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    phase_code: Mapped[str] = mapped_column(String(8), default="0")
    country: Mapped[str] = mapped_column(String(8), default="CH")
    canton: Mapped[str] = mapped_column(String(8), default="VD")
    commune: Mapped[str] = mapped_column(String(120))
    knowledge_regime: Mapped[str] = mapped_column(String(40), default="context_first")
    # Per-project regulatory inputs (AED-211): None = nothing submitted/analysed yet.
    permit_dossier: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    compliance_inputs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    brief_risks: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cost_inputs: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # AED-218
    site_inputs: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # AED-219
    created_at: Mapped[_dt.datetime] = _TS()

    org: Mapped[Org] = relationship(back_populates="projects")
    sources: Mapped[list["Source"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    claims: Mapped[list["Claim"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    routes: Mapped[list["RegulatoryRoute"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "source"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    source_id: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(60))
    locator: Mapped[str | None] = mapped_column(String(500), nullable=True)
    valid_as_of: Mapped[str | None] = mapped_column(String(40), nullable=True)
    retrieved_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    project: Mapped[Project] = relationship(back_populates="sources")


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    evidence_id: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(60))
    file_ref: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    valid_as_of: Mapped[str | None] = mapped_column(String(40), nullable=True)
    retrieved_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    project: Mapped[Project] = relationship(back_populates="evidence")


class Claim(Base):
    __tablename__ = "claim"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    claim_id: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(300))
    claim_type: Mapped[str] = mapped_column(String(40), default="regulatory")
    state: Mapped[str] = mapped_column(String(20))
    value: Mapped[dict | list | str | int | float | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), default="medium")
    formula: Mapped[str | None] = mapped_column(String(300), nullable=True)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_refs: Mapped[list] = mapped_column(JSON, default=list)
    project: Mapped[Project] = relationship(back_populates="claims")


class Report(Base):
    __tablename__ = "report"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    report_id: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(60))
    path: Mapped[str] = mapped_column(String(400))
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_refs: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[_dt.datetime] = _TS()
    project: Mapped[Project] = relationship(back_populates="reports")


class LedgerEntry(Base):
    __tablename__ = "ledger_entry"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    ledger_id: Mapped[str] = mapped_column(String(120))
    event_type: Mapped[str] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(Text)
    actor_name: Mapped[str] = mapped_column(String(200))
    actor_role: Mapped[str] = mapped_column(String(60))
    phase_code: Mapped[str] = mapped_column(String(8))
    mutating: Mapped[bool] = mapped_column(default=False)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[_dt.datetime] = _TS()
    project: Mapped[Project] = relationship(back_populates="ledger_entries")
    approval: Mapped["Approval | None"] = relationship(back_populates="ledger_entry", uselist=False, cascade="all, delete-orphan")


class Approval(Base):
    __tablename__ = "approval"
    id: Mapped[int] = mapped_column(primary_key=True)
    ledger_entry_id: Mapped[int] = mapped_column(ForeignKey("ledger_entry.id"))
    approved_by: Mapped[str] = mapped_column(String(200))
    scope: Mapped[str] = mapped_column(String(40))
    basis: Mapped[str] = mapped_column(Text)
    approved_at: Mapped[str] = mapped_column(String(40))
    ledger_entry: Mapped[LedgerEntry] = relationship(back_populates="approval")


class RegulatoryRoute(Base):
    __tablename__ = "regulatory_route"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    route_id: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(8))
    canton: Mapped[str] = mapped_column(String(8))
    commune: Mapped[str] = mapped_column(String(120))
    selected_at: Mapped[str] = mapped_column(String(40))
    active_pack_ids: Mapped[list] = mapped_column(JSON, default=list)
    project: Mapped[Project] = relationship(back_populates="routes")


class CommunePack(Base):
    """Shared, versioned commune pack (NOT project-scoped) — capitalizable cache."""

    __tablename__ = "commune_pack"
    __table_args__ = (UniqueConstraint("commune", "canton", "version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    commune: Mapped[str] = mapped_column(String(120))
    canton: Mapped[str] = mapped_column(String(8))
    version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="seed")  # seed|ingested|supported
    source_authority: Mapped[str | None] = mapped_column(String(300), nullable=True)
    valid_as_of: Mapped[str | None] = mapped_column(String(40), nullable=True)
    review_due: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ingested_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    jobs: Mapped[list["IngestionJob"]] = relationship(back_populates="pack", cascade="all, delete-orphan")


class IngestionJob(Base):
    __tablename__ = "ingestion_job"
    id: Mapped[int] = mapped_column(primary_key=True)
    commune_pack_id: Mapped[int] = mapped_column(ForeignKey("commune_pack.id"))
    status: Mapped[str] = mapped_column(String(30), default="requested")
    requested_at: Mapped[_dt.datetime] = _TS()
    sources: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pack: Mapped[CommunePack] = relationship(back_populates="jobs")


# --------------------------------------------------------------------------- #
# Trust invariant — enforced at flush, not just in the renderer.
# A sourced regulatory claim must carry source refs (mirrors claims.validate_claim).
# --------------------------------------------------------------------------- #
def _claim_violates_trust(claim: "Claim") -> bool:
    return (
        claim.claim_type == "regulatory"
        and claim.state == "sourced"
        and not (claim.source_refs or [])
    )


@event.listens_for(Session, "before_flush")
def _enforce_trust_invariant(session: Session, flush_context, instances) -> None:
    for obj in list(session.new) + list(session.dirty):
        if isinstance(obj, Claim) and _claim_violates_trust(obj):
            raise TrustInvariantError(
                f"claim {obj.claim_id!r} is sourced+regulatory but has no source_refs"
            )
