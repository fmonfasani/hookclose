"""
contracts/ — Pure Protocols and ports.

The `contracts` package is the **innermost layer** of the architecture. It
defines the interfaces (`typing.Protocol`) that the rest of the system depends
on. Nothing in here may import from `adapters`, `runtime`, `tasks`, or any
framework-bound module.

Dependency rule: every other package MAY import from `contracts`.
                 `contracts` MUST NOT import from any other in-tree package
                 except `events` (which is also in the domain layer).

This is what makes the codebase vendor-agnostic and testable.
"""

from contracts.agent import AgentPort, AgentRunContext
from contracts.code_executor import CodeExecutorPort
from contracts.event_bus import EventBusPort, EventHandler, EventSubscription
from contracts.llm_provider import LLMProviderPort, LLMRequest, LLMResponse
from contracts.memory import EpisodicMemoryPort, OperationalMemoryPort, SemanticMemoryPort
from contracts.repository import RepositoryPort
from contracts.sandbox import SandboxPort
from contracts.task_runner import TaskRunnerPort
from contracts.telemetry import TelemetryPort
from contracts.unit_of_work import UnitOfWorkPort
from contracts.vcs import VCSPort
from contracts.workflow import WorkflowEnginePort, WorkflowHandle

__all__ = [
    "AgentPort",
    "AgentRunContext",
    "CodeExecutorPort",
    "EpisodicMemoryPort",
    "EventBusPort",
    "EventHandler",
    "EventSubscription",
    "LLMProviderPort",
    "LLMRequest",
    "LLMResponse",
    "OperationalMemoryPort",
    "RepositoryPort",
    "SandboxPort",
    "SemanticMemoryPort",
    "TaskRunnerPort",
    "TelemetryPort",
    "UnitOfWorkPort",
    "VCSPort",
    "WorkflowEnginePort",
    "WorkflowHandle",
]
