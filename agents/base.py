"""Abstract base for agent implementations.

This is *only* a shape contract. No execution logic lives here — concrete
agents will be added in future commits.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from contracts.agent import AgentRunContext
from events.base import DomainEvent


class AgentBase(ABC):
    """Inherit from this to build an agent.

    Implementations MUST:
      - declare `name` and `version` as class-level attributes
      - implement `execute()`
      - never read environment variables directly — everything comes through
        the injected dependencies
    """

    name: str
    version: str

    @abstractmethod
    async def execute(
        self,
        inputs: Mapping[str, Any],
        context: AgentRunContext,
    ) -> Mapping[str, Any]:
        raise NotImplementedError

    async def emit(self, event: DomainEvent) -> None:
        raise NotImplementedError("event bus is injected by the runtime")
