"""Telemetry port — traces, metrics, structured logs."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TelemetryPort(Protocol):
    """Wraps OpenTelemetry so the rest of the codebase doesn't import
    `opentelemetry.*` directly. This keeps the domain dependency-free and
    makes telemetry swappable in tests."""

    def span(
        self,
        name: str,
        *,
        attributes: Mapping[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[Any]: ...

    def counter(self, name: str, *, description: str = "", unit: str = "") -> Any: ...

    def histogram(self, name: str, *, description: str = "", unit: str = "") -> Any: ...

    def gauge(self, name: str, *, description: str = "", unit: str = "") -> Any: ...

    def log(
        self,
        level: str,
        message: str,
        *,
        attributes: Mapping[str, Any] | None = None,
    ) -> None: ...
