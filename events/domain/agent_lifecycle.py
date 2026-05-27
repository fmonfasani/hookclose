"""Agent execution lifecycle events."""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class AgentInvoked(DomainEvent):
    event_type: ClassVar[str] = "agent.invoked"
    topic: ClassVar[str] = EventTopic.AGENT.value

    run_id: str
    workflow_id: str
    agent_name: str
    agent_version: str
    inputs_hash: str


@register_event
class AgentRunCompleted(DomainEvent):
    event_type: ClassVar[str] = "agent.run_completed"
    topic: ClassVar[str] = EventTopic.AGENT.value

    run_id: str
    agent_name: str
    duration_ms: int
    outputs_hash: str
    tokens_used: int | None = None


@register_event
class AgentRunFailed(DomainEvent):
    event_type: ClassVar[str] = "agent.run_failed"
    topic: ClassVar[str] = EventTopic.AGENT.value

    run_id: str
    agent_name: str
    error_code: str
    error_message: str
    retryable: bool
