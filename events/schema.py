"""Event topic catalog and global registry.

Every event type registers itself here so the event bus can route by topic
without importing concrete classes. Topics are stable strings; do not rename
them lightly — bump `event_version` instead.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from events.base import DomainEvent


class EventTopic(StrEnum):
    """Stable wire-level topics. Add new entries; never repurpose old ones."""

    WORKFLOW = "aine.workflow"
    AGENT = "aine.agent"
    CODEGEN = "aine.codegen"
    REVIEW = "aine.review"
    TESTING = "aine.testing"
    REPAIR = "aine.repair"
    MEMORY = "aine.memory"
    SCHEDULER = "aine.scheduler"


EVENT_REGISTRY: Final[dict[str, type[DomainEvent]]] = {}


def register_event(cls: type[DomainEvent]) -> type[DomainEvent]:
    """Decorator that adds a concrete event class to the registry."""
    key = f"{cls.event_type}@{cls.event_version}"
    if key in EVENT_REGISTRY and EVENT_REGISTRY[key] is not cls:
        raise RuntimeError(f"Duplicate event registration: {key}")
    EVENT_REGISTRY[key] = cls
    return cls
