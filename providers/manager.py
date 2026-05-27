"""ProviderManager — capability-aware invocation with automatic failover.

The manager is the runtime's single entry point for "run this request against the
best available provider for capability X". It is deliberately decoupled from the
WorkflowEngine: callers pass a request + capability, and get back a result or a
:class:`NoProviderAvailable`. Workflows decide what to do (pause/resume) on that.

Responsibilities:
  - select providers for a capability in a deterministic order,
  - skip providers that are unavailable / out of budget,
  - invoke, and on failure transition state + fail over to the next provider,
  - persist health after every transition,
  - emit a provider event for every decision (selection, failover, exhaustion).

It hardcodes no vendor logic; behavior derives entirely from provider profiles.
"""

from __future__ import annotations

from collections.abc import Sequence

from contracts.event_bus import EventBusPort
from contracts.llm_provider import LLMRequest
from events.base import DomainEvent
from events.domain.provider import (
    AllProvidersExhausted,
    ProviderCooldownEntered,
    ProviderCreditExhausted,
    ProviderFailedOver,
    ProviderInvocationSucceeded,
    ProviderSelected,
)
from providers.base import BaseProvider
from providers.errors import (
    NoProviderAvailable,
    ProviderError,
)
from providers.errors import (
    ProviderCreditExhausted as ProviderCreditExhaustedError,
)
from providers.persistence import InMemoryProviderStateStore, ProviderStateStore
from providers.registry import ProviderRegistry
from providers.state import Capability, ProviderInvocation, ProviderStatus


class ProviderManager:
    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        event_bus: EventBusPort | None = None,
        state_store: ProviderStateStore | None = None,
    ) -> None:
        self._registry = registry
        self._bus = event_bus
        self._store: ProviderStateStore = state_store or InMemoryProviderStateStore()

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    def candidates(
        self, capability: Capability, *, order: Sequence[str] | None = None
    ) -> list[BaseProvider]:
        """Available providers for ``capability``, in failover order.

        If ``order`` (a list of provider names, e.g. from the routing engine) is
        given, it takes precedence; unknown/unsupported names are ignored.
        """
        supporting = {p.name: p for p in self._registry.for_capability(capability)}
        ordered = (
            [supporting[n] for n in order if n in supporting]
            if order is not None
            else list(supporting.values())
        )
        return [p for p in ordered if p.is_available() and p.has_budget()]

    async def complete(
        self,
        request: LLMRequest,
        *,
        capability: Capability,
        order: Sequence[str] | None = None,
    ) -> ProviderInvocation:
        """Run ``request`` against the best provider, failing over on error.

        Raises :class:`NoProviderAvailable` if no provider can serve.
        """
        candidates = self.candidates(capability, order=order)
        if not candidates:
            await self._emit(AllProvidersExhausted(capability=capability.value, tried=()))
            raise NoProviderAvailable(
                f"no available provider supports capability {capability.value!r}"
            )

        failed_over: list[str] = []
        for attempt, provider in enumerate(candidates, start=1):
            await self._emit(
                ProviderSelected(
                    provider=provider.name, capability=capability.value, attempt=attempt
                )
            )
            try:
                response = await provider.complete(request)
            except ProviderError as exc:
                await self._on_failure(provider, capability, exc)
                failed_over.append(provider.name)
                continue
            await self._store.save(provider.name, provider.health)
            await self._emit(
                ProviderInvocationSucceeded(
                    provider=provider.name,
                    capability=capability.value,
                    total_tokens=response.usage.total_tokens,
                )
            )
            return ProviderInvocation(
                provider=provider.name,
                content=response.content,
                total_tokens=response.usage.total_tokens,
                attempts=attempt,
                failed_over_from=tuple(failed_over),
            )

        await self._emit(
            AllProvidersExhausted(capability=capability.value, tried=tuple(failed_over))
        )
        raise NoProviderAvailable(
            f"all {len(candidates)} provider(s) failed for capability {capability.value!r}"
        )

    async def _on_failure(
        self, provider: BaseProvider, capability: Capability, exc: ProviderError
    ) -> None:
        await self._store.save(provider.name, provider.health)
        await self._emit(
            ProviderFailedOver(
                provider=provider.name,
                capability=capability.value,
                reason=str(exc),
                error_code=exc.code,
            )
        )
        if isinstance(exc, ProviderCreditExhaustedError):
            await self._emit(ProviderCreditExhausted(provider=provider.name))
        if provider.health.status in (
            ProviderStatus.COOLDOWN,
            ProviderStatus.RATE_LIMITED,
            ProviderStatus.OFFLINE,
            ProviderStatus.FAILED,
        ):
            cooldown = provider.health.cooldown_until
            await self._emit(
                ProviderCooldownEntered(
                    provider=provider.name,
                    status=provider.health.status.value,
                    cooldown_until=cooldown.isoformat() if cooldown else None,
                    reason=exc.code,
                )
            )

    async def _emit(self, event: DomainEvent) -> None:
        if self._bus is not None:
            await self._bus.publish(event)
