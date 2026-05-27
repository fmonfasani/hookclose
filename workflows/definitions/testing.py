"""Autonomous testing workflow."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from workflows.base import WorkflowDefinition
from workflows.machine import StateMachine, Transition


class TestingInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repo: str
    ref: str
    framework: str
    selectors: tuple[str, ...] = ()


class TestingOutputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passed: int
    failed: int
    skipped: int
    coverage_pct: float | None = None


_MACHINE = StateMachine(
    name="testing",
    version="1.0.0",
    initial_state="materializing_env",
    states=frozenset(
        {
            "materializing_env",
            "installing_deps",
            "running_tests",
            "collecting_artifacts",
            "completed",
            "failed",
        },
    ),
    terminal_states=frozenset({"completed", "failed"}),
    transitions=(
        Transition("materializing_env", "installing_deps", "env_ready"),
        Transition("installing_deps", "running_tests", "deps_installed"),
        Transition("running_tests", "collecting_artifacts", "tests_done"),
        Transition("collecting_artifacts", "completed", "artifacts_persisted"),
        Transition("materializing_env", "failed", "env_unavailable"),
        Transition("installing_deps", "failed", "deps_failed"),
        Transition("running_tests", "failed", "runner_crashed"),
    ),
)


DEFINITION = WorkflowDefinition(
    name="testing",
    version="1.0.0",
    description="Run a project's test suite inside the sandbox and persist artifacts.",
    machine=_MACHINE,
    input_schema=TestingInputs,
    output_schema=TestingOutputs,
    tags=("testing", "autonomous"),
)
