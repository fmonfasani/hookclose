"""Unit tests for the ComplexityRoutingEngine (deterministic, auditable)."""

from __future__ import annotations

import pytest

from providers.implementations import (
    ClaudeProvider,
    GeminiProvider,
    LocalProvider,
    OpenCodeProvider,
)
from providers.registry import ProviderRegistry
from providers.routing import (
    ComplexityRoutingEngine,
    RoutingPolicy,
    RoutingRequest,
    TaskComplexity,
)
from providers.state import Capability

pytestmark = pytest.mark.unit


class _NullAdapter:
    provider = "null"

    async def complete(self, request: object) -> object:  # pragma: no cover
        raise NotImplementedError

    async def stream(self, request: object) -> object:  # pragma: no cover
        raise NotImplementedError

    async def embed(self, texts: object, *, model: str) -> object:  # pragma: no cover
        raise NotImplementedError


def _full_registry() -> ProviderRegistry:
    adapter = _NullAdapter()
    reg = ProviderRegistry()
    reg.register(ClaudeProvider(adapter))  # type: ignore[arg-type]
    reg.register(OpenCodeProvider(adapter))  # type: ignore[arg-type]
    reg.register(GeminiProvider(adapter))  # type: ignore[arg-type]
    reg.register(LocalProvider())
    return reg


def _engine() -> ComplexityRoutingEngine:
    return ComplexityRoutingEngine(_full_registry())


def test_architecture_routes_to_claude_first() -> None:
    decision = _engine().decide(
        RoutingRequest(capability=Capability.ARCHITECTURE, task_type="architecture.design")
    )
    assert decision.ordered_providers[0] == "claude"


def test_cheap_extraction_routes_to_gemini_first() -> None:
    decision = _engine().decide(
        RoutingRequest(capability=Capability.EXTRACTION, task_type="extraction.parse")
    )
    assert decision.ordered_providers[0] == "gemini"


def test_simple_codegen_prefers_opencode_over_claude() -> None:
    decision = _engine().decide(
        RoutingRequest(
            capability=Capability.CODE_GENERATION,
            task_type="codegen.simple",
            complexity_hint=TaskComplexity.SIMPLE,
        )
    )
    order = decision.ordered_providers
    assert order.index("opencode") < order.index("claude")


def test_local_is_last_resort() -> None:
    decision = _engine().decide(
        RoutingRequest(capability=Capability.CODE_GENERATION, task_type="codegen.x")
    )
    assert decision.ordered_providers[-1] == "local"


def test_priority_and_retries_escalate_complexity() -> None:
    engine = _engine()
    base = engine.complexity_score(
        RoutingRequest(capability=Capability.CODE_GENERATION, task_type="codegen.x")
    )
    escalated = engine.complexity_score(
        RoutingRequest(
            capability=Capability.CODE_GENERATION,
            task_type="codegen.x",
            priority=5,
            retry_count=2,
        )
    )
    assert escalated > base
    assert escalated <= 1.0


def test_retry_escalation_promotes_claude_for_codegen() -> None:
    engine = _engine()
    calm = engine.decide(
        RoutingRequest(
            capability=Capability.CODE_GENERATION,
            task_type="codegen.x",
            complexity_hint=TaskComplexity.SIMPLE,
        )
    )
    after_retries = engine.decide(
        RoutingRequest(
            capability=Capability.CODE_GENERATION,
            task_type="codegen.x",
            complexity_hint=TaskComplexity.SIMPLE,
            retry_count=4,
        )
    )
    assert calm.ordered_providers[0] != "claude"
    assert after_retries.ordered_providers[0] == "claude"


def test_context_window_filters_out_small_providers() -> None:
    # 500k tokens: only gemini (1M) fits; claude/opencode/local are too small.
    decision = _engine().decide(
        RoutingRequest(
            capability=Capability.CODE_GENERATION,
            task_type="codegen.huge",
            estimated_tokens=500_000,
        )
    )
    assert decision.ordered_providers == ("gemini",)
    assert "context-fit" in decision.reason


def test_decision_is_deterministic() -> None:
    engine = _engine()
    req = RoutingRequest(capability=Capability.CODE_GENERATION, task_type="codegen.x", priority=3)
    assert engine.decide(req) == engine.decide(req)


def test_no_capability_yields_empty_order() -> None:
    reg = ProviderRegistry()
    reg.register(LocalProvider())  # supports codegen/extraction, not embedding
    decision = ComplexityRoutingEngine(reg).decide(RoutingRequest(capability=Capability.EMBEDDING))
    assert decision.ordered_providers == ()
    assert "no provider" in decision.reason


def test_custom_policy_overrides_default_complexity() -> None:
    policy = RoutingPolicy(
        task_type_complexity={"codegen": TaskComplexity.CRITICAL},
        default_complexity=TaskComplexity.TRIVIAL,
    )
    engine = ComplexityRoutingEngine(_full_registry(), policy=policy)
    decision = engine.decide(
        RoutingRequest(capability=Capability.CODE_GENERATION, task_type="codegen.x")
    )
    # Now codegen is CRITICAL -> claude first.
    assert decision.ordered_providers[0] == "claude"
