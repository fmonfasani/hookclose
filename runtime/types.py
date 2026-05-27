"""Shared scalar type aliases. Keep these *opaque* on purpose."""

from __future__ import annotations

from typing import NewType

RunId = NewType("RunId", str)
WorkflowId = NewType("WorkflowId", str)
CorrelationId = NewType("CorrelationId", str)
TenantId = NewType("TenantId", str)
ActorId = NewType("ActorId", str)
AgentName = NewType("AgentName", str)
