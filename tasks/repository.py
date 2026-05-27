from __future__ import annotations

import json

import asyncpg

from tasks.models import Task, TaskStatus


class TaskRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, task: Task) -> Task:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO tasks
                    (id, workflow_id, status, task_type, payload, provider, max_attempts)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
                RETURNING id, status, created_at, updated_at
                """,
                task.id,
                task.workflow_id,
                task.status.value,
                task.task_type,
                json.dumps(task.payload),
                task.provider,
                task.max_attempts,
            )
            task.status = TaskStatus(row["status"])
            task.created_at = row["created_at"].isoformat()
            task.updated_at = row["updated_at"].isoformat()
        return task

    async def get(self, task_id: str) -> Task | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
            if row is None:
                return None
            return self._row_to_task(row)

    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        *,
        result: dict[str, object] | None = None,
        error: str | None = None,
        attempts: int | None = None,
    ) -> None:
        sets = ["status = $2", "updated_at = now()"]
        params: list[object] = [task_id, status.value]
        idx = 3
        if result is not None:
            sets.append(f"result = ${idx}::jsonb")
            params.append(json.dumps(result))
            idx += 1
        if error is not None:
            sets.append(f"error = ${idx}")
            params.append(error)
            idx += 1
        if attempts is not None:
            sets.append(f"attempts = ${idx}")
            params.append(attempts)
            idx += 1
        async with self._pool.acquire() as conn:
            # `sets` is built only from internal literals above — no user input
            # is interpolated, so this is not an injection vector.
            await conn.execute(
                f"UPDATE tasks SET {', '.join(sets)} WHERE id = $1",  # noqa: S608
                *params,
            )

    async def get_pending(self, limit: int = 10) -> list[Task]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM tasks WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT $1",
                limit,
            )
            return [self._row_to_task(r) for r in rows]

    @staticmethod
    def _row_to_task(row: asyncpg.Record) -> Task:
        return Task(
            id=str(row["id"]),
            workflow_id=str(row["workflow_id"]) if row.get("workflow_id") else None,
            status=TaskStatus(row["status"]),
            task_type=row["task_type"],
            payload=dict(row["payload"]) if row["payload"] else {},
            result=dict(row["result"]) if row.get("result") is not None else None,
            provider=row.get("provider") or "opencode",
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            error=row.get("error"),
            created_at=row["created_at"].isoformat(),
            updated_at=row["updated_at"].isoformat(),
        )
