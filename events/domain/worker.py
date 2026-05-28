"""Worker execution events — emitted by execution workers (e.g. OpenClaw).

Workers execute tasks; they do not drive workflows. These events let the rest of
the runtime observe and react to execution progress without coupling.
"""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class TaskExecutionStarted(DomainEvent):
    event_type: ClassVar[str] = "worker.task_started"
    topic: ClassVar[str] = EventTopic.WORKER.value

    task_id: str
    task_type: str
    worker: str
    branch: str
    attempt: int


@register_event
class TaskCodeGenerated(DomainEvent):
    event_type: ClassVar[str] = "worker.code_generated"
    topic: ClassVar[str] = EventTopic.WORKER.value

    task_id: str
    provider: str
    files: int
    total_tokens: int


@register_event
class TaskStepCompleted(DomainEvent):
    event_type: ClassVar[str] = "worker.step_completed"
    topic: ClassVar[str] = EventTopic.WORKER.value

    task_id: str
    step: str
    exit_code: int
    success: bool
    duration_ms: int


@register_event
class TaskExecutionSucceeded(DomainEvent):
    event_type: ClassVar[str] = "worker.task_succeeded"
    topic: ClassVar[str] = EventTopic.WORKER.value

    task_id: str
    worker: str
    branch: str
    attempts: int
    artifacts: tuple[str, ...]


@register_event
class TaskExecutionFailed(DomainEvent):
    event_type: ClassVar[str] = "worker.task_failed"
    topic: ClassVar[str] = EventTopic.WORKER.value

    task_id: str
    worker: str
    failed_step: str
    attempts: int
    error: str


@register_event
class TaskRetryScheduled(DomainEvent):
    event_type: ClassVar[str] = "worker.task_retry_scheduled"
    topic: ClassVar[str] = EventTopic.WORKER.value

    task_id: str
    attempt: int
    max_attempts: int
    reason: str
