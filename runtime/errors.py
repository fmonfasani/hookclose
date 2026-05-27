"""Domain-level error hierarchy.

These are the *only* exceptions that should escape a contract boundary.
Adapters MUST translate framework-specific exceptions into one of these.
"""

from __future__ import annotations


class AineError(Exception):
    """Root of all AINE domain errors."""

    code: str = "aine.unknown"


class ConfigurationError(AineError):
    code = "aine.config"


class ValidationError(AineError):
    code = "aine.validation"


class NotFoundError(AineError):
    code = "aine.not_found"


class PermissionDeniedError(AineError):
    code = "aine.permission_denied"


class InfrastructureError(AineError):
    """Wraps any underlying I/O / framework failure (DB, Redis, HTTP, …)."""

    code = "aine.infrastructure"


class DeterminismViolation(AineError):
    """Raised when a replay produces a state different from the original run."""

    code = "aine.determinism_violation"


class SandboxViolation(AineError):
    """The sandbox boundary was crossed (network leak, OOM, timeout, …)."""

    code = "aine.sandbox_violation"
