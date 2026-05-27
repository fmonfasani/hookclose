"""Canonical workflow state enum.

These are the **runtime-level** lifecycle states shared across all workflow
definitions. Each definition can additionally declare its own *application*
states inside the DRAFTING/RUNNING phase via the StateMachine API.
"""

from __future__ import annotations

from enum import StrEnum


class WorkflowState(StrEnum):
    """Coarse lifecycle states tracked by the runtime for every workflow."""

    PENDING = "pending"  # accepted, not yet scheduled
    SCHEDULED = "scheduled"  # placed on a queue
    RUNNING = "running"  # at least one step has executed
    WAITING = "waiting"  # awaiting an external signal/event
    SUSPENDED = "suspended"  # paused by operator
    SUCCEEDED = "succeeded"  # terminal
    FAILED = "failed"  # terminal — recoverable was exhausted
    CANCELLED = "cancelled"  # terminal — operator-initiated
    COMPENSATED = "compensated"  # terminal — saga rollback completed


TerminalState: frozenset[WorkflowState] = frozenset(
    {
        WorkflowState.SUCCEEDED,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
        WorkflowState.COMPENSATED,
    },
)
