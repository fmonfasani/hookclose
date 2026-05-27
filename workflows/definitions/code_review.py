"""Code review workflow."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from workflows.base import WorkflowDefinition
from workflows.machine import StateMachine, Transition


class CodeReviewInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repo: str
    pr_number: int
    reviewer_profile: str


class CodeReviewOutputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "request_changes", "comment"]
    findings_total: int


_MACHINE = StateMachine(
    name="code_review",
    version="1.0.0",
    initial_state="collecting_diff",
    states=frozenset(
        {
            "collecting_diff",
            "analyzing",
            "synthesizing_findings",
            "publishing",
            "completed",
            "failed",
        },
    ),
    terminal_states=frozenset({"completed", "failed"}),
    transitions=(
        Transition("collecting_diff", "analyzing", "diff_collected"),
        Transition("analyzing", "synthesizing_findings", "analysis_done"),
        Transition("synthesizing_findings", "publishing", "findings_ready"),
        Transition("publishing", "completed", "published"),
        Transition("collecting_diff", "failed", "diff_unavailable"),
        Transition("analyzing", "failed", "analysis_failed"),
        Transition("publishing", "failed", "publish_failed"),
    ),
)


DEFINITION = WorkflowDefinition(
    name="code_review",
    version="1.0.0",
    description="Automated code review for a pull request.",
    machine=_MACHINE,
    input_schema=CodeReviewInputs,
    output_schema=CodeReviewOutputs,
    tags=("review", "autonomous"),
)
