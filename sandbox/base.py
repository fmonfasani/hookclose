"""Abstract sandbox base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from contracts.sandbox import SandboxPolicy, SandboxResult


class SandboxBase(ABC):
    @abstractmethod
    async def run(
        self,
        image: str,
        command: Sequence[str],
        *,
        policy: SandboxPolicy,
        workdir: str | None = None,
        files: Mapping[str, bytes] | None = None,
    ) -> SandboxResult:
        raise NotImplementedError
