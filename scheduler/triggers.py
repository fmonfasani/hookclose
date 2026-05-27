"""Trigger types — declare *when* something should run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from scheduler.cron import CronExpression


@dataclass(frozen=True, slots=True)
class CronTrigger:
    cron: CronExpression


@dataclass(frozen=True, slots=True)
class IntervalTrigger:
    interval: timedelta
    jitter: timedelta | None = None


@dataclass(frozen=True, slots=True)
class OneShotTrigger:
    fire_at: datetime


@dataclass(frozen=True, slots=True)
class EventTrigger:
    """Fires whenever a matching event is observed on the bus."""

    topic: str
    event_type: str
    event_version: int | None = None


Trigger = CronTrigger | IntervalTrigger | OneShotTrigger | EventTrigger
