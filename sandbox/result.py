"""Sandbox execution outcomes."""

from __future__ import annotations

from dataclasses import dataclass

from contracts.sandbox import SandboxResult


@dataclass(frozen=True, slots=True)
class SandboxOutcome:
    """A wrapper that pairs a raw `SandboxResult` with derived signals."""

    result: SandboxResult
    artifacts: tuple[str, ...] = ()

    @property
    def success(self) -> bool:
        return (
            self.result.exit_code == 0 and not self.result.timed_out and not self.result.oom_killed
        )
