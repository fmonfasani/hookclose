"""Task runner port — deferred/durable work outside the request path."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class TaskHandle:
    task_id: str
    queue: str
    submitted_at: datetime


@runtime_checkable
class TaskRunnerPort(Protocol):
    """Submits work to the durable task runner (Celery adapter)."""

    async def enqueue(
        self,
        task_name: str,
        payload: Mapping[str, Any],
        *,
        queue: str | None = None,
        eta: datetime | None = None,
        priority: int | None = None,
        correlation_id: str | None = None,
    ) -> TaskHandle: ...

    async def cancel(self, task_id: str) -> bool: ...

    async def status(self, task_id: str) -> str: ...
