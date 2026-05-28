"""Composition root — assemble the live runtime from configuration.

This is the one place that *wires* the subsystems together: it reads provider
config from the environment, builds the provider registry (OpenRouter / OpenAI if
keys are present, always a deterministic local fallback), and constructs the
ProviderManager, ComplexityRoutingEngine, TaskChainer, and SelfHealingRuntime as
a single :class:`Runtime` bundle.

Everything below the composition root stays dependency-injected and testable; only
this module knows which concrete adapters/keys exist. With no API keys set, the
runtime still works end-to-end on the local fallback provider.
"""

from __future__ import annotations

from dataclasses import dataclass
import os

from adapters.llm.openai import OpenAIAdapter
from contracts.event_bus import EventBusPort
from orchestration.chaining import TaskChainer
from orchestration.self_healing import SelfHealingRuntime
from providers.implementations import LocalProvider, OpenAIProvider
from providers.manager import ProviderManager
from providers.persistence import ProviderStateStore
from providers.registry import ProviderRegistry
from providers.routing import ComplexityRoutingEngine
from providers.state import Capability, Clock, ProviderProfile, utc_now

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# A capable, cheap coding model on OpenRouter. Override via OPENROUTER_MODEL.
_DEFAULT_OPENROUTER_MODEL = "qwen/qwen-2.5-coder-32b-instruct"
_GENERAL_CAPS = frozenset(
    {
        Capability.CODE_GENERATION,
        Capability.REVIEW,
        Capability.ANALYSIS,
        Capability.EXTRACTION,
    }
)


@dataclass(frozen=True, slots=True)
class ProvidersConfig:
    """Which providers to wire. All keys optional; local fallback is always on."""

    openrouter_api_key: str | None = None
    openrouter_base_url: str = _OPENROUTER_BASE_URL
    openrouter_model: str = _DEFAULT_OPENROUTER_MODEL
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    enable_local_fallback: bool = True
    referer: str = "https://github.com/fmonfasani/hookclose"

    @classmethod
    def from_env(cls) -> ProvidersConfig:
        return cls(
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY") or None,
            openrouter_base_url=os.environ.get("OPENROUTER_BASE_URL", _OPENROUTER_BASE_URL),
            openrouter_model=os.environ.get("OPENROUTER_MODEL", _DEFAULT_OPENROUTER_MODEL),
            openai_api_key=os.environ.get("OPENAI_API_KEY") or None,
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        )


@dataclass(frozen=True, slots=True)
class Runtime:
    """The assembled, wired runtime. Hold one of these per process."""

    registry: ProviderRegistry
    providers: ProviderManager
    routing: ComplexityRoutingEngine
    chainer: TaskChainer
    healing: SelfHealingRuntime
    provider_names: tuple[str, ...]


def build_provider_registry(config: ProvidersConfig, *, clock: Clock = utc_now) -> ProviderRegistry:
    """Register the configured providers; always include a fallback to serve."""
    registry = ProviderRegistry()

    if config.openrouter_api_key:
        adapter = OpenAIAdapter.from_api_key(
            config.openrouter_api_key,
            base_url=config.openrouter_base_url,
            default_model=config.openrouter_model,
            default_headers={"HTTP-Referer": config.referer, "X-Title": "HookClose"},
        )
        registry.register(
            OpenAIProvider(
                adapter,
                profile=ProviderProfile(
                    name="openrouter",
                    capabilities=_GENERAL_CAPS,
                    cost_per_1k_tokens=0.3,  # cheap → preferred for low-complexity work
                    context_window=128_000,
                ),
                clock=clock,
            )
        )

    if config.openai_api_key:
        registry.register(
            OpenAIProvider(
                OpenAIAdapter.from_api_key(
                    config.openai_api_key, default_model=config.openai_model
                ),
                clock=clock,
            )
        )

    if config.enable_local_fallback or not registry.names():
        registry.register(LocalProvider(clock=clock))

    return registry


def build_runtime(
    config: ProvidersConfig | None = None,
    *,
    event_bus: EventBusPort | None = None,
    state_store: ProviderStateStore | None = None,
    clock: Clock = utc_now,
) -> Runtime:
    """Assemble the full runtime. With no keys, runs on the local fallback."""
    config = config or ProvidersConfig.from_env()
    registry = build_provider_registry(config, clock=clock)
    manager = ProviderManager(registry, event_bus=event_bus, state_store=state_store)
    return Runtime(
        registry=registry,
        providers=manager,
        routing=ComplexityRoutingEngine(registry, event_bus=event_bus),
        chainer=TaskChainer(event_bus=event_bus),
        healing=SelfHealingRuntime(event_bus=event_bus),
        provider_names=registry.names(),
    )
