"""Unit tests for the OpenAIAdapter using a fake async client (no network)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from adapters.llm.openai import OpenAIAdapter
from contracts.llm_provider import LLMMessage, LLMRequest
from providers import Capability, OpenAIProvider, ProviderManager, ProviderRegistry
from providers.errors import (
    ProviderCreditExhausted,
    ProviderError,
    ProviderRateLimited,
    ProviderTimeout,
)

pytestmark = pytest.mark.unit


class _FakeCompletions:
    def __init__(self, *, response: object = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error
        self.last_kwargs: dict[str, object] = {}

    async def create(self, **kwargs: object) -> object:
        self.last_kwargs = kwargs
        if self._error is not None:
            raise self._error
        return self._response


class _FakeClient:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


def _ok_response() -> object:
    return SimpleNamespace(
        model="gpt-4o-mini",
        choices=[
            SimpleNamespace(message=SimpleNamespace(content="hello world"), finish_reason="stop")
        ],
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7, total_tokens=18),
    )


def _request(**kw: object) -> LLMRequest:
    return LLMRequest(model="auto", messages=[LLMMessage(role="user", content="hi")], **kw)


def _err(name: str, *, status: int | None = None, message: str = "boom") -> Exception:
    exc = type(name, (Exception,), {})(message)
    if status is not None:
        exc.status_code = status  # type: ignore[attr-defined]
    return exc


async def test_complete_maps_response_and_usage() -> None:
    completions = _FakeCompletions(response=_ok_response())
    adapter = OpenAIAdapter(_FakeClient(completions), default_model="gpt-4o-mini")

    resp = await adapter.complete(_request())

    assert resp.content == "hello world"
    assert resp.finish_reason == "stop"
    assert resp.usage.total_tokens == 18


async def test_auto_model_falls_back_to_default() -> None:
    completions = _FakeCompletions(response=_ok_response())
    adapter = OpenAIAdapter(_FakeClient(completions), default_model="gpt-4o-mini")
    await adapter.complete(_request())
    assert completions.last_kwargs["model"] == "gpt-4o-mini"


async def test_json_response_format_passed_through() -> None:
    completions = _FakeCompletions(response=_ok_response())
    adapter = OpenAIAdapter(_FakeClient(completions))
    await adapter.complete(_request(response_format="json"))
    assert completions.last_kwargs["response_format"] == {"type": "json_object"}


async def test_rate_limit_maps_to_provider_rate_limited() -> None:
    completions = _FakeCompletions(error=_err("RateLimitError", status=429, message="slow down"))
    adapter = OpenAIAdapter(_FakeClient(completions))
    with pytest.raises(ProviderRateLimited):
        await adapter.complete(_request())


async def test_insufficient_quota_maps_to_credit_exhausted() -> None:
    completions = _FakeCompletions(
        error=_err(
            "RateLimitError",
            status=429,
            message="You exceeded your current quota (insufficient_quota)",
        )
    )
    adapter = OpenAIAdapter(_FakeClient(completions))
    with pytest.raises(ProviderCreditExhausted):
        await adapter.complete(_request())


async def test_timeout_maps_to_provider_timeout() -> None:
    completions = _FakeCompletions(error=_err("APITimeoutError", message="request timed out"))
    adapter = OpenAIAdapter(_FakeClient(completions))
    with pytest.raises(ProviderTimeout):
        await adapter.complete(_request())


async def test_other_errors_map_to_generic_provider_error() -> None:
    completions = _FakeCompletions(error=_err("BadRequestError", status=400, message="nope"))
    adapter = OpenAIAdapter(_FakeClient(completions))
    with pytest.raises(ProviderError):
        await adapter.complete(_request())


async def test_embed_returns_vectors() -> None:
    class _FakeEmbeddings:
        async def create(self, *, model: str, input: list[str]) -> object:
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2]) for _ in input])

    client = SimpleNamespace(embeddings=_FakeEmbeddings())
    adapter = OpenAIAdapter(client)
    vectors = await adapter.embed(["a", "b"], model="text-embedding-3-small")
    assert vectors == [[0.1, 0.2], [0.1, 0.2]]


async def test_openai_provider_uses_adapter_through_manager() -> None:
    # End-to-end: OpenAIProvider wraps the adapter; manager invokes it.
    adapter = OpenAIAdapter(_FakeClient(_FakeCompletions(response=_ok_response())))
    registry = ProviderRegistry()
    registry.register(OpenAIProvider(adapter))
    manager = ProviderManager(registry)

    result = await manager.complete(_request(), capability=Capability.CODE_GENERATION)
    assert result.provider == "openai"
    assert result.content == "hello world"
