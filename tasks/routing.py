"""Task -> queue routing rules."""

from __future__ import annotations

from collections.abc import Mapping

from tasks.queues import QueueName


def default_routes() -> Mapping[str, Mapping[str, str]]:
    """Map task name prefixes to a queue.

    Wildcard prefix `name.*` routes any task whose dotted name starts with
    the prefix to the named queue.
    """
    return {
        "codegen.*": {"queue": QueueName.CODEGEN.value},
        "review.*": {"queue": QueueName.REVIEW.value},
        "testing.*": {"queue": QueueName.TESTING.value},
        "repair.*": {"queue": QueueName.REPAIR.value},
        "ingest.*": {"queue": QueueName.INGEST.value},
        "scheduler.*": {"queue": QueueName.SCHEDULER.value},
    }
