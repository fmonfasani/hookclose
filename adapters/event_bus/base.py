"""Abstract event-bus adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from contracts.event_bus import EventHandler, EventSubscription
from events.base import DomainEvent


class EventBusAdapterBase(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...

    @abstractmethod
    async def publish_many(self, events: Iterable[DomainEvent]) -> None: ...

    @abstractmethod
    async def subscribe(
        self,
        topics: Iterable[str],
        handler: EventHandler,
        *,
        consumer_group: str,
    ) -> EventSubscription: ...

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None: ...
