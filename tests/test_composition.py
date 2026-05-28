"""Unit tests for the composition root (runtime assembly)."""

from __future__ import annotations

import pytest

from contracts.llm_provider import LLMMessage, LLMRequest
from providers.state import Capability
from runtime.composition import ProvidersConfig, build_provider_registry, build_runtime

pytestmark = pytest.mark.unit


def test_no_keys_yields_local_only() -> None:
    registry = build_provider_registry(ProvidersConfig())
    assert registry.names() == ("local",)


def test_openrouter_key_registers_openrouter_plus_local() -> None:
    registry = build_provider_registry(ProvidersConfig(openrouter_api_key="sk-test"))
    assert set(registry.names()) == {"openrouter", "local"}
    # openrouter is cheaper → sorts before local in failover order for codegen
    order = [p.name for p in registry.for_capability(Capability.CODE_GENERATION)]
    assert order == ["openrouter", "local"]


def test_openai_and_openrouter_both_register() -> None:
    registry = build_provider_registry(
        ProvidersConfig(openrouter_api_key="sk-or", openai_api_key="sk-oai")
    )
    assert set(registry.names()) == {"openrouter", "openai", "local"}


def test_local_fallback_can_be_disabled_but_forced_if_empty() -> None:
    # disabled + no real providers => still gets local (can't have an empty registry)
    registry = build_provider_registry(ProvidersConfig(enable_local_fallback=False))
    assert registry.names() == ("local",)


def test_build_runtime_wires_all_components() -> None:
    rt = build_runtime(ProvidersConfig())
    assert rt.providers is not None
    assert rt.routing is not None
    assert rt.chainer is not None
    assert rt.healing is not None
    assert rt.provider_names == ("local",)


async def test_runtime_completes_on_local_fallback_without_keys() -> None:
    rt = build_runtime(ProvidersConfig())
    request = LLMRequest(model="auto", messages=[LLMMessage(role="user", content="hola")])
    result = await rt.providers.complete(request, capability=Capability.CODE_GENERATION)
    assert result.provider == "local"
    assert "hola" in result.content


def test_from_env_reads_openrouter_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-env")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = ProvidersConfig.from_env()
    assert config.openrouter_api_key == "sk-env"
    assert config.openrouter_model == "some/model"
    assert config.openai_api_key is None
