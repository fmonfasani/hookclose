"""Code executor port — compile/test/lint inside a sandbox."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    language: str
    entrypoint: Sequence[str]
    sources: Mapping[str, bytes]
    env: Mapping[str, str] = field(default_factory=dict)
    timeout_seconds: int = 60


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    diagnostics: Sequence[Mapping[str, str]] = field(default_factory=tuple)


@runtime_checkable
class CodeExecutorPort(Protocol):
    """Higher-level than SandboxPort: knows how to *run code*, not just
    commands. Implementations compose a sandbox + language toolchain."""

    async def execute(self, request: ExecutionRequest) -> ExecutionReport: ...

    async def run_tests(
        self,
        request: ExecutionRequest,
        *,
        framework: str,
    ) -> ExecutionReport: ...

    async def lint(
        self,
        request: ExecutionRequest,
        *,
        ruleset: str,
    ) -> ExecutionReport: ...
