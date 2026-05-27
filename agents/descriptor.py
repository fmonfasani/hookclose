"""Agent descriptors — the registry's view of an agent."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from agents.capabilities import Capability


@dataclass(frozen=True, slots=True)
class AgentDescriptor:
    """Static metadata about an agent. Used by the registry and the API.

    The descriptor is *separate* from the agent instance: the runtime can
    introspect descriptors without instantiating expensive resources.
    """

    name: str
    version: str
    description: str
    capabilities: tuple[Capability, ...]
    requires: tuple[str, ...] = ()  # contract names this agent depends on
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
