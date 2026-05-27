"""
observability/ — Tracing, metrics, structured logs, audit trail.

The package wraps OpenTelemetry behind the `TelemetryPort`. Nothing outside
of this package and `adapters/telemetry/` should import `opentelemetry`
directly — that keeps the rest of the codebase swappable.
"""

from observability.audit import AuditEntry, AuditTrailBase
from observability.health import HealthCheck, HealthReport, HealthStatus
from observability.logging import LoggerBase
from observability.metrics import MetricKind, MetricSpec
from observability.tracing import SpanKind, TracerBase

__all__ = [
    "AuditEntry",
    "AuditTrailBase",
    "HealthCheck",
    "HealthReport",
    "HealthStatus",
    "LoggerBase",
    "MetricKind",
    "MetricSpec",
    "SpanKind",
    "TracerBase",
]
