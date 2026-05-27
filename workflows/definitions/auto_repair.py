"""Automated repair / self-healing workflow."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from workflows.base import WorkflowDefinition
from workflows.machine import StateMachine, Transition


class AutoRepairInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repo: str
    failing_signal: str  # test name, lint rule id, error fingerprint
    max_attempts: int = 3


class AutoRepairOutputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repaired: bool
    attempts_used: int
    final_diff_hash: str | None = None


_MACHINE = StateMachine(
    name="auto_repair",
    version="1.0.0",
    initial_state="diagnosing",
    states=frozenset(
        {
            "diagnosing",
            "proposing_patch",
            "applying_patch",
            "validating",
            "completed",
            "exhausted",
            "failed",
        },
    ),
    terminal_states=frozenset({"completed", "exhausted", "failed"}),
    transitions=(
        Transition("diagnosing", "proposing_patch", "diagnosis_ready"),
        Transition("proposing_patch", "applying_patch", "patch_proposed"),
        Transition("applying_patch", "validating", "patch_applied"),
        Transition("validating", "completed", "validation_passed"),
        Transition("validating", "diagnosing", "validation_failed_retry"),
        Transition("validating", "exhausted", "max_attempts_reached"),
        Transition("diagnosing", "failed", "diagnosis_unavailable"),
        Transition("applying_patch", "failed", "apply_failed"),
    ),
)


DEFINITION = WorkflowDefinition(
    name="auto_repair",
    version="1.0.0",
    description="Diagnose, patch, validate — iteratively, up to N attempts.",
    machine=_MACHINE,
    input_schema=AutoRepairInputs,
    output_schema=AutoRepairOutputs,
    tags=("repair", "autonomous"),
)
