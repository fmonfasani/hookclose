"""Unit of Work port — transactional consistency boundary."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol, runtime_checkable


@runtime_checkable
class UnitOfWorkPort(Protocol):
    """Demarcates a transactional unit. The concrete implementation wraps a
    SQLAlchemy `AsyncSession` and exposes typed repositories as attributes."""

    def __call__(self) -> AbstractAsyncContextManager[UnitOfWorkPort]: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
