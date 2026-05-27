"""Autonomous code-generation events."""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class CodeGenerationRequested(DomainEvent):
    event_type: ClassVar[str] = "codegen.requested"
    topic: ClassVar[str] = EventTopic.CODEGEN.value

    request_id: str
    repo: str
    target_branch: str
    spec_ref: str  # pointer to the spec in specs/ or external
    language: str


@register_event
class CodeGenerationCompleted(DomainEvent):
    event_type: ClassVar[str] = "codegen.completed"
    topic: ClassVar[str] = EventTopic.CODEGEN.value

    request_id: str
    repo: str
    branch: str
    commit_sha: str
    files_changed: int
    lines_added: int
    lines_removed: int


@register_event
class CodeGenerationFailed(DomainEvent):
    event_type: ClassVar[str] = "codegen.failed"
    topic: ClassVar[str] = EventTopic.CODEGEN.value

    request_id: str
    error_code: str
    error_message: str
    stage: str  # "planning" | "drafting" | "validating" | "committing"
