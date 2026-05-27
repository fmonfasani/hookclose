"""Automated code-review events."""

from __future__ import annotations

from typing import ClassVar, Literal

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class CodeReviewRequested(DomainEvent):
    event_type: ClassVar[str] = "review.requested"
    topic: ClassVar[str] = EventTopic.REVIEW.value

    review_id: str
    repo: str
    pr_number: int
    head_sha: str
    reviewer_profile: str  # name of the reviewer agent / persona


@register_event
class ReviewFindingProduced(DomainEvent):
    event_type: ClassVar[str] = "review.finding_produced"
    topic: ClassVar[str] = EventTopic.REVIEW.value

    review_id: str
    file_path: str
    line: int | None
    severity: Literal["info", "low", "medium", "high", "critical"]
    rule: str
    summary: str


@register_event
class CodeReviewCompleted(DomainEvent):
    event_type: ClassVar[str] = "review.completed"
    topic: ClassVar[str] = EventTopic.REVIEW.value

    review_id: str
    decision: Literal["approve", "request_changes", "comment"]
    findings_total: int
    duration_ms: int
