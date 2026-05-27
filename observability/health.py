"""Health check primitives."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass(frozen=True, slots=True)
class HealthReport:
    component: str
    status: HealthStatus
    detail: str = ""
    attributes: Mapping[str, str] = field(default_factory=dict)


class HealthCheck(ABC):
    """A single, named health probe."""

    name: str

    @abstractmethod
    async def check(self) -> HealthReport:
        raise NotImplementedError
