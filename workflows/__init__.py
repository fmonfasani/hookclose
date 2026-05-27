"""
workflows/ — Deterministic state machines.

Workflows are the orchestration backbone of AINE. They are:
  - deterministic: given the same event log + same definition, replay yields
    the same final state
  - explicit: every state and every transition is declared up-front
  - event-emitting: every transition produces a `WorkflowStateTransitioned`
  - LLM-free at the orchestration layer: LLMs are tools called from inside
    states, never the thing that decides which state comes next

A workflow definition is the (states, transitions, initial state) tuple plus
optional guards and on-enter/on-exit hooks.
"""

from workflows.base import WorkflowDefinition, WorkflowInstance
from workflows.machine import StateMachine, Transition, TransitionGuard
from workflows.state import TerminalState, WorkflowState

__all__ = [
    "StateMachine",
    "TerminalState",
    "Transition",
    "TransitionGuard",
    "WorkflowDefinition",
    "WorkflowInstance",
    "WorkflowState",
]
