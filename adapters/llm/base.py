"""Abstract LLM adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence

from contracts.llm_provider import LLMRequest, LLMResponse


class LLMAdapterBase(ABC):
    """Concrete LLM adapters subclass this.

    Implementations MUST:
      - normalize streaming chunks to plain `str` deltas
      - convert vendor errors into `runtime.errors.InfrastructureError`
      - never leak vendor exceptions across the contract boundary
      - implement bounded retries internally (using tenacity)
    """

    provider: str

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    async def embed(
        self,
        texts: Sequence[str],
        *,
        model: str,
    ) -> Sequence[Sequence[float]]:
        raise NotImplementedError
