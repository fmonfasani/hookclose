"""Operational memory base class — short-lived working memory."""

from __future__ import annotations

from abc import ABC, abstractmethod


class OperationalMemoryBase(ABC):
    @abstractmethod
    async def get(self, namespace: str, key: str) -> bytes | None:
        raise NotImplementedError

    @abstractmethod
    async def set(
        self,
        namespace: str,
        key: str,
        value: bytes,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, namespace: str, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def acquire_lock(
        self,
        namespace: str,
        key: str,
        *,
        ttl_seconds: int,
    ) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def release_lock(self, namespace: str, key: str, token: str) -> bool:
        raise NotImplementedError
