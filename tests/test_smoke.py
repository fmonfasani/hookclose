"""Runtime smoke test — wires the whole stack end-to-end in-process.

This is the deterministic integration the CI ``smoke`` job runs to assert the
runtime is actually wired together: providers -> routing -> manager invocation ->
autonomous chaining -> self-healing. No network, no containers.
"""

from __future__ import annotations

import importlib

import pytest

from contracts.llm_provider import LLMMessage, LLMRequest, LLMResponse, LLMUsage
from orchestration import SelfHealingRuntime, TaskChainer
from providers import (
    Capability,
    ComplexityRoutingEngine,
    LocalProvider,
    ProviderManager,
    ProviderRegistry,
    RoutingRequest,
)
from providers.base import BaseProvider
from providers.state import ProviderProfile
from tasks.models import Task


def _codegen_request() -> RoutingRequest:
    return RoutingRequest(capability=Capability.CODE_GENERATION, task_type="codegen.feature")


pytestmark = [pytest.mark.smoke, pytest.mark.unit]


class _EchoCodegen(BaseProvider):
    def __init__(self) -> None:
        super().__init__(
            ProviderProfile(
                name="echo-codegen",
                capabilities=frozenset({Capability.CODE_GENERATION}),
                cost_per_1k_tokens=1.0,
                context_window=100_000,
            )
        )

    async def _invoke(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            model="echo",
            content="generated",
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=5, completion_tokens=5, total_tokens=10),
        )


def test_all_packages_import() -> None:
    for pkg in (
        "runtime",
        "providers",
        "workers",
        "orchestration",
        "events",
        "tasks",
        "observability",
    ):
        assert importlib.import_module(pkg) is not None


async def test_end_to_end_pipeline() -> None:
    registry = ProviderRegistry()
    registry.register(_EchoCodegen())
    registry.register(LocalProvider())
    routing = ComplexityRoutingEngine(registry)
    manager = ProviderManager(registry)

    # routing picks an order; manager invokes the best available provider
    decision = routing.decide(_codegen_request())
    assert decision.ordered_providers[0] in registry.names()

    request = LLMRequest(model="auto", messages=[LLMMessage(role="user", content="build X")])
    invocation = await manager.complete(
        request, capability=Capability.CODE_GENERATION, order=list(decision.ordered_providers)
    )
    assert invocation.content == "generated"

    # autonomous chaining: a completed codegen task yields a testing task
    chainer = TaskChainer()
    nxt = await chainer.on_completed(Task(task_type="codegen.x"))
    assert nxt and nxt[0].task_type == "testing.auto"

    # self-healing: a failure produces a bounded, deterministic decision
    healer = SelfHealingRuntime()
    decision = await healer.handle_failure("t1", "AssertionError: 1 == 2")
    assert decision.action.value in {
        "retry",
        "deterministic_fix",
        "llm_repair",
        "rollback",
        "escalate",
    }
