"""Worker-level contracts: command execution, reports, sources, artifact stores.

These ports keep the workers testable and vendor-agnostic: the OpenClawWorker
depends only on a ``CommandRunner`` (local subprocess or Docker), a ``TaskSource``
(in-memory or Redis), and an ``ArtifactStore`` (filesystem or in-memory).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from tasks.models import Task


@dataclass(frozen=True, slots=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


@runtime_checkable
class CommandRunner(Protocol):
    """Runs a command in a working directory. Implementations: local subprocess,
    Docker sandbox. MUST enforce ``timeout`` and never raise on non-zero exit."""

    async def run(
        self,
        command: Sequence[str],
        *,
        cwd: str,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult: ...


@dataclass(frozen=True, slots=True)
class FilePatch:
    """A file to materialize into the workspace before execution."""

    path: str  # relative to workspace root
    content: str


@dataclass(frozen=True, slots=True)
class StepResult:
    name: str
    command: tuple[str, ...]
    exit_code: int
    success: bool
    duration_ms: int
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    task_id: str
    worker: str
    branch: str
    success: bool
    attempts: int
    steps: tuple[StepResult, ...] = ()
    artifacts: tuple[str, ...] = ()
    error: str | None = None
    failed_step: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "worker": self.worker,
            "branch": self.branch,
            "success": self.success,
            "attempts": self.attempts,
            "error": self.error,
            "failed_step": self.failed_step,
            "steps": [
                {
                    "name": s.name,
                    "command": list(s.command),
                    "exit_code": s.exit_code,
                    "success": s.success,
                    "duration_ms": s.duration_ms,
                    "stdout_tail": s.stdout_tail,
                    "stderr_tail": s.stderr_tail,
                }
                for s in self.steps
            ],
            "artifacts": list(self.artifacts),
        }


@runtime_checkable
class TaskSource(Protocol):
    """Where a worker claims tasks from (Redis queue, in-memory, …)."""

    async def claim(self) -> Task | None: ...


@runtime_checkable
class ArtifactStore(Protocol):
    """Durable storage for execution artifacts (reports, logs, patches)."""

    async def put(self, task_id: str, name: str, content: bytes) -> str: ...


@dataclass(slots=True)
class InMemoryTaskSource:
    """Deterministic task source backed by a list (FIFO)."""

    tasks: list[Task] = field(default_factory=list)

    async def claim(self) -> Task | None:
        return self.tasks.pop(0) if self.tasks else None


@dataclass(slots=True)
class InMemoryArtifactStore:
    """Captures artifacts in memory; returns a synthetic URI."""

    stored: dict[str, bytes] = field(default_factory=dict)

    async def put(self, task_id: str, name: str, content: bytes) -> str:
        key = f"{task_id}/{name}"
        self.stored[key] = content
        return f"mem://{key}"
