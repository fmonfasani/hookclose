"""Unit tests for the OpenClawWorker (deterministic via a fake CommandRunner)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from events.base import DomainEvent
from tasks.models import Task
from workers.contracts import CommandResult, InMemoryArtifactStore, InMemoryTaskSource
from workers.openclaw import OpenClawWorker
from workers.workspace import WorkspaceManager

pytestmark = pytest.mark.unit


class FakeRunner:
    """Returns scripted results keyed by the first non-git command token.

    Git commands always 'succeed' so branch-per-task is exercised; other commands
    look up ``script`` by command[0], defaulting to success.
    """

    def __init__(self, script: dict[str, CommandResult] | None = None) -> None:
        self.script = script or {}
        self.calls: list[tuple[str, ...]] = []

    async def run(
        self,
        command: Sequence[str],
        *,
        cwd: str,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        cmd = tuple(command)
        self.calls.append(cmd)
        if cmd[0] == "git":
            return CommandResult(exit_code=0, stdout="", stderr="", duration_ms=1)
        key = cmd[0]
        return self.script.get(
            key, CommandResult(exit_code=0, stdout="ok", stderr="", duration_ms=2)
        )


class RecordingBus:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)

    async def publish_many(self, events: object) -> None:  # pragma: no cover
        raise NotImplementedError

    async def subscribe(self, *a: object, **k: object) -> object:  # pragma: no cover
        raise NotImplementedError

    async def unsubscribe(self, subscription_id: str) -> None:  # pragma: no cover
        raise NotImplementedError


def _worker(tmp: Path, runner: FakeRunner, **kw: object) -> OpenClawWorker:
    return OpenClawWorker(runner, WorkspaceManager(tmp / "ws", runner), **kw)  # type: ignore[arg-type]


def _task(**payload: object) -> Task:
    return Task(task_type="codegen.simple", provider="opencode", payload=payload, max_attempts=3)


async def test_successful_execution_runs_all_steps(tmp_path: Path) -> None:
    runner = FakeRunner()
    bus = RecordingBus()
    worker = _worker(tmp_path, runner, event_bus=bus)
    task = _task(
        patches=[{"path": "app.py", "content": "print('hi')\n"}],
        steps=[
            {"name": "lint", "command": ["ruff", "check", "."]},
            {"name": "test", "command": ["pytest", "-q"]},
        ],
    )

    report = await worker.execute(task)

    assert report.success
    assert [s.name for s in report.steps] == ["lint", "test"]
    assert (tmp_path / "ws" / task.id / "app.py").read_text() == "print('hi')\n"
    assert any(e.event_type == "worker.task_succeeded" for e in bus.events)


async def test_failing_step_stops_and_marks_failed(tmp_path: Path) -> None:
    runner = FakeRunner(
        {"pytest": CommandResult(exit_code=1, stdout="", stderr="1 failed", duration_ms=3)}
    )
    bus = RecordingBus()
    worker = _worker(tmp_path, runner, event_bus=bus)
    task = _task(
        steps=[
            {"name": "lint", "command": ["ruff", "check", "."]},
            {"name": "test", "command": ["pytest", "-q"]},
            {"name": "build", "command": ["echo", "never"]},
        ],
        timeout=5,
    )
    task.max_attempts = 1

    report = await worker.execute(task)

    assert not report.success
    assert report.failed_step == "test"
    assert [s.name for s in report.steps] == ["lint", "test"]  # build never runs
    assert any(e.event_type == "worker.task_failed" for e in bus.events)


async def test_retries_until_max_attempts(tmp_path: Path) -> None:
    runner = FakeRunner(
        {"pytest": CommandResult(exit_code=1, stdout="", stderr="fail", duration_ms=1)}
    )
    bus = RecordingBus()
    worker = _worker(tmp_path, runner, event_bus=bus)
    task = _task(steps=[{"name": "test", "command": ["pytest"]}])
    task.max_attempts = 3

    report = await worker.execute(task)

    assert not report.success
    assert report.attempts == 3
    retries = [e for e in bus.events if e.event_type == "worker.task_retry_scheduled"]
    assert len(retries) == 2  # retries between the 3 attempts


async def test_branch_per_task_naming(tmp_path: Path) -> None:
    runner = FakeRunner()
    worker = _worker(tmp_path, runner)
    task = _task(steps=[{"name": "noop", "command": ["true"]}])

    report = await worker.execute(task)
    assert report.branch == f"task/{task.id[:12]}"
    assert any(c[:2] == ("git", "init") for c in runner.calls)


async def test_report_artifact_is_persisted(tmp_path: Path) -> None:
    runner = FakeRunner()
    store = InMemoryArtifactStore()
    worker = _worker(tmp_path, runner, artifact_store=store)
    task = _task(steps=[{"name": "noop", "command": ["true"]}])

    report = await worker.execute(task)
    assert report.artifacts
    assert any(k.endswith("report-attempt-1.json") for k in store.stored)


async def test_path_traversal_in_patch_is_rejected(tmp_path: Path) -> None:
    runner = FakeRunner()
    worker = _worker(tmp_path, runner)
    task = _task(patches=[{"path": "../escape.py", "content": "x"}], steps=[])
    task.max_attempts = 1

    with pytest.raises(ValueError, match="escapes workspace"):
        await worker.execute(task)


async def test_consume_drains_source(tmp_path: Path) -> None:
    runner = FakeRunner()
    worker = _worker(tmp_path, runner)
    source = InMemoryTaskSource(
        tasks=[_task(steps=[{"name": "noop", "command": ["true"]}]) for _ in range(2)]
    )

    await worker.run_forever(source)
    assert source.tasks == []
    assert await worker.consume_once(source) is None
