"""Abstract task base — concrete tasks subclass this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class TaskBase(ABC):
    """Tasks are stateless, idempotent units of work.

    The runtime guarantees at-least-once delivery. Implementations MUST use
    `payload["idempotency_key"]` (or an equivalent) to deduplicate.
    """

    name: str

    @abstractmethod
    async def run(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError
