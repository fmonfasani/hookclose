"""Architecture / cognition events emitted by the ClaudeArchitectWorker."""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class ArchitectureReviewed(DomainEvent):
    event_type: ClassVar[str] = "architecture.reviewed"
    topic: ClassVar[str] = EventTopic.REVIEW.value

    target: str
    kind: str
    score: int
    finding_count: int
    provider: str


@register_event
class ArchitectureDriftDetected(DomainEvent):
    event_type: ClassVar[str] = "architecture.drift_detected"
    topic: ClassVar[str] = EventTopic.REVIEW.value

    target: str
    previous_score: int
    current_score: int
    delta: int


@register_event
class SpecGenerated(DomainEvent):
    event_type: ClassVar[str] = "architecture.spec_generated"
    topic: ClassVar[str] = EventTopic.REVIEW.value

    target: str
    kind: str
    provider: str
    section_count: int
