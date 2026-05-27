"""Unit tests for the SelfHealingRuntime (deterministic, bounded repair)."""

from __future__ import annotations

import pytest

from events.base import DomainEvent
from orchestration.self_healing import (
    FailureAnalyzer,
    FailureCategory,
    RepairAction,
    RepairPolicy,
    SelfHealingRuntime,
    StacktraceParser,
)

pytestmark = pytest.mark.unit

_TRACEBACK = """Traceback (most recent call last):
  File "app.py", line 42, in handler
    do_thing()
  File "lib.py", line 7, in do_thing
    raise ValueError("bad value 0x7f at id 1234")
ValueError: bad value 0x7f at id 1234
"""

_IMPORT_FAIL = """Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import nonexistent
ModuleNotFoundError: No module named 'nonexistent'
"""

_ASSERT_FAIL = """Traceback (most recent call last):
  File "test_x.py", line 10, in test_it
    assert result == 5
AssertionError: assert 4 == 5
"""

_TIMEOUT = "step timed out after 120s"


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


# --- parsing / analysis ----------------------------------------------------


def test_stacktrace_parser_extracts_exception_and_frames() -> None:
    tb = StacktraceParser().parse(_TRACEBACK)
    assert tb.exception_type == "ValueError"
    assert tb.last_frame is not None
    assert tb.last_frame.file == "lib.py"
    assert tb.last_frame.line == 7


def test_signature_is_stable_across_volatile_tokens() -> None:
    analyzer = FailureAnalyzer()
    a = analyzer.analyze(_TRACEBACK)
    b = analyzer.analyze(_TRACEBACK.replace("0x7f", "0x9c").replace("1234", "9999"))
    # Addresses/numbers are normalized, so the signature is identical.
    assert a.signature.key() == b.signature.key()


def test_categorization() -> None:
    analyzer = FailureAnalyzer()
    assert analyzer.analyze(_IMPORT_FAIL).signature.category is FailureCategory.DEPENDENCY
    assert analyzer.analyze(_ASSERT_FAIL).signature.category is FailureCategory.ASSERTION
    assert analyzer.analyze(_TIMEOUT).signature.category is FailureCategory.TIMEOUT


# --- decisions -------------------------------------------------------------


async def test_deterministic_category_fixed_mechanically_first() -> None:
    runtime = SelfHealingRuntime()
    decision = await runtime.handle_failure("t1", _IMPORT_FAIL)  # DEPENDENCY -> deterministic
    assert decision.action is RepairAction.DETERMINISTIC_FIX


async def test_timeout_retries_once_then_repairs() -> None:
    runtime = SelfHealingRuntime()
    first = await runtime.handle_failure("t1", _TIMEOUT)
    assert first.action is RepairAction.RETRY
    second = await runtime.handle_failure("t1", _TIMEOUT)
    assert second.action is RepairAction.LLM_REPAIR


async def test_repair_attempts_are_bounded_then_escalate() -> None:
    bus = RecordingBus()
    runtime = SelfHealingRuntime(policy=RepairPolicy(max_repair_attempts=2), event_bus=bus)
    # Each non-deterministic failure consumes one repair attempt.
    a = await runtime.handle_failure("t1", _ASSERT_FAIL)
    b = await runtime.handle_failure("t1", _ASSERT_FAIL)
    c = await runtime.handle_failure("t1", _ASSERT_FAIL)
    assert a.action is RepairAction.LLM_REPAIR
    assert b.action is RepairAction.LLM_REPAIR
    assert c.action is RepairAction.ESCALATE
    assert any(e.event_type == "healing.escalated" for e in bus.events)


async def test_recurring_regression_rolls_back() -> None:
    bus = RecordingBus()
    rolled: list[tuple[str, str]] = []

    async def rollback(task_id: str, to_ref: str) -> None:
        rolled.append((task_id, to_ref))

    # deterministic_first off so a recurring non-deterministic signature can hit rollback
    # before exhausting attempts; rollback after 3 occurrences.
    policy = RepairPolicy(
        max_repair_attempts=5, deterministic_first=False, rollback_after_repeats=3
    )
    runtime = SelfHealingRuntime(policy=policy, event_bus=bus, rollback=rollback)

    actions = [(await runtime.handle_failure("t1", _IMPORT_FAIL)).action for _ in range(3)]
    assert actions[-1] is RepairAction.ROLLBACK
    assert rolled == [("t1", "last-good")]
    assert any(e.event_type == "healing.rolled_back" for e in bus.events)


async def test_every_failure_is_analyzed_and_decided_events_emitted() -> None:
    bus = RecordingBus()
    runtime = SelfHealingRuntime(event_bus=bus)
    await runtime.handle_failure("t1", _ASSERT_FAIL)
    types = {e.event_type for e in bus.events}
    assert "healing.failure_analyzed" in types
    assert "healing.repair_decided" in types
