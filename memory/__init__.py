"""
memory/ — Operational, episodic, and semantic memory subsystem.

Three distinct memory kinds:
  - **operational**: Redis-backed, short-lived working memory for in-flight runs.
  - **episodic**: append-only log of what happened, in order. Source of truth
    for deterministic replay.
  - **semantic**: pgvector-backed knowledge store for similarity search.

This package contains:
  - ORM models (SQLAlchemy 2.0)
  - bounded-context value objects
  - schema scaffolding (Alembic migrations live in `infra/alembic/`)

It does NOT contain adapters — those live in `adapters/storage/` and
`adapters/vector_store/`.
"""

from memory.episodic import EpisodicMemoryBase
from memory.models import Base, EpisodeModel, SemanticRecordModel, WorkflowSnapshotModel
from memory.operational import OperationalMemoryBase
from memory.semantic import SemanticMemoryBase

__all__ = [
    "Base",
    "EpisodeModel",
    "EpisodicMemoryBase",
    "OperationalMemoryBase",
    "SemanticMemoryBase",
    "SemanticRecordModel",
    "WorkflowSnapshotModel",
]
