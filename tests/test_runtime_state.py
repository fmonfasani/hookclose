"""Unit tests for deterministic runtime-state persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.state import RuntimeState, RuntimeStateStore

pytestmark = pytest.mark.unit


def test_load_returns_defaults_when_file_absent(tmp_path: Path) -> None:
    store = RuntimeStateStore(tmp_path / "missing.json")
    state = store.load()
    assert state.runtime_state == "BOOTSTRAPPING"
    assert state.completed_prompts == []


def test_save_then_load_roundtrip(tmp_path: Path) -> None:
    store = RuntimeStateStore(tmp_path / "state.json")
    saved = store.save(RuntimeState(current_prompt=19, runtime_state="RUNTIME_CORE"))
    assert saved.updated_at is not None

    reloaded = store.load()
    assert reloaded.current_prompt == 19
    assert reloaded.runtime_state == "RUNTIME_CORE"


def test_save_is_atomic_and_sorted(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    store = RuntimeStateStore(target)
    store.save(RuntimeState())
    # No stray temp files left behind.
    assert list(tmp_path.glob(".system_state-*.tmp")) == []
    # Keys are serialized sorted for review-friendly diffs.
    text = target.read_text(encoding="utf-8")
    assert text.index("architecture_version") < text.index("current_phase")
    assert text.endswith("\n")


def test_mark_completed_is_idempotent_and_advances_pointer() -> None:
    state = RuntimeState(current_prompt=19, failed_prompts=[19])
    advanced = state.mark_completed(19).mark_completed(19)
    assert advanced.completed_prompts == [19]
    assert advanced.failed_prompts == []
    assert advanced.current_prompt == 20


def test_mark_failed_records_without_completing() -> None:
    state = RuntimeState(current_prompt=20).mark_failed(20)
    assert state.failed_prompts == [20]
    assert 20 not in state.completed_prompts


def test_update_applies_mutation_and_persists(tmp_path: Path) -> None:
    store = RuntimeStateStore(tmp_path / "state.json")
    store.save(RuntimeState(current_prompt=19))
    result = store.update(lambda s: s.mark_completed(19).transition("PROVIDERS"))
    assert result.runtime_state == "PROVIDERS"
    assert store.load().completed_prompts == [19]
