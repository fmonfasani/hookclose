from __future__ import annotations

import asyncio
from collections.abc import Coroutine
import contextlib
from datetime import UTC, datetime
import json
import logging
import os
import signal
import time
from typing import cast

import asyncpg
import redis.asyncio as aioredis

from tasks.models import TaskStatus
from tasks.repository import TaskRepository

logging.basicConfig(
    level=os.getenv("HOOKCLOSE_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] scheduler: %(message)s",
)
log = logging.getLogger("scheduler")

PG_DSN = (
    f"postgresql://{os.getenv('HOOKCLOSE_POSTGRES_USER', 'hookclose')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PASSWORD', 'hookclose')}"
    f"@{os.getenv('HOOKCLOSE_POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PORT', '5432')}"
    f"/{os.getenv('HOOKCLOSE_POSTGRES_DB', 'hookclose')}"
)
REDIS_URL = os.getenv("HOOKCLOSE_REDIS_URL", "redis://redis:6379/0")
HEARTBEAT_INTERVAL = int(os.getenv("HOOKCLOSE_SCHEDULER_HEARTBEAT_INTERVAL", "5"))
POLL_INTERVAL = int(os.getenv("HOOKCLOSE_SCHEDULER_POLL_INTERVAL", "3"))
PORT = int(os.getenv("HOOKCLOSE_SCHEDULER_PORT", "8100"))

_shutdown = asyncio.Event()
_background_tasks: set[asyncio.Task[None]] = set()


def _spawn(coro: Coroutine[object, object, None]) -> None:
    """Schedule a long-lived task and keep a strong reference to it."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _handle_signal() -> None:
    log.info("received shutdown signal")
    _shutdown.set()


async def health_server() -> None:
    loop = asyncio.get_event_loop()
    server = await loop.create_server(
        HealthHandler,
        host="0.0.0.0",  # noqa: S104 — container-internal binding
        port=PORT,
    )
    log.info("health server listening on 0.0.0.0:%d", PORT)
    async with server:
        await _shutdown.wait()


class HealthHandler(asyncio.Protocol):
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        body = b'{"status":"ok","service":"scheduler"}'
        conn = cast(asyncio.Transport, transport)  # TCP server => connection-oriented
        conn.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            b"Content-Length: %d\r\n\r\n%s" % (len(body), body)
        )
        conn.close()


async def poll_pg(r: aioredis.Redis[str], repo: TaskRepository) -> None:
    while not _shutdown.is_set():
        try:
            pending = await repo.get_pending(limit=10)
            for task in pending:
                task.provider = task.provider or "opencode"
                queue_key = f"tasks:{task.provider}"

                await repo.update_status(task.id, TaskStatus.SCHEDULED, attempts=1)
                await r.lpush(
                    queue_key,
                    json.dumps(
                        {
                            "id": task.id,
                            "task_type": task.task_type,
                            "payload": task.payload,
                            "provider": task.provider,
                            "max_attempts": task.max_attempts,
                        }
                    ),
                )

                await r.publish(
                    "workflow:events",
                    json.dumps(
                        {
                            "event": "task_scheduled",
                            "task_id": task.id,
                            "provider": task.provider,
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    ),
                )
                log.info(
                    "dispatched task=%s type=%s provider=%s",
                    task.id[:8],
                    task.task_type,
                    task.provider,
                )
            if pending:
                log.info("dispatched %d task(s)", len(pending))
        except Exception as e:
            log.error("poll error: %s", e)
        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=POLL_INTERVAL)
        except TimeoutError:
            continue


async def main() -> None:
    log.info("scheduler starting up")

    pg_pool = await asyncpg.create_pool(PG_DSN, min_size=2, max_size=5)
    log.info("connected to postgres (pool)")
    repo = TaskRepository(pg_pool)

    r = await aioredis.from_url(REDIS_URL, decode_responses=True)
    await r.ping()
    log.info("connected to redis")

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _handle_signal)

    _spawn(health_server())
    _spawn(poll_pg(r, repo))

    tick = 0
    while not _shutdown.is_set():
        tick += 1
        await r.set("scheduler:heartbeat", str(time.time()))
        log.info("heartbeat tick=%d", tick)
        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=HEARTBEAT_INTERVAL)
        except TimeoutError:
            continue

    log.info("shutting down")
    await r.aclose()  # type: ignore[attr-defined]  # present in redis>=5; stubs lag
    await pg_pool.close()
    log.info("scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())
