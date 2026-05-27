"""Provider value objects: capabilities, status, health, budget, profile.

All routing-relevant state lives here as small, explicit, typed objects so that
selection and failover are deterministic functions of data — never hidden flags.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


class Capability(StrEnum):
    """What a provider is good for. Routing matches tasks to capabilities."""

    ARCHITECTURE = "architecture"
    CODE_GENERATION = "code_generation"
    REVIEW = "review"
    ANALYSIS = "analysis"
    EXTRACTION = "extraction"
    EMBEDDING = "embedding"


class ProviderStatus(StrEnum):
    """Operational status of a provider."""

    AVAILABLE = "AVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    OFFLINE = "OFFLINE"
    COOLDOWN = "COOLDOWN"
    FAILED = "FAILED"


# Statuses from which a provider cannot currently serve traffic.
_UNAVAILABLE: frozenset[ProviderStatus] = frozenset(
    {
        ProviderStatus.RATE_LIMITED,
        ProviderStatus.OFFLINE,
        ProviderStatus.COOLDOWN,
        ProviderStatus.FAILED,
    }
)


@dataclass(frozen=True, slots=True)
class ProviderProfile:
    """Static configuration of a provider. Immutable; drives routing/scoring.

    ``cost_per_1k_tokens`` is a relative weight (cheaper = lower) used by the
    default ordering and by the ComplexityRoutingEngine. ``weight`` breaks ties
    (higher = preferred).
    """

    name: str
    capabilities: frozenset[Capability]
    cost_per_1k_tokens: float
    context_window: int
    weight: float = 1.0
    max_consecutive_failures: int = 3
    cooldown_seconds: float = 60.0
    credit_exhausted_cooldown_seconds: float = 1800.0
    daily_token_budget: int | None = None

    def supports(self, capability: Capability) -> bool:
        return capability in self.capabilities


@dataclass(slots=True)
class ProviderHealth:
    """Mutable runtime health of a provider. Snapshotted for persistence."""

    status: ProviderStatus = ProviderStatus.AVAILABLE
    consecutive_failures: int = 0
    cooldown_until: datetime | None = None
    tokens_used: int = 0
    total_requests: int = 0
    total_failures: int = 0
    last_error: str | None = None
    last_used_at: datetime | None = None

    def snapshot(self) -> ProviderHealth:
        """Return an independent copy (for persistence without aliasing)."""
        return replace(self)

    def remaining_budget(self, daily_token_budget: int | None) -> int | None:
        if daily_token_budget is None:
            return None
        return max(0, daily_token_budget - self.tokens_used)


@dataclass(frozen=True, slots=True)
class ProviderInvocation:
    """Result of a successful managed invocation."""

    provider: str
    content: str
    total_tokens: int
    attempts: int
    failed_over_from: tuple[str, ...] = field(default_factory=tuple)


def is_unavailable_status(status: ProviderStatus) -> bool:
    return status in _UNAVAILABLE
