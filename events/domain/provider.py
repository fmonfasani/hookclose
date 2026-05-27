"""Provider lifecycle events.

These make every routing/failover decision in the ProviderManager observable and
auditable. They carry no vendor secrets — only names, reasons, and counters.
"""

from __future__ import annotations

from typing import ClassVar

from events.base import DomainEvent
from events.schema import EventTopic, register_event


@register_event
class ProviderSelected(DomainEvent):
    event_type: ClassVar[str] = "provider.selected"
    topic: ClassVar[str] = EventTopic.PROVIDER.value

    provider: str
    capability: str
    attempt: int


@register_event
class ProviderInvocationSucceeded(DomainEvent):
    event_type: ClassVar[str] = "provider.invocation_succeeded"
    topic: ClassVar[str] = EventTopic.PROVIDER.value

    provider: str
    capability: str
    total_tokens: int


@register_event
class ProviderFailedOver(DomainEvent):
    event_type: ClassVar[str] = "provider.failed_over"
    topic: ClassVar[str] = EventTopic.PROVIDER.value

    provider: str
    capability: str
    reason: str
    error_code: str


@register_event
class ProviderCooldownEntered(DomainEvent):
    event_type: ClassVar[str] = "provider.cooldown_entered"
    topic: ClassVar[str] = EventTopic.PROVIDER.value

    provider: str
    status: str
    cooldown_until: str | None
    reason: str


@register_event
class ProviderCreditExhausted(DomainEvent):
    event_type: ClassVar[str] = "provider.credit_exhausted"
    topic: ClassVar[str] = EventTopic.PROVIDER.value

    provider: str


@register_event
class ProviderRecovered(DomainEvent):
    event_type: ClassVar[str] = "provider.recovered"
    topic: ClassVar[str] = EventTopic.PROVIDER.value

    provider: str


@register_event
class AllProvidersExhausted(DomainEvent):
    event_type: ClassVar[str] = "provider.all_exhausted"
    topic: ClassVar[str] = EventTopic.PROVIDER.value

    capability: str
    tried: tuple[str, ...]
