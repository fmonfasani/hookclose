"""Automated repair / self-healing events."""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class RepairProposed(DomainEvent):
    event_type: ClassVar[str] = "repair.proposed"
    topic: ClassVar[str] = EventTopic.REPAIR.value

    repair_id: str
    target_ref: str  # what's being repaired (test name, file:line, etc.)
    diagnosis: str
    patch_diff_hash: str


@register_event
class RepairAttempted(DomainEvent):
    event_type: ClassVar[str] = "repair.attempted"
    topic: ClassVar[str] = EventTopic.REPAIR.value

    repair_id: str
    attempt: int
    success: bool
    duration_ms: int


@register_event
class RepairValidated(DomainEvent):
    event_type: ClassVar[str] = "repair.validated"
    topic: ClassVar[str] = EventTopic.REPAIR.value

    repair_id: str
    validation_method: str  # "tests" | "lint" | "human"
    passed: bool
