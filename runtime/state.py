"""Deterministic runtime-state persistence.

The runtime keeps a single, human-readable snapshot of where the build/operational
process currently stands. It is intentionally *file-backed* and *atomic* so that:

- restarts are reproducible (the runtime resumes from a known phase),
- progress is auditable (a plain-text diff shows what advanced),
- no hidden in-memory state drives orchestration decisions.

This module is the **only** sanctioned reader/writer of ``SYSTEM_STATE.json``.
It performs no I/O on import and never mutates global process state.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import tempfile
from typing import Literal

from pydantic import BaseModel, Field

RuntimePhase = Literal[
    "BOOTSTRAPPING",
    "RUNTIME_CORE",
    "PROVIDERS",
    "ROUTING",
    "WORKERS",
    "CHAINING",
    "SELF_HEALING",
    "CI_CD",
    "STABLE",
]

# Resolve the repository root relative to this file (runtime/state.py -> repo/).
_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = _REPO_ROOT / "SYSTEM_STATE.json"


class RuntimeState(BaseModel):
    """Persisted operational state of the runtime build process.

    Field order is stable and serialization is sorted so on-disk diffs stay
    minimal and review-friendly.
    """

    model_config = {"extra": "forbid"}

    current_phase: int = 1
    current_prompt: int = 1
    completed_prompts: list[int] = Field(default_factory=list)
    failed_prompts: list[int] = Field(default_factory=list)
    architecture_version: str = "v1"
    runtime_state: RuntimePhase = "BOOTSTRAPPING"
    updated_at: str | None = None

    def mark_completed(self, prompt: int) -> RuntimeState:
        """Return a copy with ``prompt`` recorded as completed (idempotent)."""
        completed = sorted({*self.completed_prompts, prompt})
        failed = [p for p in self.failed_prompts if p != prompt]
        return self.model_copy(
            update={
                "completed_prompts": completed,
                "failed_prompts": failed,
                "current_prompt": max(self.current_prompt, prompt + 1),
            }
        )

    def mark_failed(self, prompt: int) -> RuntimeState:
        """Return a copy with ``prompt`` recorded as failed (idempotent)."""
        failed = sorted({*self.failed_prompts, prompt})
        return self.model_copy(update={"failed_prompts": failed})

    def transition(self, phase: RuntimePhase) -> RuntimeState:
        """Return a copy moved into ``phase``."""
        return self.model_copy(update={"runtime_state": phase})


class RuntimeStateStore:
    """Atomic, file-backed store for :class:`RuntimeState`.

    Writes go to a temporary file in the same directory and are then
    ``os.replace``-d into place, which is atomic on POSIX and Windows. This
    guarantees readers never observe a partially written file.
    """

    def __init__(self, path: Path | str = DEFAULT_STATE_PATH) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> RuntimeState:
        """Load state from disk, returning defaults if the file is absent."""
        if not self._path.exists():
            return RuntimeState()
        raw = self._path.read_text(encoding="utf-8")
        return RuntimeState.model_validate_json(raw)

    def save(self, state: RuntimeState) -> RuntimeState:
        """Persist ``state`` atomically, stamping ``updated_at`` in UTC."""
        stamped = state.model_copy(
            update={"updated_at": datetime.now(UTC).isoformat(timespec="seconds")}
        )
        payload = json.dumps(stamped.model_dump(), indent=2, sort_keys=True) + "\n"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=".system_state-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self._path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
        return stamped

    def update(self, mutate: Callable[[RuntimeState], RuntimeState]) -> RuntimeState:
        """Load, apply ``mutate``, persist, and return the new state."""
        return self.save(mutate(self.load()))
