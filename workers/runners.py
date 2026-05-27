"""Command runners and a filesystem artifact store.

``LocalCommandRunner`` executes via an asyncio subprocess (the local-execution
fallback). ``DockerCommandRunner`` wraps any base runner with a ``docker run``
invocation for sandboxed execution. Both honor a timeout and never raise on a
non-zero exit — they translate everything into a :class:`CommandResult`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from pathlib import Path
import time

from workers.contracts import CommandResult

_TAIL = 4000  # max captured bytes per stream, to bound report/log size


class LocalCommandRunner:
    """Runs commands as local subprocesses. The default execution backend."""

    async def run(
        self,
        command: Sequence[str],
        *,
        cwd: str,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        start = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                env=dict(env) if env is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except (FileNotFoundError, OSError) as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            return CommandResult(exit_code=127, stdout="", stderr=str(exc), duration_ms=elapsed)

        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            elapsed = int((time.monotonic() - start) * 1000)
            return CommandResult(
                exit_code=124, stdout="", stderr="timed out", duration_ms=elapsed, timed_out=True
            )

        elapsed = int((time.monotonic() - start) * 1000)
        return CommandResult(
            exit_code=proc.returncode if proc.returncode is not None else -1,
            stdout=stdout_b.decode("utf-8", "replace")[-_TAIL:],
            stderr=stderr_b.decode("utf-8", "replace")[-_TAIL:],
            duration_ms=elapsed,
        )


class DockerCommandRunner:
    """Wraps a base runner to execute inside an ephemeral Docker container.

    Keeps the sandbox boundary explicit: network is disabled and the workspace is
    bind-mounted read-write at ``/workspace``. Requires a Docker daemon at runtime;
    falls back semantics are the caller's choice (inject ``LocalCommandRunner``).
    """

    def __init__(
        self, image: str, *, base: LocalCommandRunner | None = None, network: str = "none"
    ) -> None:
        self._image = image
        self._base = base or LocalCommandRunner()
        self._network = network

    async def run(
        self,
        command: Sequence[str],
        *,
        cwd: str,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        mount = f"{Path(cwd).resolve()}:/workspace:rw"
        env_flags: list[str] = []
        for key, value in (env or {}).items():
            env_flags.extend(["-e", f"{key}={value}"])
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            f"--network={self._network}",
            "-v",
            mount,
            "-w",
            "/workspace",
            *env_flags,
            self._image,
            *command,
        ]
        # The docker CLI itself runs locally; cwd is irrelevant to it.
        return await self._base.run(docker_cmd, cwd=cwd, timeout=timeout)


class FileArtifactStore:
    """Persists artifacts under ``<root>/<task_id>/<name>``."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    async def put(self, task_id: str, name: str, content: bytes) -> str:
        target = self._root / task_id / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target)
