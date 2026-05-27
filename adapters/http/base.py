"""Abstract outbound HTTP client."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class HTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes
    duration_ms: int


class HTTPClientBase(ABC):
    @abstractmethod
    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json: Any | None = None,
        params: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> HTTPResponse:
        raise NotImplementedError
