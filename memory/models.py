"""SQLAlchemy 2.0 ORM models for the memory subsystem.

Schema only — no queries, no logic. Persistence operations live in
`adapters/storage/`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import JSON, BigInteger, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base. Naming convention is consistent for Alembic."""

    metadata_naming_convention: ClassVar[dict[str, str]] = {
        "ix": "ix_%(table_name)s_%(column_0_N_name)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class EpisodeModel(Base):
    """Append-only event log entry."""

    __tablename__ = "episodes"

    episode_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(128))
    occurred_at_unix_ms: Mapped[int] = mapped_column(BigInteger, index=True)
    kind: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)

    __table_args__ = (Index("ix_episodes_workflow_time", "workflow_id", "occurred_at_unix_ms"),)


class WorkflowSnapshotModel(Base):
    """Materialised projection of a workflow instance for fast lookup."""

    __tablename__ = "workflow_snapshots"

    workflow_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    definition: Mapped[str] = mapped_column(String(128), index=True)
    definition_version: Mapped[str] = mapped_column(String(32))
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    runtime_state: Mapped[str] = mapped_column(String(32), index=True)
    application_state: Mapped[str] = mapped_column(String(64))
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB)
    outputs: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column()


class SemanticRecordModel(Base):
    """pgvector-backed semantic record. Adapter binds the `embedding` column
    to a real `vector(N)` at migration time — left untyped here to stay
    pgvector-version agnostic in scaffolding."""

    __tablename__ = "semantic_records"

    record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    namespace: Mapped[str] = mapped_column(String(128), index=True)
    text: Mapped[str] = mapped_column(Text)
    record_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    __table_args__ = (Index("ix_semantic_records_ns", "namespace"),)
