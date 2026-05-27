"""
events/ — Versioned domain events.

Every meaningful state change in the system is an event. Events are:
  - immutable (frozen Pydantic models)
  - versioned (each event type carries `event_version`)
  - addressable (every event has a stable `event_id` ULID)
  - causally linked (`correlation_id` + `causation_id`)

Events live in the domain layer. They MUST NOT depend on adapters or runtime.
"""

from events.base import DomainEvent, EventMetadata
from events.domain.agent_lifecycle import (
    AgentInvoked,
    AgentRunCompleted,
    AgentRunFailed,
)
from events.domain.code_generation import (
    CodeGenerationCompleted,
    CodeGenerationFailed,
    CodeGenerationRequested,
)
from events.domain.code_review import (
    CodeReviewCompleted,
    CodeReviewRequested,
    ReviewFindingProduced,
)
from events.domain.repair import (
    RepairAttempted,
    RepairProposed,
    RepairValidated,
)
from events.domain.testing import (
    TestRunCompleted,
    TestRunFailed,
    TestRunRequested,
)
from events.domain.workflow import (
    WorkflowCancelled,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
    WorkflowStateTransitioned,
)
from events.schema import EVENT_REGISTRY, EventTopic

__all__ = [
    "EVENT_REGISTRY",
    "AgentInvoked",
    "AgentRunCompleted",
    "AgentRunFailed",
    "CodeGenerationCompleted",
    "CodeGenerationFailed",
    "CodeGenerationRequested",
    "CodeReviewCompleted",
    "CodeReviewRequested",
    "DomainEvent",
    "EventMetadata",
    "EventTopic",
    "RepairAttempted",
    "RepairProposed",
    "RepairValidated",
    "ReviewFindingProduced",
    "TestRunCompleted",
    "TestRunFailed",
    "TestRunRequested",
    "WorkflowCancelled",
    "WorkflowCompleted",
    "WorkflowFailed",
    "WorkflowStarted",
    "WorkflowStateTransitioned",
]
