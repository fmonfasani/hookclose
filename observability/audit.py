"""Audit trail — separate from logs.

Audit entries are *guaranteed* persistent and immutable. They answer
"who did what, when, to what". Adapters write them to the DB and forward to
the event bus.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class AuditEntry:
    actor: str
    action: str
    resource: str
    occurred_at: datetime
    correlation_id: str
    outcome: str  # "success" | "denied" | "error"
    attributes: Mapping[str, Any] = field(default_factory=dict)


class AuditTrailBase(ABC):
    @abstractmethod
    async def record(self, entry: AuditEntry) -> None:
        raise NotImplementedError
