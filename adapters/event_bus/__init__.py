"""Event bus adapters (Redis Streams first; NATS/Kafka pluggable)."""

from adapters.event_bus.base import EventBusAdapterBase

__all__ = ["EventBusAdapterBase"]
