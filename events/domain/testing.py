"""Autonomous testing events."""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class TestRunRequested(DomainEvent):
    event_type: ClassVar[str] = "testing.run_requested"
    topic: ClassVar[str] = EventTopic.TESTING.value

    run_id: str
    repo: str
    ref: str
    framework: str
    selectors: tuple[str, ...] = ()


@register_event
class TestRunCompleted(DomainEvent):
    event_type: ClassVar[str] = "testing.run_completed"
    topic: ClassVar[str] = EventTopic.TESTING.value

    run_id: str
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    coverage_pct: float | None = None


@register_event
class TestRunFailed(DomainEvent):
    event_type: ClassVar[str] = "testing.run_failed"
    topic: ClassVar[str] = EventTopic.TESTING.value

    run_id: str
    error_code: str
    error_message: str
    stage: str  # "setup" | "execution" | "teardown"
