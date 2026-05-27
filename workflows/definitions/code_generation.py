"""Code generation workflow — declarative state machine."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from workflows.base import WorkflowDefinition
from workflows.machine import StateMachine, Transition


class CodeGenerationInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repo: str
    target_branch: str
    spec_ref: str
    language: str


class CodeGenerationOutputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    branch: str
    commit_sha: str
    pr_number: int | None = None


_MACHINE = StateMachine(
    name="code_generation",
    version="1.0.0",
    initial_state="planning",
    states=frozenset(
        {
            "planning",
            "drafting",
            "self_reviewing",
            "validating",
            "committing",
            "completed",
            "failed",
        },
    ),
    terminal_states=frozenset({"completed", "failed"}),
    transitions=(
        Transition("planning", "drafting", "plan_ready"),
        Transition("drafting", "self_reviewing", "draft_ready"),
        Transition("self_reviewing", "drafting", "needs_revision"),
        Transition("self_reviewing", "validating", "draft_approved"),
        Transition("validating", "committing", "validation_passed"),
        Transition("validating", "drafting", "validation_failed"),
        Transition("committing", "completed", "commit_pushed"),
        Transition("planning", "failed", "plan_aborted"),
        Transition("drafting", "failed", "draft_aborted"),
        Transition("validating", "failed", "validation_exhausted"),
        Transition("committing", "failed", "commit_failed"),
    ),
)


DEFINITION = WorkflowDefinition(
    name="code_generation",
    version="1.0.0",
    description="Autonomous code generation: plan -> draft -> self-review -> validate -> commit.",
    machine=_MACHINE,
    input_schema=CodeGenerationInputs,
    output_schema=CodeGenerationOutputs,
    tags=("codegen", "autonomous"),
)
