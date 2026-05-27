"""AutonomousTaskChaining — generate follow-up work from task outcomes.

Deterministic, bounded continuation of the build pipeline:

    codegen  --done-->  testing  --done-->  review  --done-->  deploy  (terminal)
    repair   --done-->  testing
    <any>    --failed (attempts left)-->  repair task
    <any>    --failed (attempts exhausted)-->  escalation (terminal)

Every generated task carries chain metadata (``payload["_chain"]`` = root/parent/
depth). Chains are bounded two ways — a per-edge cycle check in the dependency graph
and a hard ``max_depth`` — so they can never run forever. Every decision is persisted
(audit trail) and emitted as an event. The chainer generates tasks; it does not run
or enqueue them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from contracts.event_bus import EventBusPort
from events.base import DomainEvent
from events.domain.chaining import (
    ChainTerminated,
    EscalationRaised,
    NextTaskGenerated,
    RepairTaskCreated,
)
from orchestration.graph import TaskDependencyGraph
from tasks.models import Task, TaskStatus

_CHAIN_KEY = "_chain"


@dataclass(frozen=True, slots=True)
class ChainMeta:
    root: str
    parent: str | None
    depth: int

    def to_payload(self) -> dict[str, object]:
        return {"root": self.root, "parent": self.parent, "depth": self.depth}


def chain_meta(task: Task) -> ChainMeta:
    """Read chain metadata from a task, treating un-chained tasks as roots."""
    raw = task.payload.get(_CHAIN_KEY)
    if isinstance(raw, dict):
        return ChainMeta(
            root=str(raw.get("root", task.id)),
            parent=raw.get("parent"),
            depth=int(raw.get("depth", 0)),
        )
    return ChainMeta(root=task.id, parent=None, depth=0)


@dataclass(frozen=True, slots=True)
class ChainPolicy:
    """Configurable continuation graph + depth bound."""

    continuation: Mapping[str, str] = field(default_factory=dict)
    max_depth: int = 8

    @classmethod
    def default(cls) -> ChainPolicy:
        return cls(
            continuation={
                "codegen": "testing",
                "testing": "review",
                "review": "deploy",
                "repair": "testing",
            }
        )

    def next_head(self, task_type: str) -> str | None:
        head = task_type.split(".", 1)[0] if task_type else ""
        return self.continuation.get(head)


@runtime_checkable
class ChainStore(Protocol):
    """Audit trail of generated tasks, keyed by chain root."""

    async def record(self, root: str, task: Task) -> None: ...


@dataclass(slots=True)
class InMemoryChainStore:
    generated: dict[str, list[Task]] = field(default_factory=dict)

    async def record(self, root: str, task: Task) -> None:
        self.generated.setdefault(root, []).append(task)


class TaskChainer:
    def __init__(
        self,
        *,
        policy: ChainPolicy | None = None,
        store: ChainStore | None = None,
        event_bus: EventBusPort | None = None,
        graph: TaskDependencyGraph | None = None,
    ) -> None:
        self._policy = policy or ChainPolicy.default()
        self._store: ChainStore = store or InMemoryChainStore()
        self._bus = event_bus
        self._graph = graph or TaskDependencyGraph()

    @property
    def graph(self) -> TaskDependencyGraph:
        return self._graph

    async def on_completed(self, task: Task) -> list[Task]:
        """Generate the continuation task for a successfully completed task."""
        self._graph.mark_done(task.id)
        meta = chain_meta(task)
        next_head = self._policy.next_head(task.task_type)
        if next_head is None:
            return []  # terminal stage — nothing to chain
        if meta.depth + 1 > self._policy.max_depth:
            await self._terminate(meta.root, "max chain depth reached", meta.depth)
            return []

        child = self._make_child(task, f"{next_head}.auto", meta)
        await self._link_and_record(task, child, meta)
        await self._emit(
            NextTaskGenerated(
                parent_task_id=task.id,
                new_task_id=child.id,
                new_task_type=child.task_type,
                trigger=f"{task.task_type}:completed",
                depth=meta.depth + 1,
            )
        )
        return [child]

    async def on_failed(self, task: Task) -> list[Task]:
        """Create a repair task, or escalate if retries are exhausted."""
        self._graph.add_task(task.id)
        meta = chain_meta(task)

        if task.attempts >= task.max_attempts:
            await self._emit(
                EscalationRaised(task_id=task.id, reason="retries exhausted", depth=meta.depth)
            )
            return []
        if meta.depth + 1 > self._policy.max_depth:
            await self._terminate(meta.root, "max chain depth reached", meta.depth)
            return []

        repair = self._make_child(task, "repair.auto", meta)
        repair.payload["repairs_task_id"] = task.id
        repair.payload["original_task_type"] = task.task_type
        await self._link_and_record(task, repair, meta)
        await self._emit(
            RepairTaskCreated(
                failed_task_id=task.id,
                repair_task_id=repair.id,
                attempt=task.attempts + 1,
                depth=meta.depth + 1,
            )
        )
        return [repair]

    # --- helpers -----------------------------------------------------------

    def _make_child(self, parent: Task, task_type: str, meta: ChainMeta) -> Task:
        child_meta = ChainMeta(root=meta.root, parent=parent.id, depth=meta.depth + 1)
        return Task(
            workflow_id=parent.workflow_id,
            status=TaskStatus.PENDING,
            task_type=task_type,
            provider=parent.provider,
            payload={_CHAIN_KEY: child_meta.to_payload()},
            max_attempts=parent.max_attempts,
        )

    async def _link_and_record(self, parent: Task, child: Task, meta: ChainMeta) -> None:
        self._graph.add_dependency(child.id, parent.id)
        await self._store.record(meta.root, child)

    async def _terminate(self, root: str, reason: str, depth: int) -> None:
        await self._emit(ChainTerminated(root_task_id=root, reason=reason, depth=depth))

    async def _emit(self, event: DomainEvent) -> None:
        if self._bus is not None:
            await self._bus.publish(event)
