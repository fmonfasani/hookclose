"""Workflow engine port — drives deterministic state machines."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from workflows.state import WorkflowState


@dataclass(frozen=True, slots=True)
class WorkflowHandle:
    workflow_id: str
    definition: str
    version: str
    state: WorkflowState
    correlation_id: str


@runtime_checkable
class WorkflowEnginePort(Protocol):
    """Starts, advances, suspends and resumes workflow instances.

    The engine itself is **deterministic**: given the same event log, replaying
    against the same definition MUST produce the same state.
    """

    async def start(
        self,
        definition: str,
        inputs: Mapping[str, Any],
        *,
        correlation_id: str,
    ) -> WorkflowHandle: ...

    async def signal(
        self,
        workflow_id: str,
        signal: str,
        payload: Mapping[str, Any] | None = None,
    ) -> WorkflowHandle: ...

    async def get(self, workflow_id: str) -> WorkflowHandle: ...

    async def cancel(self, workflow_id: str, reason: str) -> WorkflowHandle: ...
