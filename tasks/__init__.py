"""
tasks/ — Celery integration scaffolding.

Tasks are durable, async, retryable units of work that run *outside* the
request-response cycle. They are the bridge between the workflow engine and
real I/O work.

This package contains:
  - the Celery application factory
  - queue declarations
  - the abstract task base class
  - routing rules

No business tasks are implemented yet.
"""

from tasks.app import create_celery_app
from tasks.base import TaskBase
from tasks.queues import QueueName, declare_queues
from tasks.routing import default_routes

__all__ = [
    "QueueName",
    "TaskBase",
    "create_celery_app",
    "declare_queues",
    "default_routes",
]
