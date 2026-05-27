"""Event inspection endpoints (scaffolding).

Read-only by design: events are mutated only by the bus, never by HTTP.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/events", tags=["events"])


class EventTypeDescriptor(BaseModel):
    event_type: str
    event_version: int
    topic: str


@router.get("/types", response_model=list[EventTypeDescriptor])
async def list_event_types() -> list[EventTypeDescriptor]:
    from events.schema import EVENT_REGISTRY  # noqa: PLC0415 — lazy to avoid import cycle

    return [
        EventTypeDescriptor(
            event_type=cls.event_type,
            event_version=cls.event_version,
            topic=cls.topic,
        )
        for cls in EVENT_REGISTRY.values()
    ]


@router.get("/by-correlation/{correlation_id}")
async def by_correlation(correlation_id: str) -> dict[str, str]:
    del correlation_id
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "event store not wired yet")
