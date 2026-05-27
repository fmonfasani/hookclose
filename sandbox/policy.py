"""Resource and permission policies for sandboxed executions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from contracts.sandbox import SandboxPolicy

DEFAULT_POLICY: Final[SandboxPolicy] = SandboxPolicy(
    cpu_cores=1.0,
    memory_mb=1024,
    timeout_seconds=120,
    network="deny",
    filesystem="ephemeral",
    allow_subprocess=False,
    env={},
)


def build_policy(
    *,
    cpu_cores: float | None = None,
    memory_mb: int | None = None,
    timeout_seconds: int | None = None,
    network: str | None = None,
    filesystem: str | None = None,
    allow_subprocess: bool | None = None,
    env: Mapping[str, str] | None = None,
) -> SandboxPolicy:
    """Construct a policy by overriding fields on top of `DEFAULT_POLICY`."""
    return SandboxPolicy(
        cpu_cores=cpu_cores if cpu_cores is not None else DEFAULT_POLICY.cpu_cores,
        memory_mb=memory_mb if memory_mb is not None else DEFAULT_POLICY.memory_mb,
        timeout_seconds=(
            timeout_seconds if timeout_seconds is not None else DEFAULT_POLICY.timeout_seconds
        ),
        network=network if network is not None else DEFAULT_POLICY.network,
        filesystem=filesystem if filesystem is not None else DEFAULT_POLICY.filesystem,
        allow_subprocess=(
            allow_subprocess if allow_subprocess is not None else DEFAULT_POLICY.allow_subprocess
        ),
        env=dict(env) if env is not None else dict(DEFAULT_POLICY.env),
    )
