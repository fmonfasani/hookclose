"""Agent registry — name-versioned lookup."""

from __future__ import annotations

from collections.abc import Iterator

from agents.descriptor import AgentDescriptor
from runtime.errors import ConfigurationError, NotFoundError


class AgentRegistry:
    """Registry of agent descriptors keyed by `(name, version)`.

    Concrete agent instances are constructed lazily by the runtime. Storing
    descriptors instead of instances keeps the registry cheap and discoverable.
    """

    __slots__ = ("_by_key",)

    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], AgentDescriptor] = {}

    def register(self, descriptor: AgentDescriptor) -> None:
        key = (descriptor.name, descriptor.version)
        if key in self._by_key:
            raise ConfigurationError(
                f"agent already registered: {descriptor.name}@{descriptor.version}"
            )
        self._by_key[key] = descriptor

    def get(self, name: str, version: str) -> AgentDescriptor:
        try:
            return self._by_key[(name, version)]
        except KeyError as exc:
            raise NotFoundError(f"agent not found: {name}@{version}") from exc

    def latest(self, name: str) -> AgentDescriptor:
        candidates = [d for (n, _v), d in self._by_key.items() if n == name]
        if not candidates:
            raise NotFoundError(f"no versions registered for agent: {name}")
        # Naive: lexicographic. Switch to semver compare when needed.
        return max(candidates, key=lambda d: d.version)

    def __iter__(self) -> Iterator[AgentDescriptor]:
        return iter(self._by_key.values())

    def __len__(self) -> int:
        return len(self._by_key)
