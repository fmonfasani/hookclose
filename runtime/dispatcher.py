"""Workflow dispatcher contract — interprets state machines.

The dispatcher's only job is to advance a workflow from one declared state to
the next, in response to triggers. It is the *deterministic* center of the
system. LLM calls are made by agents *inside* states, not by the dispatcher.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from workflows.base import WorkflowDefinition, WorkflowInstance


@runtime_checkable
class DispatcherPort(Protocol):
    async def advance(
        self,
        instance: WorkflowInstance,
        trigger: str,
        payload: Mapping[str, Any] | None = None,
    ) -> WorkflowInstance: ...

    async def replay(
        self,
        definition: WorkflowDefinition,
        instance_id: str,
    ) -> WorkflowInstance: ...
