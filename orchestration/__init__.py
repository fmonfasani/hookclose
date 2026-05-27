"""Deterministic orchestration: task dependency graph + autonomous chaining.

This layer decides *what work comes next* from task outcomes. It generates tasks
and records the dependency graph; it does not execute them (workers do) and never
calls a provider directly.
"""

from __future__ import annotations

# Importing the events modules registers their events in the global EVENT_REGISTRY.
import events.domain.chaining
import events.domain.healing
from orchestration.chaining import (
    ChainMeta,
    ChainPolicy,
    ChainStore,
    InMemoryChainStore,
    TaskChainer,
    chain_meta,
)
from orchestration.graph import CycleError, TaskDependencyGraph
from orchestration.self_healing import (
    FailureAnalysis,
    FailureAnalyzer,
    FailureCategory,
    FailureMemory,
    RepairAction,
    RepairDecision,
    RepairHistory,
    RepairPolicy,
    SelfHealingRuntime,
    StacktraceParser,
)

__all__ = [
    "ChainMeta",
    "ChainPolicy",
    "ChainStore",
    "CycleError",
    "FailureAnalysis",
    "FailureAnalyzer",
    "FailureCategory",
    "FailureMemory",
    "InMemoryChainStore",
    "RepairAction",
    "RepairDecision",
    "RepairHistory",
    "RepairPolicy",
    "SelfHealingRuntime",
    "StacktraceParser",
    "TaskChainer",
    "TaskDependencyGraph",
    "chain_meta",
]
