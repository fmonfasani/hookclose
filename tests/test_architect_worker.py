"""Unit tests for the ClaudeArchitectWorker (deterministic via scripted provider)."""

from __future__ import annotations

import json

import pytest

from contracts.llm_provider import LLMRequest, LLMResponse, LLMUsage
from events.base import DomainEvent
from providers.base import BaseProvider
from providers.manager import ProviderManager
from providers.registry import ProviderRegistry
from providers.state import Capability, ProviderProfile
from workers.architect import DRIFT_THRESHOLD, ClaudeArchitectWorker, InMemoryReviewStore
from workers.architect_prompts import ReviewKind

pytestmark = pytest.mark.unit

_ALL_CAPS = frozenset(
    {Capability.ARCHITECTURE, Capability.ANALYSIS, Capability.REVIEW, Capability.CODE_GENERATION}
)


class CannedProvider(BaseProvider):
    """Returns a fixed content string regardless of request."""

    def __init__(self, name: str, content: str) -> None:
        super().__init__(
            ProviderProfile(
                name=name, capabilities=_ALL_CAPS, cost_per_1k_tokens=10.0, context_window=200_000
            )
        )
        self._content = content

    async def _invoke(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            model="canned",
            content=self._content,
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        )


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


def _manager(content: str) -> ProviderManager:
    reg = ProviderRegistry()
    reg.register(CannedProvider("claude", content))
    return ProviderManager(reg)


def _envelope(
    score: int, *, findings: list[str] | None = None, sections: list[str] | None = None
) -> str:
    return json.dumps(
        {
            "score": score,
            "summary": "ok",
            "findings": findings or [],
            "sections": sections or [],
        }
    )


async def test_architecture_review_parses_structured_output() -> None:
    bus = RecordingBus()
    worker = ClaudeArchitectWorker(
        _manager(_envelope(82, findings=["coupling in X"])), event_bus=bus
    )

    result = await worker.review_architecture("runtime/", "module map ...")

    assert result.score == 82
    assert result.findings == ("coupling in X",)
    assert not result.degraded
    assert any(e.event_type == "architecture.reviewed" for e in bus.events)


async def test_spec_generation_emits_spec_event_with_sections() -> None:
    bus = RecordingBus()
    worker = ClaudeArchitectWorker(
        _manager(_envelope(90, sections=["Overview", "API", "Risks"])), event_bus=bus
    )

    result = await worker.generate_spec("payments", "build a payments spec")

    assert result.kind is ReviewKind.SPEC_GENERATION
    assert result.sections == ("Overview", "API", "Risks")
    spec_events = [e for e in bus.events if e.event_type == "architecture.spec_generated"]
    assert spec_events and spec_events[0].section_count == 3  # type: ignore[attr-defined]


async def test_drift_detected_when_score_drops() -> None:
    store = InMemoryReviewStore()
    bus = RecordingBus()
    # First review: healthy.
    await ClaudeArchitectWorker(
        _manager(_envelope(90)), review_store=store, event_bus=bus
    ).review_architecture("svc", "v1")
    # Second review: big drop -> drift.
    drop = 90 - DRIFT_THRESHOLD - 5
    result = await ClaudeArchitectWorker(
        _manager(_envelope(drop)), review_store=store, event_bus=bus
    ).review_architecture("svc", "v2")

    assert result.drift_detected
    assert any(e.event_type == "architecture.drift_detected" for e in bus.events)


async def test_no_drift_on_small_change() -> None:
    store = InMemoryReviewStore()
    await ClaudeArchitectWorker(_manager(_envelope(90)), review_store=store).review_architecture(
        "svc", "v1"
    )
    result = await ClaudeArchitectWorker(
        _manager(_envelope(85)), review_store=store
    ).review_architecture("svc", "v2")
    assert not result.drift_detected


async def test_malformed_output_degrades_safely() -> None:
    worker = ClaudeArchitectWorker(_manager("not json at all"))
    result = await worker.review_architecture("svc", "x")
    assert result.degraded
    assert result.score == 0


async def test_no_provider_available_degrades() -> None:
    # No providers registered at all -> manager raises NoProviderAvailable -> degrade.
    worker = ClaudeArchitectWorker(ProviderManager(ProviderRegistry()))
    result = await worker.review_architecture("svc", "x")
    assert result.degraded
    assert result.provider == "none"


async def test_score_is_clamped() -> None:
    worker = ClaudeArchitectWorker(_manager(_envelope(150)))
    result = await worker.review_architecture("svc", "x")
    assert result.score == 100
