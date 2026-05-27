"""Workflow lifecycle events."""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class WorkflowStarted(DomainEvent):
    event_type: ClassVar[str] = "workflow.started"
    topic: ClassVar[str] = EventTopic.WORKFLOW.value

    workflow_id: str
    definition: str
    definition_version: str
    inputs_hash: str


@register_event
class WorkflowStateTransitioned(DomainEvent):
    event_type: ClassVar[str] = "workflow.state_transitioned"
    topic: ClassVar[str] = EventTopic.WORKFLOW.value

    workflow_id: str
    from_state: str
    to_state: str
    trigger: str


@register_event
class WorkflowCompleted(DomainEvent):
    event_type: ClassVar[str] = "workflow.completed"
    topic: ClassVar[str] = EventTopic.WORKFLOW.value

    workflow_id: str
    outputs_hash: str
    duration_ms: int


@register_event
class WorkflowFailed(DomainEvent):
    event_type: ClassVar[str] = "workflow.failed"
    topic: ClassVar[str] = EventTopic.WORKFLOW.value

    workflow_id: str
    failed_state: str
    error_code: str
    error_message: str


@register_event
class WorkflowCancelled(DomainEvent):
    event_type: ClassVar[str] = "workflow.cancelled"
    topic: ClassVar[str] = EventTopic.WORKFLOW.value

    workflow_id: str
    reason: str
