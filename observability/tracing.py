"""Distributed tracing primitives."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from enum import StrEnum
from typing import Any


class SpanKind(StrEnum):
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class TracerBase(ABC):
    @abstractmethod
    def span(
        self,
        name: str,
        *,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Mapping[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[Any]:
        raise NotImplementedError
