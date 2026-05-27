"""Task dependency graph — deterministic readiness with cycle prevention.

A directed graph of task-id dependencies (``task`` depends on ``prerequisite``).
It answers "what is ready to run now?" (all prerequisites done) and refuses edges
that would create a cycle, which is the structural guard against infinite chains.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class CycleError(ValueError):
    """Raised when adding a dependency edge would create a cycle."""


@dataclass(slots=True)
class TaskDependencyGraph:
    _deps: dict[str, set[str]] = field(default_factory=dict)  # task -> prerequisites
    _done: set[str] = field(default_factory=set)

    def add_task(self, task_id: str) -> None:
        self._deps.setdefault(task_id, set())

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Record that ``task_id`` requires ``depends_on`` first."""
        self.add_task(task_id)
        self.add_task(depends_on)
        if task_id == depends_on or self._reaches(depends_on, task_id):
            raise CycleError(f"{task_id} -> {depends_on} would create a cycle")
        self._deps[task_id].add(depends_on)

    def mark_done(self, task_id: str) -> None:
        self.add_task(task_id)
        self._done.add(task_id)

    def is_done(self, task_id: str) -> bool:
        return task_id in self._done

    def ready(self) -> set[str]:
        """Tasks not yet done whose prerequisites are all done."""
        return {
            task
            for task, deps in self._deps.items()
            if task not in self._done and deps <= self._done
        }

    def is_complete(self) -> bool:
        return all(task in self._done for task in self._deps)

    def _reaches(self, start: str, target: str) -> bool:
        """True if ``target`` is reachable from ``start`` following prerequisites."""
        seen: set[str] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node == target:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(self._deps.get(node, set()))
        return False
