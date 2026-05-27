"""Memory ports — episodic, semantic, and operational subsystems.

These three ports are intentionally separate. They model different memory
*kinds* with different access patterns and consistency requirements.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# --- Episodic ---------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class Episode:
    episode_id: str
    workflow_id: str
    actor: str
    occurred_at_unix_ms: int
    kind: str
    payload: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class EpisodicMemoryPort(Protocol):
    """Append-only log of what happened, in order. The source of truth for
    deterministic replay."""

    async def append(self, episode: Episode) -> None: ...

    async def stream(
        self,
        workflow_id: str,
        *,
        since_unix_ms: int | None = None,
    ) -> Iterable[Episode]: ...


# --- Semantic (vector) ------------------------------------------------------
@dataclass(frozen=True, slots=True)
class SemanticRecord:
    record_id: str
    namespace: str
    text: str
    embedding: Sequence[float]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticHit:
    record_id: str
    score: float
    text: str
    metadata: Mapping[str, Any]


@runtime_checkable
class SemanticMemoryPort(Protocol):
    """Vector-backed knowledge store (pgvector adapter)."""

    async def upsert(self, records: Sequence[SemanticRecord]) -> None: ...

    async def search(
        self,
        namespace: str,
        embedding: Sequence[float],
        *,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> Sequence[SemanticHit]: ...

    async def delete(self, namespace: str, record_ids: Sequence[str]) -> None: ...


# --- Operational ------------------------------------------------------------
@runtime_checkable
class OperationalMemoryPort(Protocol):
    """Short-lived, key/value-shaped working memory for in-flight runs.

    Conceptually the operational scratch pad of the runtime (Redis-backed).
    """

    async def get(self, namespace: str, key: str) -> bytes | None: ...

    async def set(
        self,
        namespace: str,
        key: str,
        value: bytes,
        *,
        ttl_seconds: int | None = None,
    ) -> None: ...

    async def delete(self, namespace: str, key: str) -> None: ...

    async def acquire_lock(
        self,
        namespace: str,
        key: str,
        *,
        ttl_seconds: int,
    ) -> str | None:
        """Returns a fencing token on success, None on contention."""
        ...

    async def release_lock(self, namespace: str, key: str, token: str) -> bool: ...
