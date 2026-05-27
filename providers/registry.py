"""ProviderRegistry — name-keyed catalog with capability lookup and ordering.

The registry holds providers; it does not invoke them. Ordering is deterministic:
higher ``weight`` first (so a last-resort local model sorts last), then cheaper
``cost_per_1k_tokens``, then name. This is the default order the manager fails over
through; the ComplexityRoutingEngine (Prompt 21) can supply an alternative order.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from providers.base import BaseProvider
from providers.state import Capability
from runtime.errors import ConfigurationError, NotFoundError


class ProviderRegistry:
    __slots__ = ("_providers",)

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider, *, replace: bool = False) -> None:
        if not replace and provider.name in self._providers:
            raise ConfigurationError(f"provider already registered: {provider.name!r}")
        self._providers[provider.name] = provider

    def get(self, name: str) -> BaseProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise NotFoundError(f"no provider registered: {name!r}") from exc

    def all(self) -> Sequence[BaseProvider]:
        return self._ordered(self._providers.values())

    def for_capability(self, capability: Capability) -> Sequence[BaseProvider]:
        """All providers supporting ``capability``, in default failover order."""
        return self._ordered(p for p in self._providers.values() if p.supports(capability))

    def names(self) -> tuple[str, ...]:
        return tuple(self._providers)

    @staticmethod
    def _ordered(providers: Iterable[BaseProvider]) -> tuple[BaseProvider, ...]:
        return tuple(
            sorted(
                providers,
                key=lambda p: (-p.profile.weight, p.profile.cost_per_1k_tokens, p.name),
            )
        )
