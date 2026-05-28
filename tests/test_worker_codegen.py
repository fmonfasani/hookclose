"""Unit tests for the worker code-generation phase (deterministic, no network)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path

import pytest

from contracts.llm_provider import LLMRequest, LLMResponse, LLMUsage
from providers.base import BaseProvider
from providers.manager import ProviderManager
from providers.registry import ProviderRegistry
from providers.state import Capability, ProviderProfile
from tasks.models import Task
from workers.codegen import CodeGenerator
from workers.contracts import CommandResult
from workers.openclaw import OpenClawWorker
from workers.workspace import WorkspaceManager

pytestmark = pytest.mark.unit


class _CannedProvider(BaseProvider):
    def __init__(self, content: str) -> None:
        super().__init__(
            ProviderProfile(
                name="canned",
                capabilities=frozenset({Capability.CODE_GENERATION}),
                cost_per_1k_tokens=1.0,
                context_window=100_000,
            )
        )
        self._content = content

    async def _invoke(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            model="canned",
            content=self._content,
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )


def _manager(content: str) -> ProviderManager:
    reg = ProviderRegistry()
    reg.register(_CannedProvider(content))
    return ProviderManager(reg)


def _files_json(*files: tuple[str, str]) -> str:
    return json.dumps({"files": [{"path": p, "content": c} for p, c in files], "notes": "ok"})


class FakeRunner:
    def __init__(self, script: dict[str, CommandResult] | None = None) -> None:
        self.script = script or {}

    async def run(
        self,
        command: Sequence[str],
        *,
        cwd: str,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        cmd = tuple(command)
        if cmd[0] == "git":
            return CommandResult(exit_code=0, stdout="", stderr="", duration_ms=1)
        return self.script.get(
            cmd[0], CommandResult(exit_code=0, stdout="ok", stderr="", duration_ms=1)
        )


def _worker(tmp: Path, content: str, runner: FakeRunner | None = None) -> OpenClawWorker:
    runner = runner or FakeRunner()
    return OpenClawWorker(
        runner,  # type: ignore[arg-type]
        WorkspaceManager(tmp / "ws", runner),  # type: ignore[arg-type]
        generator=CodeGenerator(_manager(content)),
    )


# --- generator parsing -----------------------------------------------------


async def test_generator_parses_files() -> None:
    gen = CodeGenerator(_manager(_files_json(("app.py", "print('hi')\n"), ("README.md", "# x"))))
    result = await gen.generate("build a hello app")
    assert [p.path for p in result.patches] == ["app.py", "README.md"]
    assert not result.degraded
    assert result.total_tokens == 30


async def test_generator_degrades_on_bad_json() -> None:
    gen = CodeGenerator(_manager("not json"))
    result = await gen.generate("x")
    assert result.degraded
    assert result.patches == ()


async def test_generator_skips_malformed_entries() -> None:
    content = json.dumps({"files": [{"path": "ok.py", "content": "x"}, {"path": 123}, "junk"]})
    gen = CodeGenerator(_manager(content))
    result = await gen.generate("x")
    assert [p.path for p in result.patches] == ["ok.py"]


# --- worker integration ----------------------------------------------------


async def test_worker_generates_files_then_runs_steps(tmp_path: Path) -> None:
    worker = _worker(tmp_path, _files_json(("app.py", "print('generated')\n")))
    task = Task(
        task_type="codegen.feature",
        payload={
            "generate": {"goal": "write app.py that prints generated"},
            "steps": [{"name": "test", "command": ["pytest", "-q"]}],
        },
        max_attempts=1,
    )

    report = await worker.execute(task)

    assert report.success
    assert (tmp_path / "ws" / task.id / "app.py").read_text() == "print('generated')\n"
    assert [s.name for s in report.steps] == ["generate", "test"]


async def test_generation_failure_skips_steps_and_fails(tmp_path: Path) -> None:
    worker = _worker(tmp_path, "garbage not json")  # generator degrades
    task = Task(
        task_type="codegen.x",
        payload={
            "generate": {"goal": "x"},
            "steps": [{"name": "test", "command": ["pytest"]}],
        },
        max_attempts=1,
    )

    report = await worker.execute(task)

    assert not report.success
    assert report.failed_step == "generate"
    assert [s.name for s in report.steps] == ["generate"]  # test never ran


async def test_no_provider_makes_generation_step_fail(tmp_path: Path) -> None:
    runner = FakeRunner()
    worker = OpenClawWorker(
        runner,  # type: ignore[arg-type]
        WorkspaceManager(tmp_path / "ws", runner),  # type: ignore[arg-type]
        generator=CodeGenerator(
            ProviderManager(ProviderRegistry())
        ),  # empty -> NoProviderAvailable
    )
    task = Task(task_type="codegen.x", payload={"generate": {"goal": "x"}}, max_attempts=1)

    report = await worker.execute(task)
    assert not report.success
    assert report.failed_step == "generate"


async def test_worker_without_generate_spec_is_unchanged(tmp_path: Path) -> None:
    # Backward-compat: no "generate" key -> behaves like before (static patches only).
    worker = _worker(tmp_path, _files_json())  # generator present but unused
    task = Task(
        task_type="codegen.x",
        payload={
            "patches": [{"path": "static.txt", "content": "hi"}],
            "steps": [{"name": "noop", "command": ["true"]}],
        },
        max_attempts=1,
    )
    report = await worker.execute(task)
    assert report.success
    assert [s.name for s in report.steps] == ["noop"]  # no generate step
    assert (tmp_path / "ws" / task.id / "static.txt").read_text() == "hi"
