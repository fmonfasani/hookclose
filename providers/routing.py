"""ComplexityRoutingEngine — deterministic, cost/quality-aware provider ordering.

The engine does not invoke anything. Given a :class:`RoutingRequest` it produces a
:class:`RoutingDecision`: an ordered list of provider names that the
:class:`~providers.manager.ProviderManager` fails over through. Ordering is a pure,
deterministic function of the request and provider profiles, so the same inputs
always yield the same decision (and it is fully auditable via the emitted event).

Routing axes:
  - **complexity scoring** — task type + explicit hint, escalated by priority & retries
  - **capability matching** — only providers declaring the capability
  - **context-window-aware** — drop providers too small for the estimated tokens
  - **cost-aware** — cheaper providers favored for low-complexity work
  - **quality-aware** — pricier providers favored for high-complexity work
  - **priority/retry-aware** — both push the effective complexity up (escalation)

The cost↔quality mapping uses ``cost_per_1k_tokens`` as a quality proxy (Claude is
expensive *and* the most capable), and ``weight`` as a tiebreaker that keeps a
last-resort local model sorted last. This yields the canonical examples:
architecture→claude, simple codegen→opencode, cheap extraction→gemini, fallback→local.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from contracts.event_bus import EventBusPort
from events.domain.provider import RoutingDecided
from providers.base import BaseProvider
from providers.registry import ProviderRegistry
from providers.state import Capability


class TaskComplexity(StrEnum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"

    @property
    def score(self) -> float:
        return _COMPLEXITY_SCORE[self]


_COMPLEXITY_SCORE: dict[TaskComplexity, float] = {
    TaskComplexity.TRIVIAL: 0.1,
    TaskComplexity.SIMPLE: 0.3,
    TaskComplexity.MODERATE: 0.5,
    TaskComplexity.COMPLEX: 0.8,
    TaskComplexity.CRITICAL: 1.0,
}

# At/above this complexity, ordering favors quality (pricier) over cost.
_QUALITY_THRESHOLD = 0.5


@dataclass(frozen=True, slots=True)
class RoutingRequest:
    capability: Capability
    task_type: str = ""
    estimated_tokens: int = 0
    priority: int = 0  # 0..10; higher escalates toward quality
    retry_count: int = 0
    complexity_hint: TaskComplexity | None = None


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    """Configurable routing knobs. Defaults give the canonical behavior."""

    task_type_complexity: Mapping[str, TaskComplexity] = field(default_factory=dict)
    default_complexity: TaskComplexity = TaskComplexity.MODERATE
    priority_weight: float = 0.03  # added to complexity per priority point
    retry_escalation: float = 0.15  # added to complexity per retry

    @classmethod
    def default(cls) -> RoutingPolicy:
        return cls(
            task_type_complexity={
                "architecture": TaskComplexity.CRITICAL,
                "review": TaskComplexity.COMPLEX,
                "analysis": TaskComplexity.COMPLEX,
                "refactor": TaskComplexity.COMPLEX,
                "spec": TaskComplexity.COMPLEX,
                "codegen": TaskComplexity.MODERATE,
                "testing": TaskComplexity.SIMPLE,
                "extraction": TaskComplexity.TRIVIAL,
                "ingest": TaskComplexity.TRIVIAL,
            }
        )

    def base_complexity(self, task_type: str) -> TaskComplexity:
        # Longest matching prefix wins (e.g. "architecture.review" -> architecture).
        head = task_type.split(".", 1)[0] if task_type else ""
        return self.task_type_complexity.get(head, self.default_complexity)


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    capability: Capability
    complexity_score: float
    ordered_providers: tuple[str, ...]
    provider_scores: tuple[tuple[str, float], ...]
    reason: str


class ComplexityRoutingEngine:
    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        policy: RoutingPolicy | None = None,
        event_bus: EventBusPort | None = None,
    ) -> None:
        self._registry = registry
        self._policy = policy or RoutingPolicy.default()
        self._bus = event_bus

    def complexity_score(self, request: RoutingRequest) -> float:
        base = (
            request.complexity_hint.score
            if request.complexity_hint is not None
            else self._policy.base_complexity(request.task_type).score
        )
        escalated = (
            base
            + request.priority * self._policy.priority_weight
            + request.retry_count * self._policy.retry_escalation
        )
        return _clamp(escalated, 0.0, 1.0)

    def decide(self, request: RoutingRequest) -> RoutingDecision:
        score = self.complexity_score(request)
        supporting = list(self._registry.for_capability(request.capability))

        if not supporting:
            return RoutingDecision(
                capability=request.capability,
                complexity_score=score,
                ordered_providers=(),
                provider_scores=(),
                reason=f"no provider declares capability {request.capability.value!r}",
            )

        # Context-window-aware: prefer providers that fit; only relax if none fit.
        fitting = [p for p in supporting if p.profile.context_window >= request.estimated_tokens]
        if fitting:
            candidates, ctx_note = fitting, "context-fit"
        else:
            candidates, ctx_note = supporting, "context-overflow-relaxed"

        ranked = _rank(candidates, score)
        ordered = tuple(name for name, _ in ranked)
        reason = (
            f"complexity={score:.2f} ({ctx_note}); "
            f"{'quality-weighted' if score >= _QUALITY_THRESHOLD else 'cost-weighted'} order"
        )
        return RoutingDecision(
            capability=request.capability,
            complexity_score=score,
            ordered_providers=ordered,
            provider_scores=ranked,
            reason=reason,
        )

    async def route(self, request: RoutingRequest) -> RoutingDecision:
        """Decide and emit an auditable :class:`RoutingDecided` event."""
        decision = self.decide(request)
        if self._bus is not None:
            await self._bus.publish(
                RoutingDecided(
                    capability=decision.capability.value,
                    complexity_score=decision.complexity_score,
                    ordered_providers=decision.ordered_providers,
                    reason=decision.reason,
                )
            )
        return decision


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _rank(candidates: Sequence[BaseProvider], complexity: float) -> tuple[tuple[str, float], ...]:
    """Score and sort providers. Higher complexity favors pricier (better) models."""
    costs = [p.profile.cost_per_1k_tokens for p in candidates]
    lo, hi = min(costs), max(costs)
    span = hi - lo

    def normalized_cost(provider: BaseProvider) -> float:
        if span == 0:
            return 0.5
        return (provider.profile.cost_per_1k_tokens - lo) / span

    scored: list[tuple[str, float]] = []
    for provider in candidates:
        ncost = normalized_cost(provider)
        # High complexity -> reward high cost; low complexity -> reward low cost.
        affinity = complexity * ncost + (1.0 - complexity) * (1.0 - ncost)
        scored.append((provider.name, round(affinity * provider.profile.weight, 6)))

    # Sort by score desc, then name asc for determinism.
    scored.sort(key=lambda item: (-item[1], item[0]))
    return tuple(scored)
