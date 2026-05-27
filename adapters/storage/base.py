"""Abstract repository base bound to a SQLAlchemy session."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

EntityT = TypeVar("EntityT")
KeyT = TypeVar("KeyT")


class RepositoryBase(ABC, Generic[EntityT, KeyT]):
    @abstractmethod
    async def get(self, key: KeyT) -> EntityT | None: ...

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[EntityT]: ...

    @abstractmethod
    async def add(self, entity: EntityT) -> EntityT: ...

    @abstractmethod
    async def update(self, entity: EntityT) -> EntityT: ...

    @abstractmethod
    async def delete(self, key: KeyT) -> bool: ...
