"""Provider error hierarchy.

These are the only exceptions a provider's ``_invoke`` may raise across the
``BaseProvider`` boundary. Concrete adapters MUST translate vendor exceptions into
one of these so the manager can react deterministically (cooldown, failover, …).
"""

from __future__ import annotations

from runtime.errors import AineError, InfrastructureError


class ProviderError(InfrastructureError):
    """Generic, retryable provider failure."""

    code = "aine.provider.error"


class ProviderRateLimited(ProviderError):
    """Vendor returned a rate-limit / 429. Triggers a cooldown."""

    code = "aine.provider.rate_limited"


class ProviderCreditExhausted(ProviderError):
    """Vendor credit/quota is exhausted. Provider goes OFFLINE; runtime fails over."""

    code = "aine.provider.credit_exhausted"


class ProviderTimeout(ProviderError):
    """The invocation exceeded its deadline."""

    code = "aine.provider.timeout"


class ProviderUnavailable(ProviderError):
    """Provider was asked to serve while not AVAILABLE."""

    code = "aine.provider.unavailable"


class NoProviderAvailable(AineError):
    """No registered provider could serve the request (all filtered/exhausted)."""

    code = "aine.provider.none_available"
