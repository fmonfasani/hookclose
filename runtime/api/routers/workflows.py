"""Workflow control plane endpoints (scaffolding)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/workflows", tags=["workflows"])


class StartWorkflowRequest(BaseModel):
    definition: str = Field(..., description="Registered workflow definition name")
    version: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    definition: str
    version: str
    runtime_state: str
    application_state: str
    correlation_id: str


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_workflow(_payload: StartWorkflowRequest) -> WorkflowResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "workflow engine not wired yet")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str) -> WorkflowResponse:
    del workflow_id
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "workflow engine not wired yet")


@router.post("/{workflow_id}/cancel", response_model=WorkflowResponse)
async def cancel_workflow(workflow_id: str, reason: str = "operator_request") -> WorkflowResponse:
    del workflow_id, reason
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "workflow engine not wired yet")
