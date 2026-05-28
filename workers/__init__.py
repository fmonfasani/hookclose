"""Execution workers.

Workers execute tasks; they never control workflows or decide architecture. The
:class:`OpenClawWorker` is the persistent execution runtime (sandboxed command
execution, branch-per-task, retries, artifacts, events).
"""

from __future__ import annotations

# Importing the events modules registers their events in the global EVENT_REGISTRY.
import events.domain.architecture
import events.domain.worker
from workers.architect import (
    ClaudeArchitectWorker,
    InMemoryReviewStore,
    ReviewResult,
    ReviewStore,
)
from workers.architect_prompts import ReviewKind
from workers.codegen import CodeGenerator, GenerationResult
from workers.contracts import (
    ArtifactStore,
    CommandResult,
    CommandRunner,
    ExecutionReport,
    FilePatch,
    InMemoryArtifactStore,
    InMemoryTaskSource,
    StepResult,
    TaskSource,
)
from workers.openclaw import OpenClawWorker
from workers.runners import (
    DockerCommandRunner,
    FileArtifactStore,
    LocalCommandRunner,
)
from workers.workspace import Workspace, WorkspaceManager

__all__ = [
    "ArtifactStore",
    "ClaudeArchitectWorker",
    "CodeGenerator",
    "CommandResult",
    "CommandRunner",
    "DockerCommandRunner",
    "ExecutionReport",
    "FileArtifactStore",
    "FilePatch",
    "GenerationResult",
    "InMemoryArtifactStore",
    "InMemoryReviewStore",
    "InMemoryTaskSource",
    "LocalCommandRunner",
    "OpenClawWorker",
    "ReviewKind",
    "ReviewResult",
    "ReviewStore",
    "StepResult",
    "TaskSource",
    "Workspace",
    "WorkspaceManager",
]
