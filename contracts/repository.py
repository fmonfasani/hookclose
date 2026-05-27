"""Repository pattern port — generic persistence boundary."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar, runtime_checkable

EntityT = TypeVar("EntityT")
# KeyT_contra only ever appears in input position (get/delete), so it is contravariant.
KeyT_contra = TypeVar("KeyT_contra", contravariant=True)


@runtime_checkable
class RepositoryPort(Protocol[EntityT, KeyT_contra]):
    """A repository is a typed, async-friendly persistence boundary.

    Concrete adapters live in `adapters/storage/` and translate to SQLAlchemy
    sessions, Redis, or any other backing store. The repository never leaks
    ORM types to the caller.
    """

    async def get(self, key: KeyT_contra) -> EntityT | None: ...

    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[EntityT]: ...

    async def add(self, entity: EntityT) -> EntityT: ...

    async def update(self, entity: EntityT) -> EntityT: ...

    async def delete(self, key: KeyT_contra) -> bool: ...
