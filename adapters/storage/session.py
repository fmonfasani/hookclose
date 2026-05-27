"""AsyncSession factory contract.

Concrete `sqlalchemy.ext.asyncio.async_sessionmaker` binding happens at boot
inside `runtime/bootstrap.py`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Any


class AsyncSessionFactory(ABC):
    @abstractmethod
    def __call__(self) -> AbstractAsyncContextManager[Any]:
        raise NotImplementedError
