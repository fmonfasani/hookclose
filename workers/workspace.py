"""Per-task workspaces with branch-per-task isolation.

Each task gets its own directory and its own git branch (``task/<id>``), so
concurrent executions never clobber each other and every task's changes are
isolated and reviewable. Git operations are best-effort: if git is unavailable
the workspace still works, it just isn't branched.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from workers.contracts import CommandRunner, FilePatch


class Workspace:
    def __init__(self, root: Path, branch: str, *, git_enabled: bool) -> None:
        self.root = root
        self.branch = branch
        self.git_enabled = git_enabled

    def write_patches(self, patches: Iterable[FilePatch]) -> tuple[str, ...]:
        """Materialize file patches into the workspace. Returns written paths."""
        written: list[str] = []
        for patch in patches:
            target = (self.root / patch.path).resolve()
            # Guard against path traversal outside the workspace.
            if not str(target).startswith(str(self.root.resolve())):
                raise ValueError(f"patch path escapes workspace: {patch.path!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(patch.content, encoding="utf-8")
            written.append(patch.path)
        return tuple(written)


class WorkspaceManager:
    """Creates branch-per-task workspaces under a base directory."""

    def __init__(self, base_dir: str | Path, runner: CommandRunner) -> None:
        self._base = Path(base_dir)
        self._runner = runner

    @staticmethod
    def branch_name(task_id: str) -> str:
        return f"task/{task_id[:12]}"

    async def create(self, task_id: str) -> Workspace:
        root = self._base / task_id
        root.mkdir(parents=True, exist_ok=True)
        branch = self.branch_name(task_id)
        git_enabled = await self._init_branch(root, branch)
        return Workspace(root, branch, git_enabled=git_enabled)

    async def _init_branch(self, root: Path, branch: str) -> bool:
        """Init a repo (if needed) and check out the task branch. Best-effort."""
        cwd = str(root)
        init = await self._runner.run(["git", "init", "-q"], cwd=cwd, timeout=30)
        if not init.success:
            return False  # git unavailable / failed — continue without branching
        await self._runner.run(["git", "checkout", "-q", "-b", branch], cwd=cwd, timeout=30)
        return True
