"""Deterministic orchestration: task dependency graph + autonomous chaining.

This layer decides *what work comes next* from task outcomes. It generates tasks
and records the dependency graph; it does not execute them (workers do) and never
calls a provider directly.
"""

from __future__ import annotations

# Importing the events module registers chaining events in the global EVENT_REGISTRY.
import events.domain.chaining
from orchestration.chaining import (
    ChainMeta,
    ChainPolicy,
    ChainStore,
    InMemoryChainStore,
    TaskChainer,
    chain_meta,
)
from orchestration.graph import CycleError, TaskDependencyGraph

__all__ = [
    "ChainMeta",
    "ChainPolicy",
    "ChainStore",
    "CycleError",
    "InMemoryChainStore",
    "TaskChainer",
    "TaskDependencyGraph",
    "chain_meta",
]
