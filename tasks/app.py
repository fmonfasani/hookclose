"""Celery application factory.

Built but **not** loaded with real tasks. Concrete tasks register themselves
once they exist.
"""

from __future__ import annotations

from celery import Celery

from runtime.config import RuntimeSettings, get_settings
from tasks.queues import declare_queues
from tasks.routing import default_routes


def create_celery_app(settings: RuntimeSettings | None = None) -> Celery:
    """Build the project's Celery application.

    Note: this module is the canonical `-A tasks.app` target for `celery
    worker` and `celery beat`.
    """
    settings = settings or get_settings()

    app = Celery(
        "aine",
        broker=settings.celery.broker_url,
        backend=settings.celery.result_backend,
    )
    app.conf.task_default_queue = settings.celery.task_default_queue
    app.conf.task_routes = default_routes()
    app.conf.task_queues = tuple({"name": q.value} for q in declare_queues())
    app.conf.task_acks_late = True
    app.conf.task_reject_on_worker_lost = True
    app.conf.task_track_started = True
    app.conf.worker_prefetch_multiplier = 1
    app.conf.broker_connection_retry_on_startup = True
    return app


# Module-level Celery instance discovered by `celery -A tasks.app`.
app = create_celery_app()
