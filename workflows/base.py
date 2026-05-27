"""Workflow definition and runtime-instance scaffolding."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from workflows.machine import StateMachine
from workflows.state import WorkflowState


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """Static, registry-addressable definition of a workflow.

    Implementations register concrete `WorkflowDefinition` objects through
    `runtime.registry`; the runtime never instantiates them by name guessing.
    """

    name: str
    version: str
    description: str
    machine: StateMachine
    input_schema: type  # Pydantic model — declared by consumers
    output_schema: type  # Pydantic model — declared by consumers
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class WorkflowInstance:
    """Runtime-side projection of a running workflow.

    The instance is rebuilt deterministically by replaying the episodic log;
    it is never the source of truth.
    """

    workflow_id: str
    definition: str
    definition_version: str
    correlation_id: str
    runtime_state: WorkflowState
    application_state: str
    created_at: datetime
    updated_at: datetime
    inputs: Mapping[str, Any]
    context: Mapping[str, Any] = field(default_factory=dict)
    outputs: Mapping[str, Any] | None = None
    error: Mapping[str, Any] | None = None
