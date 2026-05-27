"""Agent inventory endpoints (scaffolding)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentDescriptor(BaseModel):
    name: str
    version: str
    capabilities: list[str]
    description: str


@router.get("", response_model=list[AgentDescriptor])
async def list_agents() -> list[AgentDescriptor]:
    return []


@router.get("/{name}", response_model=AgentDescriptor)
async def get_agent(name: str) -> AgentDescriptor:
    del name
    raise HTTPException(status.HTTP_404_NOT_FOUND, "no agents registered yet")
