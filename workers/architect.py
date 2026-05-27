"""ClaudeArchitectWorker — the expensive cognition layer.

Claude (routed via the ProviderManager with ARCHITECTURE/ANALYSIS/REVIEW capability)
is used *only* for high-value reasoning: architecture reviews, runtime analysis,
spec generation, and refactor reviews. It never executes code, drives workflows,
or manages global state — it produces a structured, scored, persisted review.

Outputs are deterministic JSON envelopes (see ``architect_prompts``). The worker:
  - dispatches the right handler per :class:`ReviewKind`,
  - invokes the provider for the matching capability,
  - parses + validates the JSON into a :class:`ReviewResult` (degrading safely),
  - computes an architecture score and detects drift vs. the previous review,
  - persists the review and emits review/drift/spec events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Protocol, runtime_checkable

from contracts.event_bus import EventBusPort
from events.base import DomainEvent
from events.domain.architecture import (
    ArchitectureDriftDetected,
    ArchitectureReviewed,
    SpecGenerated,
)
from providers.errors import NoProviderAvailable
from providers.manager import ProviderManager
from workers.architect_prompts import ReviewKind, build_request

DRIFT_THRESHOLD = 15  # a score drop >= this vs. the last review flags drift


@dataclass(frozen=True, slots=True)
class ReviewResult:
    kind: ReviewKind
    target: str
    provider: str
    score: int
    summary: str
    findings: tuple[str, ...] = ()
    sections: tuple[str, ...] = ()
    drift_detected: bool = False
    degraded: bool = False  # True if the model output could not be parsed as JSON


@runtime_checkable
class ReviewStore(Protocol):
    """Persists reviews and exposes the latest score per target (for drift)."""

    async def save(self, result: ReviewResult) -> None: ...

    async def latest_score(self, target: str, kind: ReviewKind) -> int | None: ...


@dataclass(slots=True)
class InMemoryReviewStore:
    history: dict[tuple[str, str], list[ReviewResult]] = field(default_factory=dict)

    async def save(self, result: ReviewResult) -> None:
        self.history.setdefault((result.target, result.kind.value), []).append(result)

    async def latest_score(self, target: str, kind: ReviewKind) -> int | None:
        entries = self.history.get((target, kind.value), [])
        return entries[-1].score if entries else None


class ClaudeArchitectWorker:
    name = "claude-architect"

    def __init__(
        self,
        manager: ProviderManager,
        *,
        review_store: ReviewStore | None = None,
        event_bus: EventBusPort | None = None,
    ) -> None:
        self._manager = manager
        self._store: ReviewStore = review_store or InMemoryReviewStore()
        self._bus = event_bus

    # --- handlers (one per ReviewKind) ------------------------------------

    async def review_architecture(self, target: str, content: str) -> ReviewResult:
        return await self._run(ReviewKind.ARCHITECTURE_REVIEW, target, content)

    async def analyze_runtime(self, target: str, content: str) -> ReviewResult:
        return await self._run(ReviewKind.RUNTIME_ANALYSIS, target, content)

    async def generate_spec(self, target: str, content: str) -> ReviewResult:
        return await self._run(ReviewKind.SPEC_GENERATION, target, content)

    async def review_refactor(self, target: str, content: str) -> ReviewResult:
        return await self._run(ReviewKind.REFACTOR_REVIEW, target, content)

    # --- core --------------------------------------------------------------

    async def _run(self, kind: ReviewKind, target: str, content: str) -> ReviewResult:
        previous = await self._store.latest_score(target, kind)
        request = build_request(kind, target=target, content=content)

        try:
            invocation = await self._manager.complete(request, capability=kind.capability)
        except NoProviderAvailable:
            result = ReviewResult(
                kind=kind,
                target=target,
                provider="none",
                score=0,
                summary="no provider available for cognition",
                degraded=True,
            )
            await self._store.save(result)
            return result

        parsed = _parse(invocation.content)
        drift = previous is not None and (previous - parsed.score) >= DRIFT_THRESHOLD
        result = ReviewResult(
            kind=kind,
            target=target,
            provider=invocation.provider,
            score=parsed.score,
            summary=parsed.summary,
            findings=parsed.findings,
            sections=parsed.sections,
            drift_detected=drift,
            degraded=parsed.degraded,
        )
        await self._store.save(result)
        await self._emit_events(result, previous)
        return result

    async def _emit_events(self, result: ReviewResult, previous: int | None) -> None:
        await self._emit(
            ArchitectureReviewed(
                target=result.target,
                kind=result.kind.value,
                score=result.score,
                finding_count=len(result.findings),
                provider=result.provider,
            )
        )
        if result.kind is ReviewKind.SPEC_GENERATION:
            await self._emit(
                SpecGenerated(
                    target=result.target,
                    kind=result.kind.value,
                    provider=result.provider,
                    section_count=len(result.sections),
                )
            )
        if result.drift_detected and previous is not None:
            await self._emit(
                ArchitectureDriftDetected(
                    target=result.target,
                    previous_score=previous,
                    current_score=result.score,
                    delta=previous - result.score,
                )
            )

    async def _emit(self, event: DomainEvent) -> None:
        if self._bus is not None:
            await self._bus.publish(event)


@dataclass(frozen=True, slots=True)
class _Parsed:
    score: int
    summary: str
    findings: tuple[str, ...]
    sections: tuple[str, ...]
    degraded: bool


def _parse(content: str) -> _Parsed:
    """Parse the JSON envelope, degrading safely on malformed output."""
    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except (json.JSONDecodeError, ValueError):
        return _Parsed(score=0, summary=content[:200], findings=(), sections=(), degraded=True)

    raw_score = data.get("score", 0)
    score = int(raw_score) if isinstance(raw_score, (int, float)) else 0
    score = max(0, min(100, score))

    raw_findings = data.get("findings", [])
    raw_sections = data.get("sections", [])
    findings = tuple(str(f) for f in raw_findings) if isinstance(raw_findings, list) else ()
    sections = tuple(str(s) for s in raw_sections) if isinstance(raw_sections, list) else ()
    return _Parsed(
        score=score,
        summary=str(data.get("summary", "")),
        findings=findings,
        sections=sections,
        degraded=False,
    )
