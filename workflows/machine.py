"""State machine primitives.

Pure data — no execution logic. The runtime in `runtime/dispatcher.py` is
responsible for *interpreting* these declarations.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

TransitionGuard = Callable[[Mapping[str, Any]], Awaitable[bool]]


@dataclass(frozen=True, slots=True)
class Transition:
    """A single declared edge in the state machine."""

    from_state: str
    to_state: str
    trigger: str
    guard: TransitionGuard | None = None
    description: str = ""


@dataclass(frozen=True, slots=True)
class StateMachine:
    """Static declaration of a deterministic state machine.

    Validation of well-formedness (no orphans, no unreachable states, exactly
    one initial state, every terminal reachable) is enforced by the runtime
    loader at startup, not here.
    """

    name: str
    version: str
    initial_state: str
    states: frozenset[str]
    terminal_states: frozenset[str]
    transitions: tuple[Transition, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def transitions_from(self, state: str) -> tuple[Transition, ...]:
        return tuple(t for t in self.transitions if t.from_state == state)

    def is_terminal(self, state: str) -> bool:
        return state in self.terminal_states
