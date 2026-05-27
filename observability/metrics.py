"""Metric declarations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MetricKind(StrEnum):
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    UP_DOWN_COUNTER = "up_down_counter"


@dataclass(frozen=True, slots=True)
class MetricSpec:
    name: str
    kind: MetricKind
    description: str = ""
    unit: str = ""
