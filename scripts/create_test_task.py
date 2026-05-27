#!/usr/bin/env python3
"""Create a test task and push it to the queue for processing."""

import asyncio
import json
import os
import sys

import asyncpg
import redis.asyncio as aioredis

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tasks.models import Task
from tasks.repository import TaskRepository

PG_DSN = (
    f"postgresql://{os.getenv('HOOKCLOSE_POSTGRES_USER', 'hookclose')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PASSWORD', 'hookclose')}"
    f"@{os.getenv('HOOKCLOSE_POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PORT', '5432')}"
    f"/{os.getenv('HOOKCLOSE_POSTGRES_DB', 'hookclose')}"
)
REDIS_URL = os.getenv("HOOKCLOSE_REDIS_URL", "redis://localhost:6379/0")


async def main() -> None:
    task_type = sys.argv[1] if len(sys.argv) > 1 else "echo"
    message = sys.argv[2] if len(sys.argv) > 2 else "hello from hookclose"

    task = Task(
        task_type=task_type,
        payload={"message": message, "source": "create_test_task.py"},
        provider="opencode",
        max_attempts=3,
    )

    pool = await asyncpg.create_pool(PG_DSN, min_size=1, max_size=2)
    repo = TaskRepository(pool)

    task = await repo.create(task)
    print(f"task created: id={task.id[:8]} type={task.task_type} status={task.status.value}")

    r = await aioredis.from_url(REDIS_URL, decode_responses=True)
    await r.publish("tasks:pending", json.dumps({"task_id": task.id}))
    print("notification sent to tasks:pending channel")

    await r.aclose()
    await pool.close()
    print(f"task {task.id[:8]} ready for processing")


if __name__ == "__main__":
    asyncio.run(main())
