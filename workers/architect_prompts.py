"""Structured, deterministic prompt builders for the ClaudeArchitectWorker.

Every prompt asks for a strict JSON envelope so outputs are machine-parseable and
deterministic (temperature 0). Building prompts is pure and side-effect free.
"""

from __future__ import annotations

from enum import StrEnum

from contracts.llm_provider import LLMMessage, LLMRequest
from providers.state import Capability


class ReviewKind(StrEnum):
    ARCHITECTURE_REVIEW = "architecture_review"
    RUNTIME_ANALYSIS = "runtime_analysis"
    SPEC_GENERATION = "spec_generation"
    REFACTOR_REVIEW = "refactor_review"

    @property
    def capability(self) -> Capability:
        return _KIND_CAPABILITY[self]

    @property
    def task_type(self) -> str:
        return _KIND_TASK_TYPE[self]


_KIND_CAPABILITY: dict[ReviewKind, Capability] = {
    ReviewKind.ARCHITECTURE_REVIEW: Capability.ARCHITECTURE,
    ReviewKind.RUNTIME_ANALYSIS: Capability.ANALYSIS,
    ReviewKind.SPEC_GENERATION: Capability.ARCHITECTURE,
    ReviewKind.REFACTOR_REVIEW: Capability.REVIEW,
}

_KIND_TASK_TYPE: dict[ReviewKind, str] = {
    ReviewKind.ARCHITECTURE_REVIEW: "architecture.review",
    ReviewKind.RUNTIME_ANALYSIS: "analysis.runtime",
    ReviewKind.SPEC_GENERATION: "architecture.spec",
    ReviewKind.REFACTOR_REVIEW: "review.refactor",
}

_SYSTEM = (
    "You are a Principal Software Architect performing a {role}. "
    "Be precise, deterministic, and conservative. "
    "Respond with ONLY a JSON object and no prose. Schema: "
    '{{"score": <int 0-100>, "summary": <string>, '
    '"findings": [<string>, ...], "sections": [<string>, ...]}}. '
    "score is overall architectural health (100 = excellent). "
    "findings are concrete issues or risks. sections is the document outline "
    "(used for spec generation; otherwise []).".strip()
)

_ROLE = {
    ReviewKind.ARCHITECTURE_REVIEW: "design review",
    ReviewKind.RUNTIME_ANALYSIS: "runtime/orchestration analysis",
    ReviewKind.SPEC_GENERATION: "specification generation",
    ReviewKind.REFACTOR_REVIEW: "refactor review",
}


def build_request(
    kind: ReviewKind, *, target: str, content: str, model: str = "auto"
) -> LLMRequest:
    """Build a deterministic, JSON-constrained request for a review ``kind``."""
    system = _SYSTEM.format(role=_ROLE[kind])
    user = (
        f"Target: {target}\n"
        f"Review kind: {kind.value}\n"
        f"--- material ---\n{content}\n--- end ---\n"
        "Return the JSON object now."
    )
    return LLMRequest(
        model=model,
        messages=[
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content=user),
        ],
        temperature=0.0,
        response_format="json",
    )
