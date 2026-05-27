"""Capability vocabulary — the verbs agents can declare they perform."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CapabilityName(StrEnum):
    """Canonical capability names. Add entries; never repurpose."""

    CODE_GENERATE = "code.generate"
    CODE_REVIEW = "code.review"
    CODE_REFACTOR = "code.refactor"
    CODE_REPAIR = "code.repair"
    TEST_AUTHOR = "test.author"
    TEST_RUN = "test.run"
    SPEC_INTERPRET = "spec.interpret"
    DOC_AUTHOR = "doc.author"
    SECURITY_REVIEW = "security.review"
    DEPENDENCY_AUDIT = "dependency.audit"


@dataclass(frozen=True, slots=True)
class CapabilitySpec:
    """Schema-level description of a capability invocation."""

    name: CapabilityName
    input_schema: type  # Pydantic model
    output_schema: type  # Pydantic model
    description: str = ""
    cost_class: str = "standard"  # "cheap" | "standard" | "expensive"


@dataclass(frozen=True, slots=True)
class Capability:
    """A capability *binding* on a concrete agent."""

    spec: CapabilitySpec
    parameters: dict[str, Any] = field(default_factory=dict)
