import asyncio
from datetime import UTC, datetime
import json
import logging
import os
import signal
import time

import asyncpg
import redis.asyncio as aioredis

from tasks.executor import execute_task
from tasks.models import TaskStatus
from tasks.repository import TaskRepository

logging.basicConfig(
    level=os.getenv("HOOKCLOSE_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] opencode-worker: %(message)s",
)
log = logging.getLogger("opencode-worker")

PG_DSN = (
    f"postgresql://{os.getenv('HOOKCLOSE_POSTGRES_USER', 'hookclose')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PASSWORD', 'hookclose')}"
    f"@{os.getenv('HOOKCLOSE_POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PORT', '5432')}"
    f"/{os.getenv('HOOKCLOSE_POSTGRES_DB', 'hookclose')}"
)
REDIS_URL = os.getenv("HOOKCLOSE_REDIS_URL", "redis://redis:6379/0")
TASK_QUEUE = os.getenv("HOOKCLOSE_OPENCODE_TASK_QUEUE", "tasks:opencode")
PORT = int(os.getenv("HOOKCLOSE_OPENCODE_WORKER_PORT", "8102"))

_shutdown = asyncio.Event()


def _handle_signal() -> None:
    log.info("received shutdown signal")
    _shutdown.set()


async def health_server() -> None:
    loop = asyncio.get_event_loop()
    server = await loop.create_server(
        lambda: HealthHandler(), host="0.0.0.0", port=PORT
    )
    log.info("health server listening on 0.0.0.0:%d", PORT)
    async with server:
        await _shutdown.wait()


class HealthHandler(asyncio.Protocol):
    def connection_made(self, transport) -> None:
        body = b'{"status":"ok","service":"opencode-worker"}'
        transport.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            b"Content-Length: %d\r\n\r\n%s" % (len(body), body)
        )
        transport.close()


async def consume(r: aioredis.Redis, repo: TaskRepository) -> None:
    while not _shutdown.is_set():
        try:
            result = await r.blpop(TASK_QUEUE, timeout=2)
            if result is None:
                continue
            _, raw = result
            task_data = json.loads(raw)
            task_id = task_data["id"]
            log.info("consumed task=%s type=%s", task_id[:8], task_data.get("task_type"))

            await repo.update_status(task_id, TaskStatus.RUNNING)
            result_data, error = await execute_task(task_data)

            if error:
                task_db = await repo.get(task_id)
                attempts = (task_db.attempts if task_db else 0) + 1
                if task_db and attempts < task_db.max_attempts:
                    await repo.update_status(
                        task_id, TaskStatus.RETRYING,
                        error=error, attempts=attempts,
                    )
                    await r.lpush(TASK_QUEUE, raw)
                    log.info("re-queued task=%s attempt=%d/%d", task_id[:8], attempts, task_db.max_attempts)
                else:
                    await repo.update_status(
                        task_id, TaskStatus.FAILED,
                        error=error, attempts=attempts,
                    )
                    log.warning("task=%s failed after %d attempts", task_id[:8], attempts)
                    await publish_event(r, "task_failed", task_id, error=error)
                continue

            await repo.update_status(
                task_id, TaskStatus.COMPLETED,
                result=result_data, attempts=0,
            )
            log.info("task=%s completed", task_id[:8])
            await publish_event(r, "task_completed", task_id, result=result_data)

        except Exception as e:
            log.error("consume error: %s", e)
            await asyncio.sleep(1)


async def publish_event(r: aioredis.Redis, event: str, task_id: str, **extra) -> None:
    try:
        await r.publish("workflow:events", json.dumps({
            "event": event,
            "task_id": task_id,
            "timestamp": datetime.now(UTC).isoformat(),
            **extra,
        }))
    except Exception as e:
        log.warning("publish event failed: %s", e)


async def main() -> None:
    log.info("opencode worker starting up")

    pg_pool = await asyncpg.create_pool(PG_DSN, min_size=1, max_size=3)
    repo = TaskRepository(pg_pool)

    r = await aioredis.from_url(REDIS_URL, decode_responses=True)
    await r.ping()
    log.info("connected to redis")

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            pass

    asyncio.create_task(health_server())
    asyncio.create_task(consume(r, repo))

    tick = 0
    while not _shutdown.is_set():
        tick += 1
        await r.set("opencode-worker:heartbeat", str(time.time()))
        log.info("heartbeat tick=%d", tick)
        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=10)
        except TimeoutError:
            continue

    log.info("shutting down")
    await r.aclose()
    await pg_pool.close()
    log.info("opencode worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
