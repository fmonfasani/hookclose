"""Execution workers.

Workers execute tasks; they never control workflows or decide architecture. The
:class:`OpenClawWorker` is the persistent execution runtime (sandboxed command
execution, branch-per-task, retries, artifacts, events).
"""

from __future__ import annotations

# Importing the events module registers worker events in the global EVENT_REGISTRY.
import events.domain.worker
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
    "CommandResult",
    "CommandRunner",
    "DockerCommandRunner",
    "ExecutionReport",
    "FileArtifactStore",
    "FilePatch",
    "InMemoryArtifactStore",
    "InMemoryTaskSource",
    "LocalCommandRunner",
    "OpenClawWorker",
    "StepResult",
    "TaskSource",
    "Workspace",
    "WorkspaceManager",
]
