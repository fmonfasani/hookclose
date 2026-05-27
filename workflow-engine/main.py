import asyncio
import json
import logging
import os
import signal
import time

import asyncpg
import redis.asyncio as aioredis

logging.basicConfig(
    level=os.getenv("HOOKCLOSE_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] workflow-engine: %(message)s",
)
log = logging.getLogger("workflow-engine")

PG_DSN = (
    f"postgresql://{os.getenv('HOOKCLOSE_POSTGRES_USER', 'hookclose')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PASSWORD', 'hookclose')}"
    f"@{os.getenv('HOOKCLOSE_POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PORT', '5432')}"
    f"/{os.getenv('HOOKCLOSE_POSTGRES_DB', 'hookclose')}"
)
REDIS_URL = os.getenv("HOOKCLOSE_REDIS_URL", "redis://redis:6379/0")
PORT = int(os.getenv("HOOKCLOSE_WORKFLOW_ENGINE_PORT", "8101"))

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
        body = b'{"status":"ok","service":"workflow-engine"}'
        transport.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            b"Content-Length: %d\r\n\r\n%s" % (len(body), body)
        )
        transport.close()


def format_msg(data: bytes | str | None) -> dict | None:
    if data is None:
        return None
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {"raw": data}


async def listen_events(r: aioredis.Redis, pg: asyncpg.Connection) -> None:
    pubsub = r.pubsub()
    await pubsub.subscribe("workflow:events")
    log.info("subscribed to workflow:events")

    while not _shutdown.is_set():
        try:
            msg = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if msg is not None:
                data = format_msg(msg.get("data"))
                if data:
                    event = data.get("event", "unknown")
                    task_id = data.get("task_id", "?")
                    log.info(
                        "event=%s task=%s type=%s",
                        event, task_id[:8] if len(task_id) > 8 else task_id,
                        data.get("task_type", "?"),
                    )
                    await pg.execute(
                        "INSERT INTO events (workflow_id, event_type, payload) VALUES ($1, $2, $3::jsonb)",
                        data.get("workflow_id") or task_id,
                        event,
                        json.dumps(data),
                    )
        except Exception as e:
            log.error("event listener error: %s", e)
        await asyncio.sleep(0.1)

    await pubsub.unsubscribe("workflow:events")
    log.info("unsubscribed from workflow:events")


async def main() -> None:
    log.info("workflow engine starting up")

    pg = await asyncpg.connect(PG_DSN)
    log.info("connected to postgres")

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
    asyncio.create_task(listen_events(r, pg))

    tick = 0
    while not _shutdown.is_set():
        tick += 1
        await r.set("workflow-engine:heartbeat", str(time.time()))
        log.info("heartbeat tick=%d", tick)
        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=10)
        except TimeoutError:
            continue

    log.info("shutting down")
    await r.aclose()
    await pg.close()
    log.info("workflow engine stopped")


if __name__ == "__main__":
    asyncio.run(main())
