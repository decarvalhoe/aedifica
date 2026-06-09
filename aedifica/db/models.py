"""Aedifica product data model (SQLAlchemy 2.0).

Mirrors the engine's domain objects as a multi-project, multi-tenant SQL schema.
The trust contract is enforced at flush time: a ``sourced`` regulatory claim
without source refs is rejected before it can persist.
"""
from __future__ import annotations

import datetime as _dt

from sqlalchemy import (
    DateTime,
    Float,
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
    # W10: when role=external, this links the user to a specific intervenant on a project.
    # All their scoped data access derives from this link (the user only sees their slice).
    linked_intervenant_id: Mapped[int | None] = mapped_column(ForeignKey("intervenant.id"), nullable=True)
    invite_token: Mapped[str | None] = mapped_column(String(96), unique=True, nullable=True)
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
    # W12.C — LLM opt-in mode: off (default) | local (Ollama, on the atelier's
    # machine, confidential content allowed) | cloud (opt-in, confidential
    # content NEVER sent — pieces with confidential=true are excluded from the
    # prompt by the LLM layer).
    llm_mode: Mapped[str] = mapped_column(String(10), default="off")
    created_at: Mapped[_dt.datetime] = _TS()

    org: Mapped[Org] = relationship(back_populates="projects")
    sources: Mapped[list["Source"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    claims: Mapped[list["Claim"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    knowledge_chunks: Mapped[list["ProjectKnowledgeChunk"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    routes: Mapped[list["RegulatoryRoute"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    intervenant_groups: Mapped[list["IntervenantGroup"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    intervenants: Mapped[list["Intervenant"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    brs_entries: Mapped[list["BrsEntry"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    captures: Mapped[list["CaptureNote"]] = relationship(back_populates="project", cascade="all, delete-orphan")


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
    trust_tier: Mapped[str | None] = mapped_column(String(20), nullable=True, default="unverified")
    provenance: Mapped[str | None] = mapped_column(String(40), nullable=True, default="official")
    facets: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
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


class JurisdictionKnowledgeChunk(Base):
    """Shared retrieval chunk pool scoped by jurisdiction, not by project."""

    __tablename__ = "jurisdiction_knowledge_chunk"
    __table_args__ = (UniqueConstraint("country", "canton", "commune", "chunk_id", name="uq_jurisdiction_chunk_scope"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    country: Mapped[str] = mapped_column(String(8), default="CH")
    canton: Mapped[str | None] = mapped_column(String(8), nullable=True)
    commune: Mapped[str | None] = mapped_column(String(120), nullable=True)
    chunk_id: Mapped[str] = mapped_column(String(160))
    text: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str] = mapped_column(String(64))
    source_path: Mapped[str] = mapped_column(String(500))
    span: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    facets: Mapped[dict] = mapped_column(JSON, default=dict)
    trust_tier: Mapped[str | None] = mapped_column(String(20), nullable=True, default="unverified")
    provenance: Mapped[str | None] = mapped_column(String(40), nullable=True, default="official")
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[_dt.datetime] = _TS()


class ProjectKnowledgeChunk(Base):
    """Project-private retrieval chunk silo; Postgres RLS is added by migration."""

    __tablename__ = "project_knowledge_chunk"
    __table_args__ = (UniqueConstraint("project_id", "chunk_id", name="uq_project_chunk_scope"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    chunk_id: Mapped[str] = mapped_column(String(160))
    text: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str] = mapped_column(String(64))
    source_path: Mapped[str] = mapped_column(String(500))
    span: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    facets: Mapped[dict] = mapped_column(JSON, default=dict)
    trust_tier: Mapped[str | None] = mapped_column(String(20), nullable=True, default="unverified")
    provenance: Mapped[str | None] = mapped_column(String(40), nullable=True, default="user_promoted")
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[_dt.datetime] = _TS()
    project: Mapped[Project] = relationship(back_populates="knowledge_chunks")


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
    trust_tier: Mapped[str | None] = mapped_column(String(20), nullable=True, default="unverified")
    provenance: Mapped[str | None] = mapped_column(String(40), nullable=True, default="official")
    facets: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
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
# W9 — Operating layer: intervenants, documents & access (the "Project OS").    #
# Captured from the partner session (docs/strategy/session-2026-06-05-…).        #
# --------------------------------------------------------------------------- #
VALIDATION_LEVELS = ("pending", "canonical", "indicative", "refused")
ACCESS_LEVELS = ("read", "write")
DOCUMENT_ACCESS_FIELDS = (
    "official_name",
    "category",
    "validation_level",
    "confidential",
    "note",
    "validated_by",
    "validated_at",
    "versions",
    "latest",
)


class IntervenantGroup(Base):
    """A group of actors on a project (a company / a discipline), nestable via parent_id."""

    __tablename__ = "intervenant_group"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("intervenant_group.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(60), default="group")  # company | discipline | group
    created_at: Mapped[_dt.datetime] = _TS()
    project: Mapped["Project"] = relationship(back_populates="intervenant_groups")


class Intervenant(Base):
    """A person on the project, sourced with their contact and responsibility."""

    __tablename__ = "intervenant"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("intervenant_group.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)  # architecte, ingénieur civil…
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_responsible: Mapped[bool] = mapped_column(default=False)  # personne responsable / de référence
    created_at: Mapped[_dt.datetime] = _TS()
    project: Mapped["Project"] = relationship(back_populates="intervenants")


class Document(Base):
    """A project document/source under curation, validated by the lead architect."""

    __tablename__ = "document"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    official_name: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(80), default="general")  # dossier / catégorie
    validation_level: Mapped[str] = mapped_column(String(20), default="pending")  # pending|canonical|indicative|refused
    confidential: Mapped[bool] = mapped_column(default=False)  # LPD
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[_dt.datetime] = _TS()
    validated_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    project: Mapped["Project"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    grants: Mapped[list["AccessGrant"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    __tablename__ = "document_version"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    label: Mapped[str] = mapped_column(String(40))  # v1, v2…
    file_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="manual")  # manual | fetched
    uploaded_at: Mapped[_dt.datetime] = _TS()
    document: Mapped["Document"] = relationship(back_populates="versions")


class AccessGrant(Base):
    """Who (group or person) may access a document, and at what level."""

    __tablename__ = "access_grant"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("intervenant_group.id"), nullable=True)
    intervenant_id: Mapped[int | None] = mapped_column(ForeignKey("intervenant.id"), nullable=True)
    level: Mapped[str] = mapped_column(String(20), default="read")  # read | write
    # None means "full document". A non-empty list limits what an external
    # recipient can see down to explicit document fields.
    field_scope: Mapped[list | None] = mapped_column(JSON, nullable=True)
    document: Mapped["Document"] = relationship(back_populates="grants")


BRS_CHANNELS = ("phone", "email", "pv", "meeting", "other")


class BrsEntry(Base):
    """Business Requirements Specifications — a living, sourced, attributed register of
    the client/owner requirements that change over time. Append-only; each entry traces
    its channel + emitter + date for the architect's legal protection (traceability)."""

    __tablename__ = "brs_entry"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    content: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(30), default="requirement")  # requirement|change|decision
    channel: Mapped[str] = mapped_column(String(20), default="other")  # phone|email|pv|meeting|other
    emitter_intervenant_id: Mapped[int | None] = mapped_column(ForeignKey("intervenant.id"), nullable=True)
    emitter_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    supersedes_id: Mapped[int | None] = mapped_column(ForeignKey("brs_entry.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|superseded|locked
    created_at: Mapped[_dt.datetime] = _TS()
    project: Mapped["Project"] = relationship(back_populates="brs_entries")


class ChecklistItem(Base):
    """A step of the project's SIA checklist — seeded from a template per phase, then made
    parametric by the atelier (todo/done/deferred/skipped). Retroactive items back-fill
    earlier phases when a project is onboarded mid-process."""

    __tablename__ = "checklist_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    phase_code: Mapped[str] = mapped_column(String(8))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Responsible actor category (mo | architecte | mandataire | entreprise). Everything
    # that is not "architecte" is external — drives per-actor checklists + external blockers.
    actor: Mapped[str] = mapped_column(String(20), default="architecte")
    # Optional specific person on the project accountable for this step (the annuaire entry).
    responsible_intervenant_id: Mapped[int | None] = mapped_column(ForeignKey("intervenant.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="todo")  # todo|done|deferred|skipped
    order_index: Mapped[int] = mapped_column(default=0)
    is_retroactive: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[_dt.datetime] = _TS()
    project: Mapped["Project"] = relationship(back_populates="checklist_items")


TASK_PRIORITIES = ("p0", "p1", "p2")
TASK_STATUS = ("todo", "doing", "done", "blocked")


class Task(Base):
    """A project task — priority (P0/P1/P2), optional estimate/actual hours (for learned
    prediction), assignee (collaborator), deadline, quick-win flag, and dependency edges.
    The atelier navigates by priority + what blocks, across all projects (not an agenda)."""

    __tablename__ = "task"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    title: Mapped[str] = mapped_column(String(300))
    priority: Mapped[str] = mapped_column(String(8), default="p2")  # p0|p1|p2
    status: Mapped[str] = mapped_column(String(12), default="todo")  # todo|doing|done|blocked
    assignee_user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    estimate_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)  # YYYY-MM-DD
    is_quick_win: Mapped[bool] = mapped_column(default=False)
    phase_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    checklist_item_id: Mapped[int | None] = mapped_column(ForeignKey("checklist_item.id"), nullable=True)
    created_at: Mapped[_dt.datetime] = _TS()
    done_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    project: Mapped["Project"] = relationship(back_populates="tasks")


class TaskDependency(Base):
    """``task`` is blocked by ``blocked_by`` (a dependency edge for the task graph)."""

    __tablename__ = "task_dependency"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"))
    blocked_by_id: Mapped[int] = mapped_column(ForeignKey("task.id"))


CAPTURE_KINDS = ("friction", "observation", "photo", "decision", "regulation")

# W11.B: an Attachment is either an inline-uploaded blob (kind="upload") or a
# pointer to a file hosted outside Aedifica (kind="link"). The doctrine is
# explicit — the atelier already has Drive/OneDrive/Dropbox/intranet for the
# heavy plans; Aedifica is the index + the rights + the trace, not a Dropbox
# bis. Every domain object that holds documents (Document, BrsEntry,
# ChecklistItem, Task, CaptureNote, Permit dossier item…) can carry an
# attachment via the polymorphic (owner_kind, owner_id) pair.
ATTACHMENT_KINDS = ("link", "upload")
ATTACHMENT_PROVIDERS = ("local", "gdrive", "onedrive", "dropbox", "sharepoint", "icloud", "url", "other")
ATTACHMENT_OWNERS = ("document", "brs", "checklist", "task", "capture", "permit")


class Attachment(Base):
    """A file the atelier wants to reach from inside Aedifica. Either uploaded
    (`kind="upload"`, persisted at `file_ref` on the local volume) or linked
    (`kind="link"`, just a URL in `url`). Polymorphic owner: a Document, a BRS
    entry, a checklist step, a task, a capture, or a permit-dossier item all
    reuse the same table — same UI component, same access rules, single point
    of truth for *« où est ce fichier ? »*."""

    __tablename__ = "attachment"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    owner_kind: Mapped[str] = mapped_column(String(20))  # document|brs|checklist|task|capture|permit
    owner_id: Mapped[str] = mapped_column(String(120))  # int FK for the typed tables; string for permit items
    kind: Mapped[str] = mapped_column(String(10))  # link|upload
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    file_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)  # local path under /data/attachments/...
    provider: Mapped[str] = mapped_column(String(20), default="url")  # local|gdrive|onedrive|...
    mime: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[_dt.datetime] = _TS()


# W11.F — AAA: org/project-level security events that are NOT part of the
# domain ledger (which is per-project, business-meaning). Audit covers
# invitations, revocations, access grants, token rotations, password resets.
AUDIT_EVENT_TYPES = (
    "invite_issued",       # architect provisioned an external user
    "invite_redeemed",     # external accepted the invite and set their password
    "invite_revoked",      # architect cancelled an unredeemed invite
    "access_granted",      # AccessGrant created (intervenant/group can read a doc)
    "access_revoked",      # AccessGrant deleted
    "token_rotated",       # user explicitly rotated their api_token
    "token_revoked",       # user (or org owner) revoked the token, forcing re-login
    "password_set",        # user set/changed their password
    "external_view_blocked",  # external attempted an out-of-scope read; recorded for audit
    "llm_mode_changed",   # W12.C — project's llm_mode flipped off/local/cloud
    "llm_called",         # W12.C — an LLM-backed Foresight rule was invoked
    "scope_granted",      # W16 — owner set/raised a CollaboratorScope row
    "scope_revoked",      # W16 — owner removed/lowered a CollaboratorScope row
)


# W16 — fine-grained access control for internal collaborators.
# Externals (role="external") keep their own scoping via AccessGrant + the
# ExternalView. This table only constrains members/viewers; owners are
# always full-write regardless.
SCOPE_LEVELS = ("none", "read", "write")
# Surfaces the architect can scope. Settings/atelier/equipe stay role-only
# to avoid lockouts on org administration.
SCOPED_SURFACES = (
    "dashboard", "foresight", "taches", "checklist", "terrain", "copilote", "memoire",
    "coordination", "intervenants", "documents", "brs",
    "permis", "opposition", "conformite",
    "couts", "chantier",
)


class CollaboratorScope(Base):
    """Per-(user, project, surface) override of a collaborator's access
    level. Resolution walks specificity: exact → project-wide → surface-wide
    → user-default → role-default. Empty table = role-default everywhere."""

    __tablename__ = "collaborator_scope"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", "surface", name="uq_scope_triple"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("org.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id"), nullable=True)
    surface: Mapped[str | None] = mapped_column(String(30), nullable=True)
    level: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[_dt.datetime] = _TS()
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)


class AuditEvent(Base):
    """Append-only security audit log. Distinct from LedgerEntry (domain-scoped,
    project-bound) because security events (rotate token, invite, revoke) cross
    project boundaries and must survive even if the project is deleted.

    Queryable per-org (owner only) and per-project (members). Never edited,
    never deleted — only inserted."""

    __tablename__ = "audit_event"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("org.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(200))
    actor_role: Mapped[str] = mapped_column(String(20))
    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    target_summary: Mapped[str] = mapped_column(Text)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[_dt.datetime] = _TS()


# W12.A — Foresight: deterministic, explainable, decision-bound IA proposals.
# A Proposal is NEVER applied silently; it sits with confidence + basis until
# the architect accepts / defers / refuses. Source-bound by construction.
PROPOSAL_KINDS = (
    "duration_adjust",
    "cost_factor",
    "risk_alert",
    "reuse_brs",
    "reuse_checklist",
    "rebalance",
    "next_step_ranked",
    "brs_summary",        # W12.C — LLM-generated summary of a BRS thread
    "regulation_extract", # W12.C — extracted regulatory claims from a règlement
    "friction_cluster",   # W12.C — clustering of recurring frictions
)
PROPOSAL_DECISIONS = ("pending", "accepted", "deferred", "refused")


class AtelierBenchmark(Base):
    """W12.E — atelier-wide capitalization snapshot. We freeze the current
    learned ratios so they survive the noise of any single project. The
    Foresight engine can optionally prefer a recent benchmark over live
    computation for stability.

    Append-only: a snapshot is never edited. A new snapshot supersedes the
    old for "latest" lookups but the history is preserved — useful to see
    how the atelier's behavior shifts over time."""

    __tablename__ = "atelier_benchmark"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("org.id"))
    period_label: Mapped[str] = mapped_column(String(20))   # e.g. "2026-Q2"
    n_projects: Mapped[int] = mapped_column(default=0)
    n_tasks_done: Mapped[int] = mapped_column(default=0)
    duration_ratios_json: Mapped[str] = mapped_column(Text)   # JSON: {"32": 1.4, "33": 1.2}
    cost_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    frozen_at: Mapped[_dt.datetime] = _TS()


class Proposal(Base):
    """An IA proposition the architect must explicitly approve before it mutates
    anything. Doctrine: "l'IA propose, l'architecte décide" — the apply_payload
    describes WHAT would be written if accepted, basis lists WHY (named sources),
    confidence is a 0..1 number derived from the comparable count / signal
    strength, NEVER a vibe."""

    __tablename__ = "proposal"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    kind: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text)
    basis_json: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    apply_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_at: Mapped[_dt.datetime] = _TS()
    decided_at: Mapped[_dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decision: Mapped[str] = mapped_column(String(20), default="pending")
    decision_basis: Mapped[str | None] = mapped_column(Text, nullable=True)


class CaptureNote(Base):
    """A captured note — site friction/observation, a photo proof ('preuve à futur'),
    a verbal decision, or a 'regulation under study' alert. Append-only, author-tagged,
    timestamped; never fabricated (the architect enters it). Covers #232 and #231."""

    __tablename__ = "capture_note"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    kind: Mapped[str] = mapped_column(String(20), default="observation")  # friction|observation|photo|decision|regulation
    content: Mapped[str] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)  # photo URL / attachment / reference
    created_at: Mapped[_dt.datetime] = _TS()
    project: Mapped["Project"] = relationship(back_populates="captures")


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
