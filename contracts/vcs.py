"""VCS port — abstract version control (GitHub, GitLab, Gitea, raw git)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class RepoRef:
    provider: str
    owner: str
    name: str
    default_branch: str


@dataclass(frozen=True, slots=True)
class PullRequestRef:
    repo: RepoRef
    number: int
    head_sha: str
    base_branch: str
    head_branch: str


@dataclass(frozen=True, slots=True)
class FileDiff:
    path: str
    status: str  # "added" | "modified" | "removed" | "renamed"
    additions: int
    deletions: int
    patch: str | None


@runtime_checkable
class VCSPort(Protocol):
    """All write operations MUST be idempotent on `(repo, branch, sha)`."""

    async def clone(self, repo: RepoRef, *, ref: str, dest: str) -> None: ...

    async def create_branch(self, repo: RepoRef, name: str, from_ref: str) -> None: ...

    async def commit(
        self,
        repo: RepoRef,
        branch: str,
        message: str,
        files: dict[str, bytes],
        *,
        author: str,
    ) -> str: ...

    async def open_pull_request(
        self,
        repo: RepoRef,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> PullRequestRef: ...

    async def review_pull_request(
        self,
        pr: PullRequestRef,
        body: str,
        decision: str,
    ) -> None: ...

    async def list_changed_files(self, pr: PullRequestRef) -> Sequence[FileDiff]: ...
