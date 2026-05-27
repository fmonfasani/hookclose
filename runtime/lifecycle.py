"""Process lifecycle hooks: startup/shutdown ordering.

The lifecycle defines a deterministic sequence in which components are
initialised and torn down. Order matters: e.g. the event bus must be ready
before any agent runs, the DB pool must close *after* the API stops accepting
new requests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

Hook = Callable[[], Awaitable[None]]


@dataclass(slots=True)
class LifecycleStage:
    name: str
    on_startup: tuple[Hook, ...] = ()
    on_shutdown: tuple[Hook, ...] = ()


class Lifecycle:
    """Ordered collection of lifecycle stages.

    The runtime executes stages in declared order on startup and in reverse
    order on shutdown. Each stage's hooks run concurrently within the stage;
    stages themselves run sequentially.
    """

    __slots__ = ("_stages",)

    def __init__(self) -> None:
        self._stages: list[LifecycleStage] = []

    def add(self, stage: LifecycleStage) -> None:
        self._stages.append(stage)

    @property
    def stages(self) -> tuple[LifecycleStage, ...]:
        return tuple(self._stages)

    async def startup(self) -> None:
        raise NotImplementedError("runtime.bootstrap will provide the orchestrator")

    async def shutdown(self) -> None:
        raise NotImplementedError("runtime.bootstrap will provide the orchestrator")
