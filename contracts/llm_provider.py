"""LLM provider port — vendor-agnostic model invocation."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: Role
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMRequest:
    model: str
    messages: Sequence[LLMMessage]
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stop: Sequence[str] | None = None
    response_format: str | None = None  # "text" | "json"
    tools: Sequence[Mapping[str, Any]] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True, slots=True)
class LLMResponse:
    model: str
    content: str
    finish_reason: str
    usage: LLMUsage
    tool_calls: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMProviderPort(Protocol):
    """Abstract LLM endpoint. Each provider (OpenAI, Anthropic, vLLM, …)
    is implemented as a separate adapter."""

    provider: str

    async def complete(self, request: LLMRequest) -> LLMResponse: ...

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]: ...

    async def embed(
        self,
        texts: Sequence[str],
        *,
        model: str,
    ) -> Sequence[Sequence[float]]: ...
