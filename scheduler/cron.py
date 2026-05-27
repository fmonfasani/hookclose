"""Cron expression wrapper. Validation logic lives in the adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CronExpression:
    """A 5- or 6-field cron expression.

    Validation is performed by the scheduler adapter at registration time.
    """

    expression: str
    timezone: str = "UTC"

    def __str__(self) -> str:
        return f"{self.expression} ({self.timezone})"
