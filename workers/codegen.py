"""Code generation — turn a task goal into real file patches via a provider.

This is what makes the worker *build* something instead of only running pre-supplied
steps: it asks the routed provider (OpenRouter/OpenAI/local) for the files that
satisfy a goal, parses the JSON envelope into :class:`FilePatch` objects, and hands
them back to the worker to materialize + test.

Output is constrained to a strict JSON schema so it is deterministic and parseable;
malformed output degrades safely (no files) rather than corrupting the workspace.
"""

from __future__ import annotations

from dataclasses import dataclass
import json

from contracts.llm_provider import LLMMessage, LLMRequest
from providers.manager import ProviderManager
from providers.state import Capability
from workers.contracts import FilePatch

_SYSTEM = (
    "You are an expert software engineer working inside an automated build runtime. "
    "Generate the COMPLETE files needed to accomplish the goal. "
    "Respond with ONLY a JSON object, no prose, matching this schema: "
    '{"files": [{"path": "<relative/path>", "content": "<full file contents>"}], '
    '"notes": "<short summary>"}. '
    "Paths are relative to the project root and must not start with '/' or contain '..'. "
    "Return complete, runnable files — never elide with '...'."
)


@dataclass(frozen=True, slots=True)
class GenerationResult:
    provider: str
    patches: tuple[FilePatch, ...]
    notes: str
    total_tokens: int
    degraded: bool = False


class CodeGenerator:
    """Generates file patches for a goal using the ProviderManager."""

    def __init__(
        self,
        manager: ProviderManager,
        *,
        capability: Capability = Capability.CODE_GENERATION,
        max_tokens: int = 4096,
    ) -> None:
        self._manager = manager
        self._capability = capability
        self._max_tokens = max_tokens

    def build_request(self, goal: str, *, context: str = "") -> LLMRequest:
        user = f"Goal:\n{goal}\n"
        if context:
            user += f"\nContext / constraints:\n{context}\n"
        user += "\nReturn the JSON object now."
        return LLMRequest(
            model="auto",
            messages=[
                LLMMessage(role="system", content=_SYSTEM),
                LLMMessage(role="user", content=user),
            ],
            temperature=0.0,
            max_tokens=self._max_tokens,
            response_format="json",
        )

    async def generate(self, goal: str, *, context: str = "") -> GenerationResult:
        """Invoke the provider and parse the result. Raises NoProviderAvailable
        only if no provider can serve (the worker treats that as a failed step)."""
        invocation = await self._manager.complete(
            self.build_request(goal, context=context), capability=self._capability
        )
        patches, notes, degraded = _parse(invocation.content)
        return GenerationResult(
            provider=invocation.provider,
            patches=patches,
            notes=notes,
            total_tokens=invocation.total_tokens,
            degraded=degraded,
        )


def _parse(content: str) -> tuple[tuple[FilePatch, ...], str, bool]:
    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except (json.JSONDecodeError, ValueError):
        return (), content[:200], True

    raw_files = data.get("files", [])
    if not isinstance(raw_files, list):
        return (), str(data.get("notes", "")), True

    patches: list[FilePatch] = []
    for entry in raw_files:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        body = entry.get("content")
        if isinstance(path, str) and isinstance(body, str) and path:
            patches.append(FilePatch(path=path, content=body))

    return tuple(patches), str(data.get("notes", "")), len(patches) == 0
