"""Structured logging base — bound to structlog by the adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class LoggerBase(ABC):
    @abstractmethod
    def debug(self, event: str, **fields: Any) -> None: ...

    @abstractmethod
    def info(self, event: str, **fields: Any) -> None: ...

    @abstractmethod
    def warning(self, event: str, **fields: Any) -> None: ...

    @abstractmethod
    def error(self, event: str, **fields: Any) -> None: ...

    @abstractmethod
    def bind(self, **fields: Any) -> LoggerBase:
        """Return a child logger with additional bound context fields."""

    @abstractmethod
    def with_correlation(self, correlation_id: str) -> LoggerBase: ...

    def context(self) -> Mapping[str, Any]:
        return {}
