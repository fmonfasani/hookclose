"""Queue topology.

Queues isolate workloads with different SLAs (priority, latency, capacity).
"""

from __future__ import annotations

from enum import StrEnum


class QueueName(StrEnum):
    DEFAULT = "default"
    CODEGEN = "codegen"
    REVIEW = "review"
    TESTING = "testing"
    REPAIR = "repair"
    INGEST = "ingest"
    SCHEDULER = "scheduler"


def declare_queues() -> tuple[QueueName, ...]:
    return tuple(QueueName)
