"""Autonomous task-chaining events — the audit trail of generated work."""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class NextTaskGenerated(DomainEvent):
    event_type: ClassVar[str] = "chaining.next_generated"
    topic: ClassVar[str] = EventTopic.CHAINING.value

    parent_task_id: str
    new_task_id: str
    new_task_type: str
    trigger: str
    depth: int


@register_event
class RepairTaskCreated(DomainEvent):
    event_type: ClassVar[str] = "chaining.repair_created"
    topic: ClassVar[str] = EventTopic.CHAINING.value

    failed_task_id: str
    repair_task_id: str
    attempt: int
    depth: int


@register_event
class EscalationRaised(DomainEvent):
    event_type: ClassVar[str] = "chaining.escalation_raised"
    topic: ClassVar[str] = EventTopic.CHAINING.value

    task_id: str
    reason: str
    depth: int


@register_event
class ChainTerminated(DomainEvent):
    event_type: ClassVar[str] = "chaining.terminated"
    topic: ClassVar[str] = EventTopic.CHAINING.value

    root_task_id: str
    reason: str
    depth: int
