"""
sandbox/ — Isolated execution boundary.

The sandbox is the runtime's *trust boundary*. Anything the platform did not
write goes inside one. The package declares:
  - the policy schema (resource limits, network policy, FS policy)
  - result types
  - the abstract runner base class

Concrete backends (docker, gVisor, firecracker, …) live in `adapters/sandbox/`.
"""

from sandbox.base import SandboxBase
from sandbox.policy import DEFAULT_POLICY, build_policy
from sandbox.result import SandboxOutcome

__all__ = ["DEFAULT_POLICY", "SandboxBase", "SandboxOutcome", "build_policy"]
