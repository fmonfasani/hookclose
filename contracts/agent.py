"""Agent port — the contract every specialized agent must satisfy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class AgentRunContext:
    """Immutable execution context passed to every agent invocation.

    The context is what makes runs **reproducible**: the same context + same
    inputs must produce semantically equivalent outputs.
    """

    run_id: str
    workflow_id: str
    correlation_id: str
    tenant_id: str | None
    actor: str
    deadline_unix_ms: int | None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class AgentPort(Protocol):
    """An agent is a capability-bound, side-effect-aware unit of work.

    Agents are stateless from the runtime's perspective: any persistent state
    must be loaded from `memory/` and written back through the same port.
    """

    name: str
    version: str

    async def execute(
        self,
        inputs: Mapping[str, Any],
        context: AgentRunContext,
    ) -> Mapping[str, Any]:
        """Execute the agent against the given inputs.

        MUST NOT raise on business-domain failures — return a structured
        result instead. MAY raise on infrastructure failures (cancelled,
        sandbox unavailable, etc.).
        """
        ...

    async def emit(self, event: DomainEvent) -> None:
        """Emit a domain event during execution. Implementation forwards to
        the event bus injected by the runtime."""
        ...
