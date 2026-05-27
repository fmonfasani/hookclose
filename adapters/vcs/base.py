"""Abstract VCS adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from contracts.vcs import FileDiff, PullRequestRef, RepoRef


class VCSAdapterBase(ABC):
    @abstractmethod
    async def clone(self, repo: RepoRef, *, ref: str, dest: str) -> None: ...

    @abstractmethod
    async def create_branch(self, repo: RepoRef, name: str, from_ref: str) -> None: ...

    @abstractmethod
    async def commit(
        self,
        repo: RepoRef,
        branch: str,
        message: str,
        files: dict[str, bytes],
        *,
        author: str,
    ) -> str: ...

    @abstractmethod
    async def open_pull_request(
        self,
        repo: RepoRef,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> PullRequestRef: ...

    @abstractmethod
    async def review_pull_request(
        self,
        pr: PullRequestRef,
        body: str,
        decision: str,
    ) -> None: ...

    @abstractmethod
    async def list_changed_files(self, pr: PullRequestRef) -> Sequence[FileDiff]: ...
