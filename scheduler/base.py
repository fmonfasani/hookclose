"""Abstract scheduler base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from scheduler.triggers import Trigger


class SchedulerBase(ABC):
    @abstractmethod
    async def register(
        self,
        name: str,
        trigger: Trigger,
        task_name: str,
        payload: Mapping[str, Any] | None = None,
    ) -> str:
        """Returns a schedule id."""

    @abstractmethod
    async def unregister(self, schedule_id: str) -> None:
        raise NotImplementedError
