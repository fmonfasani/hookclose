"""BaseProvider — a vendor wrapped with health, cooldown, and budget logic.

A provider is the runtime's unit of failover. It owns its own ``ProviderHealth``
and translates the outcome of an invocation into deterministic state transitions:

    success            -> AVAILABLE, failures reset, tokens accounted
    ProviderRateLimited-> RATE_LIMITED + cooldown
    ProviderCreditExhausted -> OFFLINE + long cooldown
    other ProviderError-> failures++, and COOLDOWN once the threshold is hit

Cooldowns are time-based and resolved against an injected clock, so tests are
fully deterministic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from contracts.llm_provider import LLMRequest, LLMResponse
from providers.errors import (
    ProviderCreditExhausted,
    ProviderError,
    ProviderRateLimited,
    ProviderUnavailable,
)
from providers.state import (
    Capability,
    Clock,
    ProviderHealth,
    ProviderProfile,
    ProviderStatus,
    utc_now,
)


class BaseProvider(ABC):
    """Concrete providers subclass this and implement :meth:`_invoke`."""

    def __init__(self, profile: ProviderProfile, *, clock: Clock = utc_now) -> None:
        self.profile = profile
        self.health = ProviderHealth()
        self._clock = clock

    @property
    def name(self) -> str:
        return self.profile.name

    def supports(self, capability: Capability) -> bool:
        return self.profile.supports(capability)

    # --- availability ------------------------------------------------------

    def is_available(self) -> bool:
        """True if the provider can serve now. Resolves expired cooldowns first."""
        self.refresh(self._clock())
        return self.health.status == ProviderStatus.AVAILABLE

    def has_budget(self, estimated_tokens: int = 0) -> bool:
        remaining = self.health.remaining_budget(self.profile.daily_token_budget)
        if remaining is None:
            return True
        if remaining <= 0:
            return False
        return remaining >= estimated_tokens

    def refresh(self, now: datetime | None = None) -> bool:
        """Expire a cooldown if it has elapsed. Returns True if recovered."""
        now = now or self._clock()
        if (
            self.health.status
            in (ProviderStatus.COOLDOWN, ProviderStatus.RATE_LIMITED, ProviderStatus.OFFLINE)
            and self.health.cooldown_until is not None
            and now >= self.health.cooldown_until
        ):
            self.health.status = ProviderStatus.AVAILABLE
            self.health.consecutive_failures = 0
            self.health.cooldown_until = None
            self.health.last_error = None
            return True
        return False

    # --- invocation --------------------------------------------------------

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Invoke the vendor with full health management.

        Raises the original :class:`ProviderError` after recording the state
        transition, so the manager can decide whether to fail over.
        """
        if not self.is_available():
            raise ProviderUnavailable(
                f"provider {self.name!r} is {self.health.status} (not available)"
            )
        self.health.total_requests += 1
        try:
            response = await self._invoke(request)
        except ProviderError as exc:
            self._record_failure(exc)
            raise
        self._record_success(response)
        return response

    def _record_success(self, response: LLMResponse) -> None:
        now = self._clock()
        self.health.status = ProviderStatus.AVAILABLE
        self.health.consecutive_failures = 0
        self.health.cooldown_until = None
        self.health.last_error = None
        self.health.last_used_at = now
        self.health.tokens_used += response.usage.total_tokens

    def _record_failure(self, exc: ProviderError) -> None:
        now = self._clock()
        self.health.total_failures += 1
        self.health.last_error = f"{exc.code}: {exc}"
        if isinstance(exc, ProviderRateLimited):
            self.health.status = ProviderStatus.RATE_LIMITED
            self.health.cooldown_until = now + timedelta(seconds=self.profile.cooldown_seconds)
            return
        if isinstance(exc, ProviderCreditExhausted):
            self.health.status = ProviderStatus.OFFLINE
            self.health.cooldown_until = now + timedelta(
                seconds=self.profile.credit_exhausted_cooldown_seconds
            )
            return
        # Generic failure: count toward the threshold, then cool down.
        self.health.consecutive_failures += 1
        if self.health.consecutive_failures >= self.profile.max_consecutive_failures:
            self.health.status = ProviderStatus.FAILED
            self.health.cooldown_until = now + timedelta(seconds=self.profile.cooldown_seconds)

    @abstractmethod
    async def _invoke(self, request: LLMRequest) -> LLMResponse:
        """Perform the actual vendor call. Translate vendor errors into
        :class:`providers.errors.ProviderError` subclasses."""
        raise NotImplementedError
