"""Event bus port — pub/sub for domain events."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from events.base import DomainEvent

EventHandler = Callable[[DomainEvent], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class EventSubscription:
    subscription_id: str
    topics: tuple[str, ...]
    handler: EventHandler


@runtime_checkable
class EventBusPort(Protocol):
    """Publishes and subscribes to versioned domain events.

    Delivery semantics MUST be at-least-once. Handlers MUST be idempotent
    (use `event.event_id` as the dedup key).
    """

    async def publish(self, event: DomainEvent) -> None: ...

    async def publish_many(self, events: Iterable[DomainEvent]) -> None: ...

    async def subscribe(
        self,
        topics: Iterable[str],
        handler: EventHandler,
        *,
        consumer_group: str,
    ) -> EventSubscription: ...

    async def unsubscribe(self, subscription_id: str) -> None: ...
