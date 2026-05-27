from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
import uuid

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    task_type: str = "generic"
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    provider: str = "opencode"
    attempts: int = 0
    max_attempts: int = 3
    error: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
