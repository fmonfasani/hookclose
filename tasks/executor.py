"""Task execution logic — shared between worker and tests."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

log = logging.getLogger("tasks.executor")


async def execute_task(task_data: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    task_type = task_data.get("task_type", "generic")
    payload = task_data.get("payload", {})

    log.info("executing task type=%s payload=%s", task_type, payload)

    if task_type == "echo":
        message = payload.get("message", "")
        return {"echo": message, "output": f"processed: {message}"}, None

    if task_type == "sleep":
        duration = payload.get("duration", 1)
        await asyncio.sleep(duration)
        return {"slept": duration}, None

    if task_type == "fail":
        return None, "simulated failure for task type 'fail'"

    return {"processed": True, "task_type": task_type, "input": payload}, None
