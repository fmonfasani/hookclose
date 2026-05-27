"""Episodic memory base class — append-only log abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from contracts.memory import Episode


class EpisodicMemoryBase(ABC):
    """The episodic log is the *source of truth* for deterministic replay."""

    @abstractmethod
    async def append(self, episode: Episode) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        workflow_id: str,
        *,
        since_unix_ms: int | None = None,
    ) -> Iterable[Episode]:
        raise NotImplementedError
