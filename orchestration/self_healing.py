"""SelfHealingRuntime — bounded, deterministic-first failure repair.

Pipeline: parse the failure output -> classify it into a stable signature ->
decide a repair action under hard limits -> record it -> emit it. The decision is
a pure function of (analysis, failure memory, repair history, policy), so it is
deterministic and auditable.

Guarantees the prompt requires:
  - **bounded**: a signature can be repaired at most ``max_repair_attempts`` times
    before it escalates; repeated regressions roll back instead of looping.
  - **deterministic-first**: deterministically fixable categories (lint/format/deps)
    are fixed mechanically before any LLM repair is considered.
  - **auditable**: every failure and decision is recorded (memory + history) and
    emitted as an event.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
import re

from contracts.event_bus import EventBusPort
from events.base import DomainEvent
from events.domain.healing import (
    FailureAnalyzed,
    RepairDecisionMade,
    RepairEscalated,
    RolledBack,
)


class FailureCategory(StrEnum):
    SYNTAX = "syntax"
    IMPORT = "import"
    DEPENDENCY = "dependency"
    ASSERTION = "assertion"
    TIMEOUT = "timeout"
    LINT = "lint"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"


# Categories that can be fixed mechanically without a model.
_DETERMINISTIC: frozenset[FailureCategory] = frozenset(
    {FailureCategory.LINT, FailureCategory.DEPENDENCY}
)


class RepairAction(StrEnum):
    RETRY = "retry"
    DETERMINISTIC_FIX = "deterministic_fix"
    LLM_REPAIR = "llm_repair"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"


@dataclass(frozen=True, slots=True)
class Frame:
    file: str
    line: int
    func: str


@dataclass(frozen=True, slots=True)
class ParsedTraceback:
    exception_type: str
    message: str
    frames: tuple[Frame, ...]

    @property
    def last_frame(self) -> Frame | None:
        return self.frames[-1] if self.frames else None


@dataclass(frozen=True, slots=True)
class FailureSignature:
    category: FailureCategory
    exception_type: str
    location: str  # "file:line" or ""
    normalized_message: str

    def key(self) -> str:
        raw = f"{self.category}|{self.exception_type}|{self.location}|{self.normalized_message}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]  # noqa: S324 — id, not security


@dataclass(frozen=True, slots=True)
class FailureAnalysis:
    signature: FailureSignature
    summary: str
    deterministic_fixable: bool
    traceback: ParsedTraceback | None


_FRAME_RE = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>\S+)')
_EXC_RE = re.compile(
    r"^(?P<type>[A-Za-z_][\w.]*(?:Error|Exception|Warning|Failure)): ?(?P<msg>.*)$"
)
_NUM_RE = re.compile(r"\b0x[0-9a-fA-F]+\b|\b\d+\b")


class StacktraceParser:
    """Parses Python-style tracebacks. Tolerant of partial / non-traceback output."""

    def parse(self, text: str) -> ParsedTraceback:
        frames = tuple(
            Frame(file=m["file"], line=int(m["line"]), func=m["func"])
            for m in _FRAME_RE.finditer(text)
        )
        exc_type, message = "", text.strip().splitlines()[-1] if text.strip() else ""
        for line in reversed(text.strip().splitlines()):
            match = _EXC_RE.match(line.strip())
            if match:
                exc_type, message = match["type"], match["msg"].strip()
                break
        return ParsedTraceback(exception_type=exc_type, message=message, frames=frames)


class FailureAnalyzer:
    def __init__(self, parser: StacktraceParser | None = None) -> None:
        self._parser = parser or StacktraceParser()

    def analyze(self, output: str) -> FailureAnalysis:
        tb = self._parser.parse(output)
        category = self._categorize(tb, output)
        location = ""
        if tb.last_frame is not None:
            location = f"{tb.last_frame.file}:{tb.last_frame.line}"
        signature = FailureSignature(
            category=category,
            exception_type=tb.exception_type or category.value,
            location=location,
            normalized_message=_normalize(tb.message),
        )
        summary = f"{category.value}: {tb.exception_type or 'failure'} {tb.message}".strip()
        return FailureAnalysis(
            signature=signature,
            summary=summary[:300],
            deterministic_fixable=category in _DETERMINISTIC,
            traceback=tb,
        )

    @staticmethod
    def _categorize(tb: ParsedTraceback, output: str) -> FailureCategory:
        exc = tb.exception_type
        if exc in _EXC_CATEGORY:
            return _EXC_CATEGORY[exc]
        lowered = output.lower()
        if "timed out" in lowered:
            return FailureCategory.TIMEOUT
        if "assert" in lowered and "failed" in lowered:
            return FailureCategory.ASSERTION
        if "ruff" in lowered or re.search(r"\b[EWFB]\d{3}\b", output):
            return FailureCategory.LINT
        return FailureCategory.RUNTIME if exc else FailureCategory.UNKNOWN


# Exact exception-type -> category mapping (checked before content heuristics).
_EXC_CATEGORY: dict[str, FailureCategory] = {
    "SyntaxError": FailureCategory.SYNTAX,
    "IndentationError": FailureCategory.SYNTAX,
    "ModuleNotFoundError": FailureCategory.DEPENDENCY,
    "ImportError": FailureCategory.IMPORT,
    "AssertionError": FailureCategory.ASSERTION,
    "TimeoutError": FailureCategory.TIMEOUT,
}


def _normalize(message: str) -> str:
    """Strip volatile tokens (addresses, line numbers) so signatures are stable."""
    return _NUM_RE.sub("N", message).strip()[:160]


@dataclass(frozen=True, slots=True)
class RepairPolicy:
    max_repair_attempts: int = 3
    deterministic_first: bool = True
    rollback_after_repeats: int = 3  # same signature recurs this many times -> rollback


@dataclass(slots=True)
class FailureMemory:
    """Counts how often each failure signature has been seen."""

    _counts: dict[str, int] = field(default_factory=dict)

    def record(self, signature: FailureSignature) -> int:
        key = signature.key()
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key]

    def occurrences(self, signature: FailureSignature) -> int:
        return self._counts.get(signature.key(), 0)


@dataclass(slots=True)
class RepairHistory:
    """Records repair attempts per signature for bounding the loop."""

    _attempts: dict[str, int] = field(default_factory=dict)
    log: list[tuple[str, str]] = field(default_factory=list)  # (signature_key, action)

    def attempts_for(self, key: str) -> int:
        return self._attempts.get(key, 0)

    def record(self, key: str, action: RepairAction) -> None:
        if action in (RepairAction.DETERMINISTIC_FIX, RepairAction.LLM_REPAIR, RepairAction.RETRY):
            self._attempts[key] = self._attempts.get(key, 0) + 1
        self.log.append((key, action.value))


@dataclass(frozen=True, slots=True)
class RepairDecision:
    action: RepairAction
    category: FailureCategory
    signature_key: str
    attempt: int
    reason: str


RollbackFn = Callable[[str, str], Awaitable[None]]  # (task_id, to_ref) -> None


class SelfHealingRuntime:
    def __init__(
        self,
        *,
        policy: RepairPolicy | None = None,
        memory: FailureMemory | None = None,
        history: RepairHistory | None = None,
        analyzer: FailureAnalyzer | None = None,
        event_bus: EventBusPort | None = None,
        rollback: RollbackFn | None = None,
    ) -> None:
        self._policy = policy or RepairPolicy()
        self._memory = memory or FailureMemory()
        self._history = history or RepairHistory()
        self._analyzer = analyzer or FailureAnalyzer()
        self._bus = event_bus
        self._rollback = rollback

    async def handle_failure(
        self, task_id: str, failure_output: str, *, rollback_ref: str = "last-good"
    ) -> RepairDecision:
        analysis = self._analyzer.analyze(failure_output)
        sig = analysis.signature
        occurrences = self._memory.record(sig)
        prior_attempts = self._history.attempts_for(sig.key())

        await self._emit(
            FailureAnalyzed(
                task_id=task_id,
                category=sig.category.value,
                signature_key=sig.key(),
                deterministic_fixable=analysis.deterministic_fixable,
                occurrences=occurrences,
            )
        )

        action, reason = self._decide(analysis, prior_attempts, occurrences)
        self._history.record(sig.key(), action)
        attempt = self._history.attempts_for(sig.key())

        decision = RepairDecision(
            action=action,
            category=sig.category,
            signature_key=sig.key(),
            attempt=attempt,
            reason=reason,
        )
        await self._emit(
            RepairDecisionMade(task_id=task_id, action=action.value, attempt=attempt, reason=reason)
        )
        if action is RepairAction.ROLLBACK:
            if self._rollback is not None:
                await self._rollback(task_id, rollback_ref)
            await self._emit(RolledBack(task_id=task_id, to_ref=rollback_ref, reason=reason))
        elif action is RepairAction.ESCALATE:
            await self._emit(
                RepairEscalated(task_id=task_id, reason=reason, attempts=prior_attempts)
            )
        return decision

    def _decide(
        self, analysis: FailureAnalysis, prior_attempts: int, occurrences: int
    ) -> tuple[RepairAction, str]:
        if prior_attempts >= self._policy.max_repair_attempts:
            return RepairAction.ESCALATE, "repair attempts exhausted"
        if analysis.signature.category is FailureCategory.TIMEOUT and prior_attempts == 0:
            return RepairAction.RETRY, "transient timeout — retry once"
        if analysis.deterministic_fixable and self._policy.deterministic_first:
            return (
                RepairAction.DETERMINISTIC_FIX,
                f"{analysis.signature.category.value} is mechanically fixable",
            )
        if occurrences >= self._policy.rollback_after_repeats:
            return RepairAction.ROLLBACK, "recurring regression — rolling back"
        return RepairAction.LLM_REPAIR, "needs reasoning-based repair"

    async def _emit(self, event: DomainEvent) -> None:
        if self._bus is not None:
            await self._bus.publish(event)
