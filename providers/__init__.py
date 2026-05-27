"""Vendor-agnostic provider subsystem.

The runtime never talks to a vendor directly. It asks the :class:`ProviderManager`
to serve a *capability*; the manager selects, invokes, and fails over across
registered providers, persisting health and emitting events for every decision.
"""

from __future__ import annotations

# Importing the events module registers provider events in the global EVENT_REGISTRY.
import events.domain.provider
from providers.base import BaseProvider
from providers.errors import (
    NoProviderAvailable,
    ProviderCreditExhausted,
    ProviderError,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from providers.implementations import (
    ClaudeProvider,
    GeminiProvider,
    LocalProvider,
    OpenCodeProvider,
)
from providers.manager import ProviderManager
from providers.persistence import (
    InMemoryProviderStateStore,
    ProviderStateStore,
    RedisProviderStateStore,
)
from providers.registry import ProviderRegistry
from providers.routing import (
    ComplexityRoutingEngine,
    RoutingDecision,
    RoutingPolicy,
    RoutingRequest,
    TaskComplexity,
)
from providers.state import (
    Capability,
    ProviderHealth,
    ProviderInvocation,
    ProviderProfile,
    ProviderStatus,
)

__all__ = [
    "BaseProvider",
    "Capability",
    "ClaudeProvider",
    "ComplexityRoutingEngine",
    "GeminiProvider",
    "InMemoryProviderStateStore",
    "LocalProvider",
    "NoProviderAvailable",
    "OpenCodeProvider",
    "ProviderCreditExhausted",
    "ProviderError",
    "ProviderHealth",
    "ProviderInvocation",
    "ProviderManager",
    "ProviderProfile",
    "ProviderRateLimited",
    "ProviderRegistry",
    "ProviderStateStore",
    "ProviderStatus",
    "ProviderTimeout",
    "ProviderUnavailable",
    "RedisProviderStateStore",
    "RoutingDecision",
    "RoutingPolicy",
    "RoutingRequest",
    "TaskComplexity",
]
