"""Unit tests for the ProviderManager subsystem.

Deterministic throughout: a fake clock drives cooldowns and fake adapters drive
provider outcomes (success / rate-limit / credit-exhausted / generic failure).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from contracts.llm_provider import LLMMessage, LLMRequest, LLMResponse, LLMUsage
from events.base import DomainEvent
from providers.base import BaseProvider
from providers.errors import (
    NoProviderAvailable,
    ProviderCreditExhausted,
    ProviderError,
    ProviderRateLimited,
)
from providers.implementations import LocalProvider
from providers.manager import ProviderManager
from providers.persistence import InMemoryProviderStateStore
from providers.registry import ProviderRegistry
from providers.state import Capability, ProviderProfile, ProviderStatus

pytestmark = pytest.mark.unit


# --- test doubles ----------------------------------------------------------


class FakeClock:
    def __init__(self, start: datetime | None = None) -> None:
        self.now = start or datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def _response(content: str = "ok", tokens: int = 10) -> LLMResponse:
    return LLMResponse(
        model="fake",
        content=content,
        finish_reason="stop",
        usage=LLMUsage(prompt_tokens=tokens, completion_tokens=tokens, total_tokens=2 * tokens),
    )


class ScriptedProvider(BaseProvider):
    """Provider whose _invoke follows a script of outcomes (response or exception)."""

    def __init__(self, profile: ProviderProfile, script: list[object], *, clock: object) -> None:
        super().__init__(profile, clock=clock)  # type: ignore[arg-type]
        self._script = list(script)
        self.calls = 0

    async def _invoke(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        outcome = self._script.pop(0) if self._script else _response()
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, LLMResponse)
        return outcome


class RecordingBus:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)

    async def publish_many(self, events: object) -> None:  # pragma: no cover
        raise NotImplementedError

    async def subscribe(self, *a: object, **k: object) -> object:  # pragma: no cover
        raise NotImplementedError

    async def unsubscribe(self, subscription_id: str) -> None:  # pragma: no cover
        raise NotImplementedError


def _profile(name: str, *, cost: float, weight: float = 1.0, **kw: object) -> ProviderProfile:
    return ProviderProfile(
        name=name,
        capabilities=frozenset({Capability.CODE_GENERATION}),
        cost_per_1k_tokens=cost,
        context_window=100_000,
        weight=weight,
        **kw,  # type: ignore[arg-type]
    )


def _request() -> LLMRequest:
    return LLMRequest(model="x", messages=[LLMMessage(role="user", content="hello")])


# --- tests -----------------------------------------------------------------


async def test_selects_single_available_provider() -> None:
    clock = FakeClock()
    reg = ProviderRegistry()
    reg.register(ScriptedProvider(_profile("a", cost=1.0), [_response("hi", 5)], clock=clock))
    mgr = ProviderManager(reg)

    result = await mgr.complete(_request(), capability=Capability.CODE_GENERATION)

    assert result.provider == "a"
    assert result.content == "hi"
    assert result.total_tokens == 10
    assert result.attempts == 1


async def test_registry_orders_by_weight_then_cost() -> None:
    clock = FakeClock()
    reg = ProviderRegistry()
    reg.register(ScriptedProvider(_profile("pricey", cost=15.0), [], clock=clock))
    reg.register(ScriptedProvider(_profile("cheap", cost=0.5), [], clock=clock))
    reg.register(ScriptedProvider(_profile("local", cost=0.0, weight=0.1), [], clock=clock))

    order = [p.name for p in reg.for_capability(Capability.CODE_GENERATION)]
    assert order == ["cheap", "pricey", "local"]  # weight desc, then cost asc


async def test_fails_over_to_next_provider_on_error() -> None:
    clock = FakeClock()
    reg = ProviderRegistry()
    reg.register(
        ScriptedProvider(_profile("first", cost=0.5), [ProviderError("boom")], clock=clock)
    )
    reg.register(ScriptedProvider(_profile("second", cost=1.0), [_response("served")], clock=clock))
    bus = RecordingBus()
    mgr = ProviderManager(reg, event_bus=bus)

    result = await mgr.complete(_request(), capability=Capability.CODE_GENERATION)

    assert result.provider == "second"
    assert result.failed_over_from == ("first",)
    assert any(e.event_type == "provider.failed_over" for e in bus.events)
    assert any(e.event_type == "provider.invocation_succeeded" for e in bus.events)


async def test_rate_limit_enters_cooldown_and_recovers_after_clock_advance() -> None:
    clock = FakeClock()
    p = ScriptedProvider(
        _profile("rl", cost=1.0, cooldown_seconds=60.0),
        [ProviderRateLimited("429"), _response("recovered")],
        clock=clock,
    )
    reg = ProviderRegistry()
    reg.register(p)
    mgr = ProviderManager(reg)

    with pytest.raises(NoProviderAvailable):
        await mgr.complete(_request(), capability=Capability.CODE_GENERATION)
    assert p.health.status == ProviderStatus.RATE_LIMITED

    clock.advance(61)
    result = await mgr.complete(_request(), capability=Capability.CODE_GENERATION)
    assert result.provider == "rl"
    assert p.health.status == ProviderStatus.AVAILABLE


async def test_credit_exhaustion_takes_provider_offline_and_emits_event() -> None:
    clock = FakeClock()
    reg = ProviderRegistry()
    reg.register(
        ScriptedProvider(
            _profile("paid", cost=0.5), [ProviderCreditExhausted("no credit")], clock=clock
        )
    )
    reg.register(ScriptedProvider(_profile("backup", cost=1.0), [_response("ok")], clock=clock))
    bus = RecordingBus()
    mgr = ProviderManager(reg, event_bus=bus)

    result = await mgr.complete(_request(), capability=Capability.CODE_GENERATION)

    assert result.provider == "backup"
    paid = reg.get("paid")
    assert paid.health.status == ProviderStatus.OFFLINE
    assert any(e.event_type == "provider.credit_exhausted" for e in bus.events)


async def test_generic_failures_trip_failed_status_at_threshold() -> None:
    clock = FakeClock()
    p = ScriptedProvider(
        _profile("flaky", cost=1.0, max_consecutive_failures=2),
        [ProviderError("e1"), ProviderError("e2")],
        clock=clock,
    )
    reg = ProviderRegistry()
    reg.register(p)
    mgr = ProviderManager(reg)

    for _ in range(2):
        with pytest.raises(NoProviderAvailable):
            await mgr.complete(_request(), capability=Capability.CODE_GENERATION)
    assert p.health.status == ProviderStatus.FAILED


async def test_token_budget_excludes_exhausted_provider() -> None:
    clock = FakeClock()
    p = ScriptedProvider(
        _profile("budgeted", cost=1.0, daily_token_budget=5),
        [_response("first", tokens=10)],  # consumes 20 tokens > budget 5
        clock=clock,
    )
    reg = ProviderRegistry()
    reg.register(p)
    mgr = ProviderManager(reg)

    await mgr.complete(_request(), capability=Capability.CODE_GENERATION)
    assert p.has_budget() is False
    with pytest.raises(NoProviderAvailable):
        await mgr.complete(_request(), capability=Capability.CODE_GENERATION)


async def test_no_provider_for_capability_raises() -> None:
    reg = ProviderRegistry()
    reg.register(ScriptedProvider(_profile("only_codegen", cost=1.0), [], clock=FakeClock()))
    mgr = ProviderManager(reg)

    with pytest.raises(NoProviderAvailable):
        await mgr.complete(_request(), capability=Capability.EMBEDDING)


async def test_explicit_order_overrides_default() -> None:
    clock = FakeClock()
    reg = ProviderRegistry()
    reg.register(ScriptedProvider(_profile("cheap", cost=0.5), [_response("c")], clock=clock))
    reg.register(ScriptedProvider(_profile("pricey", cost=15.0), [_response("p")], clock=clock))
    mgr = ProviderManager(reg)

    result = await mgr.complete(
        _request(), capability=Capability.CODE_GENERATION, order=["pricey", "cheap"]
    )
    assert result.provider == "pricey"


async def test_state_is_persisted_after_invocation() -> None:
    clock = FakeClock()
    store = InMemoryProviderStateStore()
    reg = ProviderRegistry()
    reg.register(ScriptedProvider(_profile("p", cost=1.0), [_response(tokens=7)], clock=clock))
    mgr = ProviderManager(reg, state_store=store)

    await mgr.complete(_request(), capability=Capability.CODE_GENERATION)
    saved = await store.load("p")
    assert saved is not None
    assert saved.total_requests == 1
    assert saved.tokens_used == 14


async def test_local_provider_degraded_fallback_without_adapter() -> None:
    provider = LocalProvider(clock=FakeClock())
    reg = ProviderRegistry()
    reg.register(provider)
    mgr = ProviderManager(reg)

    result = await mgr.complete(_request(), capability=Capability.CODE_GENERATION)
    assert result.provider == "local"
    assert result.content == "[local-fallback] hello"
