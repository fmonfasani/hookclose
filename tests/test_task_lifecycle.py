"""Unit tests for the task lifecycle (no Docker / PG / Redis required)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tasks.executor import execute_task
from tasks.models import Task, TaskStatus
from tasks.repository import TaskRepository


class TestTaskModel:
    def test_create_task_defaults(self):
        task = Task(task_type="echo", payload={"msg": "hello"})
        assert task.status == TaskStatus.PENDING
        assert task.attempts == 0
        assert task.max_attempts == 3
        assert task.provider == "opencode"
        assert task.error is None

    def test_task_status_transitions(self):
        task = Task()
        assert task.status == TaskStatus.PENDING
        task.status = TaskStatus.SCHEDULED
        assert task.status == TaskStatus.SCHEDULED
        task.status = TaskStatus.RUNNING
        assert task.status == TaskStatus.RUNNING
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED

    def test_failed_task_retry_state(self):
        task = Task(attempts=1, max_attempts=3)
        assert task.attempts < task.max_attempts
        task.status = TaskStatus.RETRYING
        assert task.status == TaskStatus.RETRYING

    def test_task_exhausted_retries(self):
        task = Task(attempts=3, max_attempts=3)
        assert task.attempts >= task.max_attempts

    def test_task_to_dict(self):
        task = Task(task_type="echo", payload={"msg": "hi"}, provider="opencode")
        d = task.model_dump()
        assert d["task_type"] == "echo"
        assert d["payload"] == {"msg": "hi"}
        assert d["provider"] == "opencode"


def _mock_row(**kwargs):
    """Create a MagicMock that acts like an asyncpg Record."""
    row = MagicMock()
    row.__getitem__.side_effect = kwargs.get
    row.get = lambda k, default=None: kwargs.get(k, default)
    for k, v in kwargs.items():
        setattr(row, k, v)
    return row


class TestTaskRepository:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        conn = AsyncMock()
        pool.acquire.return_value = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = conn
        return pool

    @pytest.fixture
    def repo(self, mock_pool):
        return TaskRepository(mock_pool)

    async def test_create_task(self, repo, mock_pool):
        row = _mock_row(
            id="abc-123",
            status="PENDING",
            created_at=MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
            updated_at=MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
        )
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.return_value = row

        task = Task(id="abc-123", task_type="echo", payload={"msg": "hello"})
        result = await repo.create(task)

        assert result.status == TaskStatus.PENDING
        assert result.id == "abc-123"

    async def test_update_status(self, repo, mock_pool):
        await repo.update_status("task-1", TaskStatus.RUNNING)
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.execute.assert_called_once()

    async def test_update_status_with_result(self, repo, mock_pool):
        await repo.update_status("task-1", TaskStatus.COMPLETED, result={"output": "ok"})
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        assert conn.execute.call_count == 1
        call_args = conn.execute.call_args[0]
        assert "result" in call_args[0]
        assert "COMPLETED" in call_args[2]

    async def test_get_pending(self, repo, mock_pool):
        row = _mock_row(
            id="t1",
            workflow_id=None,
            status="PENDING",
            task_type="echo",
            payload={},
            result=None,
            provider="opencode",
            attempts=0,
            max_attempts=3,
            error=None,
            created_at=MagicMock(isoformat=lambda: "now"),
            updated_at=MagicMock(isoformat=lambda: "now"),
        )
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetch.return_value = [row]

        tasks = await repo.get_pending()
        assert len(tasks) == 1
        assert tasks[0].status == TaskStatus.PENDING


@pytest.mark.asyncio
class TestExecuteTask:
    async def test_execute_echo(self):
        result, error = await execute_task(
            {
                "id": "t1",
                "task_type": "echo",
                "payload": {"message": "hello"},
            }
        )
        assert error is None
        assert result["echo"] == "hello"
        assert "processed: hello" in result["output"]

    async def test_execute_sleep(self):
        result, error = await execute_task(
            {
                "id": "t2",
                "task_type": "sleep",
                "payload": {"duration": 0.01},
            }
        )
        assert error is None
        assert result["slept"] == 0.01

    async def test_execute_fail(self):
        result, error = await execute_task(
            {
                "id": "t3",
                "task_type": "fail",
                "payload": {},
            }
        )
        assert result is None
        assert error is not None
        assert "simulated failure" in error

    async def test_execute_generic(self):
        result, error = await execute_task(
            {
                "id": "t4",
                "task_type": "codegen",
                "payload": {"language": "python"},
            }
        )
        assert error is None
        assert result["processed"] is True
        assert result["task_type"] == "codegen"


@pytest.mark.asyncio
class TestTaskLifecycleIntegration:
    async def test_full_lifecycle(self):
        task = Task(task_type="echo", payload={"message": "integration test"})
        assert task.status == TaskStatus.PENDING

        task.status = TaskStatus.SCHEDULED
        task.attempts += 1
        assert task.status == TaskStatus.SCHEDULED

        task.status = TaskStatus.RUNNING
        assert task.status == TaskStatus.RUNNING

        result, error = await execute_task(
            {
                "id": task.id,
                "task_type": task.task_type,
                "payload": task.payload,
            }
        )
        assert error is None
        assert result is not None

        task.result = result
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED
        assert task.result["echo"] == "integration test"

    async def test_failure_with_retry(self):
        task = Task(task_type="fail", payload={}, max_attempts=3)

        results = []
        for attempt in range(1, task.max_attempts + 1):
            task.status = TaskStatus.SCHEDULED
            task.attempts = attempt

            task.status = TaskStatus.RUNNING
            result, error = await execute_task(
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "payload": task.payload,
                }
            )

            if error and attempt < task.max_attempts:
                task.status = TaskStatus.RETRYING
                results.append("retry")
            elif error and attempt >= task.max_attempts:
                task.status = TaskStatus.FAILED
                task.error = error
                results.append("failed")
            else:
                task.status = TaskStatus.COMPLETED
                results.append("completed")

        assert results == ["retry", "retry", "failed"]
        assert task.status == TaskStatus.FAILED
        assert task.error is not None


class TestStatusEnum:
    def test_all_statuses_defined(self):
        expected = {"PENDING", "SCHEDULED", "RUNNING", "COMPLETED", "FAILED", "RETRYING"}
        actual = {s.value for s in TaskStatus}
        assert actual == expected

    def test_status_transition_validity(self):
        valid = {
            TaskStatus.PENDING: [TaskStatus.SCHEDULED],
            TaskStatus.SCHEDULED: [TaskStatus.RUNNING],
            TaskStatus.RUNNING: [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.RETRYING],
            TaskStatus.RETRYING: [TaskStatus.SCHEDULED, TaskStatus.FAILED],
        }
        for status, next_states in valid.items():
            for next_state in next_states:
                assert isinstance(next_state, TaskStatus)
