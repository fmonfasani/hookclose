"""Sandbox port — isolated execution boundary for AI-generated code."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    cpu_cores: float
    memory_mb: int
    timeout_seconds: int
    network: str  # "deny" | "allow" | "egress-only"
    filesystem: str  # "ephemeral" | "readonly" | "scoped-rw"
    allow_subprocess: bool = False
    env: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool
    oom_killed: bool


@runtime_checkable
class SandboxPort(Protocol):
    """Runs untrusted code inside a strict resource/permission boundary."""

    async def run(
        self,
        image: str,
        command: Sequence[str],
        *,
        policy: SandboxPolicy,
        workdir: str | None = None,
        files: Mapping[str, bytes] | None = None,
    ) -> SandboxResult: ...
