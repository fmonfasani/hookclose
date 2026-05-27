"""Self-healing events (failure analysis, repair decisions, rollback, escalation).

Complements the existing repair.* events with the decision/observability layer of
the SelfHealingRuntime. Same REPAIR topic so consumers subscribe in one place.
"""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class FailureAnalyzed(DomainEvent):
    event_type: ClassVar[str] = "healing.failure_analyzed"
    topic: ClassVar[str] = EventTopic.REPAIR.value

    task_id: str
    category: str
    signature_key: str
    deterministic_fixable: bool
    occurrences: int


@register_event
class RepairDecisionMade(DomainEvent):
    event_type: ClassVar[str] = "healing.repair_decided"
    topic: ClassVar[str] = EventTopic.REPAIR.value

    task_id: str
    action: str
    attempt: int
    reason: str


@register_event
class RolledBack(DomainEvent):
    event_type: ClassVar[str] = "healing.rolled_back"
    topic: ClassVar[str] = EventTopic.REPAIR.value

    task_id: str
    to_ref: str
    reason: str


@register_event
class RepairEscalated(DomainEvent):
    event_type: ClassVar[str] = "healing.escalated"
    topic: ClassVar[str] = EventTopic.REPAIR.value

    task_id: str
    reason: str
    attempts: int
