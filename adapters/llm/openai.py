"""OpenAI LLM adapter — real chat-completions / embeddings behind ``LLMProviderPort``.

Translates the vendor SDK into the project's contract types and, crucially, maps
OpenAI errors into the provider error taxonomy so the ProviderManager can react
deterministically (cooldown on rate limit, fail over on credit exhaustion, …).

The ``openai`` SDK is imported lazily (only when building a real client), so this
module imports without the package installed and tests inject a fake client.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
import os
from typing import Any

from contracts.llm_provider import LLMRequest, LLMResponse, LLMUsage
from providers.errors import (
    ProviderCreditExhausted,
    ProviderError,
    ProviderRateLimited,
    ProviderTimeout,
)
from runtime.errors import ConfigurationError

_RATE_LIMIT_STATUS = 429
_TIMEOUT_STATUS = 408
_AUTH_STATUS = frozenset({401, 403})


class OpenAIAdapter:
    """Implements the LLM port using OpenAI's async client.

    ``client`` is an ``openai.AsyncOpenAI``-compatible object (duck-typed so tests
    can pass a fake). Build a real one with :meth:`from_api_key` / :meth:`from_env`.
    """

    provider = "openai"

    def __init__(
        self, client: Any, *, default_model: str = "gpt-4o-mini", timeout: float = 60.0
    ) -> None:
        self._client = client
        self._default_model = default_model
        self._timeout = timeout

    @classmethod
    def from_api_key(
        cls,
        api_key: str,
        *,
        default_model: str = "gpt-4o-mini",
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> OpenAIAdapter:
        import openai  # lazy: only needed for a real client  # noqa: PLC0415

        client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        return cls(client, default_model=default_model, timeout=timeout)

    @classmethod
    def from_env(cls, **kwargs: Any) -> OpenAIAdapter:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ConfigurationError("OPENAI_API_KEY is not set")
        return cls.from_api_key(key, **kwargs)

    def _model(self, request: LLMRequest) -> str:
        return request.model if request.model and request.model != "auto" else self._default_model

    def _build_kwargs(self, request: LLMRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._model(request),
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.stop is not None:
            kwargs["stop"] = list(request.stop)
        if request.response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    async def complete(self, request: LLMRequest) -> LLMResponse:
        try:
            response = await self._client.chat.completions.create(**self._build_kwargs(request))
        except Exception as exc:
            raise _map_error(exc) from exc

        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        return LLMResponse(
            model=getattr(response, "model", self._default_model),
            content=choice.message.content or "",
            finish_reason=choice.finish_reason or "stop",
            usage=LLMUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
                total_tokens=getattr(usage, "total_tokens", 0) if usage else 0,
            ),
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        kwargs = self._build_kwargs(request)
        kwargs["stream"] = True
        try:
            stream = await self._client.chat.completions.create(**kwargs)
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            raise _map_error(exc) from exc

    async def embed(self, texts: Sequence[str], *, model: str) -> Sequence[Sequence[float]]:
        try:
            response = await self._client.embeddings.create(model=model, input=list(texts))
        except Exception as exc:
            raise _map_error(exc) from exc
        return [item.embedding for item in response.data]


def _map_error(exc: Exception) -> ProviderError:
    """Map an OpenAI SDK exception to the provider error taxonomy.

    Uses ``status_code`` + class name so it works without importing openai types
    (and so fakes in tests can mimic the behavior).
    """
    status = getattr(exc, "status_code", None)
    name = type(exc).__name__
    msg = str(exc)
    lowered = msg.lower()

    if status == _RATE_LIMIT_STATUS or name == "RateLimitError":
        if "insufficient_quota" in lowered or "exceeded your current quota" in lowered:
            return ProviderCreditExhausted(msg)
        return ProviderRateLimited(msg)
    if (
        name in ("APITimeoutError", "TimeoutError")
        or status == _TIMEOUT_STATUS
        or "timed out" in lowered
    ):
        return ProviderTimeout(msg)
    if status in _AUTH_STATUS:
        return ProviderError(f"openai auth/permission error: {msg}")
    return ProviderError(f"openai error: {msg}")
