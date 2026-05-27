"""Concrete providers: Claude, OpenCode, Gemini, Local.

Each provider carries a default :class:`ProviderProfile` (capabilities, relative
cost, context window) and delegates the actual call to an injected LLM adapter
(``LLMProviderPort``), translating any stray exception into a ``ProviderError``.

``LocalProvider`` is the last-resort fallback: if no adapter is supplied it returns
a deterministic stub response so the runtime always has *some* provider to fall back
to. Real network adapters live in ``adapters/llm/`` and are wired at bootstrap.
"""

from __future__ import annotations

from contracts.llm_provider import LLMProviderPort, LLMRequest, LLMResponse, LLMUsage
from providers.base import BaseProvider
from providers.errors import ProviderError
from providers.state import Capability, Clock, ProviderProfile, utc_now


class _AdapterProvider(BaseProvider):
    """Shared base for providers that delegate to an ``LLMProviderPort``."""

    def __init__(
        self, adapter: LLMProviderPort, profile: ProviderProfile, *, clock: Clock = utc_now
    ) -> None:
        super().__init__(profile, clock=clock)
        self._adapter = adapter

    async def _invoke(self, request: LLMRequest) -> LLMResponse:
        try:
            return await self._adapter.complete(request)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"{self.name} invocation failed: {exc}") from exc


class ClaudeProvider(_AdapterProvider):
    """Expensive, high-capability cognition (architecture, review, codegen)."""

    @staticmethod
    def default_profile() -> ProviderProfile:
        return ProviderProfile(
            name="claude",
            capabilities=frozenset(
                {
                    Capability.ARCHITECTURE,
                    Capability.REVIEW,
                    Capability.ANALYSIS,
                    Capability.CODE_GENERATION,
                }
            ),
            cost_per_1k_tokens=15.0,
            context_window=200_000,
            weight=1.0,
        )

    def __init__(
        self,
        adapter: LLMProviderPort,
        *,
        profile: ProviderProfile | None = None,
        clock: Clock = utc_now,
    ) -> None:
        super().__init__(adapter, profile or self.default_profile(), clock=clock)


class OpenCodeProvider(_AdapterProvider):
    """Cheap, fast implementation worker (codegen, review)."""

    @staticmethod
    def default_profile() -> ProviderProfile:
        return ProviderProfile(
            name="opencode",
            capabilities=frozenset({Capability.CODE_GENERATION, Capability.REVIEW}),
            cost_per_1k_tokens=2.0,
            context_window=128_000,
            weight=1.0,
        )

    def __init__(
        self,
        adapter: LLMProviderPort,
        *,
        profile: ProviderProfile | None = None,
        clock: Clock = utc_now,
    ) -> None:
        super().__init__(adapter, profile or self.default_profile(), clock=clock)


class GeminiProvider(_AdapterProvider):
    """Very cheap extraction / large-context analysis / embeddings."""

    @staticmethod
    def default_profile() -> ProviderProfile:
        return ProviderProfile(
            name="gemini",
            capabilities=frozenset(
                {
                    Capability.EXTRACTION,
                    Capability.CODE_GENERATION,
                    Capability.ANALYSIS,
                    Capability.EMBEDDING,
                }
            ),
            cost_per_1k_tokens=0.5,
            context_window=1_000_000,
            weight=1.0,
        )

    def __init__(
        self,
        adapter: LLMProviderPort,
        *,
        profile: ProviderProfile | None = None,
        clock: Clock = utc_now,
    ) -> None:
        super().__init__(adapter, profile or self.default_profile(), clock=clock)


class LocalProvider(BaseProvider):
    """Last-resort local model. Lowest ``weight`` so it sorts after real vendors.

    With no adapter it produces a deterministic stub so the runtime can always
    degrade gracefully instead of raising :class:`NoProviderAvailable`.
    """

    @staticmethod
    def default_profile() -> ProviderProfile:
        return ProviderProfile(
            name="local",
            capabilities=frozenset({Capability.EXTRACTION, Capability.CODE_GENERATION}),
            cost_per_1k_tokens=0.0,
            context_window=32_000,
            weight=0.1,
            daily_token_budget=None,
        )

    def __init__(
        self,
        adapter: LLMProviderPort | None = None,
        *,
        profile: ProviderProfile | None = None,
        clock: Clock = utc_now,
    ) -> None:
        super().__init__(profile or self.default_profile(), clock=clock)
        self._adapter = adapter

    async def _invoke(self, request: LLMRequest) -> LLMResponse:
        if self._adapter is not None:
            try:
                return await self._adapter.complete(request)
            except ProviderError:
                raise
            except Exception as exc:
                raise ProviderError(f"local invocation failed: {exc}") from exc
        # Deterministic degraded fallback.
        last_user = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        content = f"[local-fallback] {last_user}".strip()
        approx = max(1, len(content) // 4)
        return LLMResponse(
            model="local-fallback",
            content=content,
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=approx, completion_tokens=approx, total_tokens=2 * approx),
            metadata={"degraded": True},
        )
