"""Unit tests for AutonomousTaskChaining and the dependency graph."""

from __future__ import annotations

import pytest

from events.base import DomainEvent
from orchestration.chaining import ChainPolicy, InMemoryChainStore, TaskChainer, chain_meta
from orchestration.graph import CycleError, TaskDependencyGraph
from tasks.models import Task

pytestmark = pytest.mark.unit


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


# --- graph -----------------------------------------------------------------


def test_graph_ready_respects_prerequisites() -> None:
    g = TaskDependencyGraph()
    g.add_dependency("b", "a")
    assert g.ready() == {"a"}
    g.mark_done("a")
    assert g.ready() == {"b"}
    g.mark_done("b")
    assert g.is_complete()


def test_graph_rejects_cycles() -> None:
    g = TaskDependencyGraph()
    g.add_dependency("b", "a")
    g.add_dependency("c", "b")
    with pytest.raises(CycleError):
        g.add_dependency("a", "c")  # would close the loop a->c->b->a


# --- chaining --------------------------------------------------------------


async def test_codegen_completion_chains_to_testing() -> None:
    bus = RecordingBus()
    chainer = TaskChainer(event_bus=bus)
    nxt = await chainer.on_completed(Task(task_type="codegen.feature"))
    assert len(nxt) == 1
    assert nxt[0].task_type == "testing.auto"
    assert any(e.event_type == "chaining.next_generated" for e in bus.events)


async def test_full_pipeline_codegen_to_deploy_then_terminal() -> None:
    chainer = TaskChainer()
    codegen = Task(task_type="codegen.x")
    testing = (await chainer.on_completed(codegen))[0]
    review = (await chainer.on_completed(testing))[0]
    deploy = (await chainer.on_completed(review))[0]
    assert [t.task_type for t in (testing, review, deploy)] == [
        "testing.auto",
        "review.auto",
        "deploy.auto",
    ]
    # deploy is terminal — no further chaining
    assert await chainer.on_completed(deploy) == []
    # chain metadata threads the same root and increments depth
    assert chain_meta(deploy).root == codegen.id
    assert chain_meta(deploy).depth == 3


async def test_failure_creates_repair_task() -> None:
    bus = RecordingBus()
    chainer = TaskChainer(event_bus=bus)
    failed = Task(task_type="codegen.x", attempts=1, max_attempts=3)
    repair = await chainer.on_failed(failed)
    assert len(repair) == 1
    assert repair[0].task_type == "repair.auto"
    assert repair[0].payload["repairs_task_id"] == failed.id
    assert any(e.event_type == "chaining.repair_created" for e in bus.events)


async def test_exhausted_retries_escalate_instead_of_repair() -> None:
    bus = RecordingBus()
    chainer = TaskChainer(event_bus=bus)
    failed = Task(task_type="codegen.x", attempts=3, max_attempts=3)
    assert await chainer.on_failed(failed) == []
    assert any(e.event_type == "chaining.escalation_raised" for e in bus.events)


async def test_chain_depth_is_bounded_no_infinite_loop() -> None:
    bus = RecordingBus()
    # Self-continuing policy ("step" -> "step") would loop forever without the bound.
    policy = ChainPolicy(continuation={"step": "step"}, max_depth=3)
    chainer = TaskChainer(policy=policy, event_bus=bus)

    task = Task(task_type="step.0")
    count = 0
    while True:
        produced = await chainer.on_completed(task)
        if not produced:
            break
        task = produced[0]
        count += 1
        assert count <= 10  # guardrail so a real infinite loop fails the test

    assert count == 3  # exactly max_depth tasks, then terminated
    assert any(e.event_type == "chaining.terminated" for e in bus.events)


async def test_generated_tasks_recorded_in_store() -> None:
    store = InMemoryChainStore()
    chainer = TaskChainer(store=store)
    root = Task(task_type="codegen.x")
    await chainer.on_completed(root)
    assert root.id in store.generated
    assert store.generated[root.id][0].task_type == "testing.auto"


async def test_graph_links_child_to_parent() -> None:
    chainer = TaskChainer()
    root = Task(task_type="codegen.x")
    child = (await chainer.on_completed(root))[0]
    # root is done; child becomes ready once its parent (root) is done
    assert child.id in chainer.graph.ready()
