"""Abstract vector store adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from contracts.memory import SemanticHit, SemanticRecord


class VectorStoreAdapterBase(ABC):
    @abstractmethod
    async def upsert(self, records: Sequence[SemanticRecord]) -> None: ...

    @abstractmethod
    async def search(
        self,
        namespace: str,
        embedding: Sequence[float],
        *,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> Sequence[SemanticHit]: ...

    @abstractmethod
    async def delete(self, namespace: str, record_ids: Sequence[str]) -> None: ...
