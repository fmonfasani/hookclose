"""OpenClawWorker — persistent task execution runtime.

OpenClaw *executes tasks*; it does not control workflows or decide architecture.
For each task it:

  1. creates a branch-per-task workspace,
  2. materializes the task's file patches,
  3. runs the configured steps (lint, tests, …) inside a CommandRunner
     (local subprocess or Docker sandbox),
  4. retries the whole execution up to ``task.max_attempts`` on failure,
  5. persists a JSON report artifact,
  6. emits worker events for every started/step/succeeded/failed/retry transition.

The step plan is data-driven from ``task.payload`` (no hardcoded vendor logic):

    payload = {
        "patches": [{"path": "app.py", "content": "..."}],
        "steps": [{"name": "lint", "command": ["ruff", "check", "."]},
                  {"name": "test", "command": ["pytest", "-q"]}],
        "timeout": 120,
    }
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import json
from typing import cast

from contracts.event_bus import EventBusPort
from events.base import DomainEvent
from events.domain.worker import (
    TaskExecutionFailed,
    TaskExecutionStarted,
    TaskExecutionSucceeded,
    TaskRetryScheduled,
    TaskStepCompleted,
)
from tasks.models import Task
from workers.contracts import (
    ArtifactStore,
    CommandRunner,
    ExecutionReport,
    FilePatch,
    StepResult,
    TaskSource,
)
from workers.workspace import WorkspaceManager

_DEFAULT_TIMEOUT = 120.0


class OpenClawWorker:
    name = "openclaw"

    def __init__(
        self,
        runner: CommandRunner,
        workspaces: WorkspaceManager,
        *,
        artifact_store: ArtifactStore | None = None,
        event_bus: EventBusPort | None = None,
    ) -> None:
        self._runner = runner
        self._workspaces = workspaces
        self._artifacts = artifact_store
        self._bus = event_bus

    # --- public API --------------------------------------------------------

    async def execute(self, task: Task) -> ExecutionReport:
        """Execute one task with bounded retries; returns the final report."""
        max_attempts = max(1, task.max_attempts)
        report: ExecutionReport | None = None
        for attempt in range(1, max_attempts + 1):
            report = await self._execute_once(task, attempt)
            if report.success:
                return report
            if attempt < max_attempts:
                await self._emit(
                    TaskRetryScheduled(
                        task_id=task.id,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        reason=report.failed_step or "execution failed",
                    )
                )
        if report is None:  # unreachable: the loop runs at least once
            raise RuntimeError("no execution attempt was made")
        return report

    async def consume_once(self, source: TaskSource) -> ExecutionReport | None:
        """Claim a single task from ``source`` and execute it (or return None)."""
        task = await source.claim()
        if task is None:
            return None
        return await self.execute(task)

    async def run_forever(
        self, source: TaskSource, *, stop: Callable[[], bool] | None = None
    ) -> None:
        """Drain ``source`` until empty (or ``stop`` returns True). Watchdog-friendly."""
        while stop is None or not stop():
            report = await self.consume_once(source)
            if report is None:
                return

    # --- internals ---------------------------------------------------------

    async def _execute_once(self, task: Task, attempt: int) -> ExecutionReport:
        workspace = await self._workspaces.create(task.id)
        await self._emit(
            TaskExecutionStarted(
                task_id=task.id,
                task_type=task.task_type,
                worker=self.name,
                branch=workspace.branch,
                attempt=attempt,
            )
        )

        patches = [FilePatch(path=p["path"], content=p["content"]) for p in _patches(task)]
        workspace.write_patches(patches)

        timeout = float(task.payload.get("timeout", _DEFAULT_TIMEOUT))
        steps: list[StepResult] = []
        failed_step: str | None = None

        for spec in _steps(task):
            command = tuple(str(c) for c in cast("Sequence[object]", spec["command"]))
            result = await self._runner.run(list(command), cwd=str(workspace.root), timeout=timeout)
            step = StepResult(
                name=str(spec["name"]),
                command=command,
                exit_code=result.exit_code,
                success=result.success,
                duration_ms=result.duration_ms,
                stdout_tail=result.stdout[-600:],
                stderr_tail=result.stderr[-600:],
            )
            steps.append(step)
            await self._emit(
                TaskStepCompleted(
                    task_id=task.id,
                    step=step.name,
                    exit_code=step.exit_code,
                    success=step.success,
                    duration_ms=step.duration_ms,
                )
            )
            if not step.success:
                failed_step = step.name
                break

        success = failed_step is None
        artifacts = await self._persist_report(
            task, workspace.branch, success, attempt, steps, failed_step
        )

        report = ExecutionReport(
            task_id=task.id,
            worker=self.name,
            branch=workspace.branch,
            success=success,
            attempts=attempt,
            steps=tuple(steps),
            artifacts=artifacts,
            failed_step=failed_step,
            error=None if success else f"step {failed_step!r} failed",
        )

        if success:
            await self._emit(
                TaskExecutionSucceeded(
                    task_id=task.id,
                    worker=self.name,
                    branch=workspace.branch,
                    attempts=attempt,
                    artifacts=artifacts,
                )
            )
        else:
            await self._emit(
                TaskExecutionFailed(
                    task_id=task.id,
                    worker=self.name,
                    failed_step=failed_step or "unknown",
                    attempts=attempt,
                    error=report.error or "execution failed",
                )
            )
        return report

    async def _persist_report(
        self,
        task: Task,
        branch: str,
        success: bool,
        attempt: int,
        steps: Sequence[StepResult],
        failed_step: str | None,
    ) -> tuple[str, ...]:
        if self._artifacts is None:
            return ()
        report = ExecutionReport(
            task_id=task.id,
            worker=self.name,
            branch=branch,
            success=success,
            attempts=attempt,
            steps=tuple(steps),
            failed_step=failed_step,
        )
        payload = json.dumps(report.to_dict(), indent=2, sort_keys=True).encode("utf-8")
        uri = await self._artifacts.put(task.id, f"report-attempt-{attempt}.json", payload)
        return (uri,)

    async def _emit(self, event: DomainEvent) -> None:
        if self._bus is not None:
            await self._bus.publish(event)


def _patches(task: Task) -> list[dict[str, str]]:
    raw = task.payload.get("patches", [])
    return list(raw) if isinstance(raw, list) else []


def _steps(task: Task) -> list[dict[str, object]]:
    raw = task.payload.get("steps", [])
    return list(raw) if isinstance(raw, list) else []
