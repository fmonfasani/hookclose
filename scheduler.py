"""Top-level scheduler entrypoint — thin shim.

The runnable scheduler service lives in ``scheduler/main.py`` (it polls Postgres
for pending tasks, dispatches them to provider queues in Redis, emits heartbeats,
and — in later phases — retries failed tasks, recovers dead workers, and routes
via the ComplexityRoutingEngine). This shim just runs it.
"""

from __future__ import annotations

import asyncio

from scheduler.main import main as _service_main


def main() -> None:
    asyncio.run(_service_main())


if __name__ == "__main__":
    main()
