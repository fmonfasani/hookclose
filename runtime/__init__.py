"""
runtime/ — Operational kernel.

The runtime is the only layer that knows how to:
  - load configuration
  - construct the component graph (DI container)
  - bring services up/down in a deterministic order
  - dispatch workflows
  - expose the public HTTP surface (FastAPI)

It is the **composition root**. Everything below depends only on contracts;
the runtime is where contracts are bound to concrete adapters.
"""

from runtime.config import RuntimeSettings, get_settings
from runtime.errors import (
    AineError,
    ConfigurationError,
    InfrastructureError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from runtime.registry import ComponentRegistry
from runtime.types import ActorId, CorrelationId, RunId, TenantId, WorkflowId

__all__ = [
    "ActorId",
    "AineError",
    "ComponentRegistry",
    "ConfigurationError",
    "CorrelationId",
    "InfrastructureError",
    "NotFoundError",
    "PermissionDeniedError",
    "RunId",
    "RuntimeSettings",
    "TenantId",
    "ValidationError",
    "WorkflowId",
    "get_settings",
]
