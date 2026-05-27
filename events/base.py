"""Base classes shared by every domain event."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from ulid import ULID


def _new_event_id() -> str:
    return str(ULID())


def _now_utc() -> datetime:
    return datetime.now(UTC)


class EventMetadata(BaseModel):
    """Envelope metadata attached to every event. Carries the causal graph."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str = Field(default_factory=_new_event_id)
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None
    occurred_at: datetime = Field(default_factory=_now_utc)
    producer: str = "aine-runtime"
    tenant_id: str | None = None
    schema_version: int = 1


class DomainEvent(BaseModel):
    """Abstract base for all domain events. Concrete subclasses MUST override
    `event_type` and `event_version` as ClassVars and add their own payload
    fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_type: ClassVar[str]
    event_version: ClassVar[int] = 1
    topic: ClassVar[str]

    metadata: EventMetadata = Field(default_factory=EventMetadata)

    def to_envelope(self) -> dict[str, Any]:
        """Serialize for transport on the event bus."""
        return {
            "type": self.event_type,
            "version": self.event_version,
            "topic": self.topic,
            "metadata": self.metadata.model_dump(mode="json"),
            "payload": self.model_dump(mode="json", exclude={"metadata"}),
        }
