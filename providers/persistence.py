"""Provider-state persistence.

Persisting health (status, cooldowns, token usage) lets the runtime survive
restarts without re-probing every vendor: a provider that was OFFLINE due to
credit exhaustion stays OFFLINE until its cooldown elapses.

The port is async to allow Redis/PostgreSQL adapters. The in-memory store is the
default and is fully deterministic for tests; the Redis adapter is provided as a
thin, integration-tested implementation.
"""

from __future__ import annotations

from datetime import datetime
import json
from typing import Protocol, cast, runtime_checkable

from providers.state import ProviderHealth, ProviderStatus


@runtime_checkable
class ProviderStateStore(Protocol):
    """Durable snapshot of per-provider health."""

    async def save(self, name: str, health: ProviderHealth) -> None: ...

    async def load(self, name: str) -> ProviderHealth | None: ...

    async def load_all(self) -> dict[str, ProviderHealth]: ...


def health_to_dict(health: ProviderHealth) -> dict[str, object]:
    return {
        "status": health.status.value,
        "consecutive_failures": health.consecutive_failures,
        "cooldown_until": health.cooldown_until.isoformat() if health.cooldown_until else None,
        "tokens_used": health.tokens_used,
        "total_requests": health.total_requests,
        "total_failures": health.total_failures,
        "last_error": health.last_error,
        "last_used_at": health.last_used_at.isoformat() if health.last_used_at else None,
    }


def health_from_dict(data: dict[str, object]) -> ProviderHealth:
    def _dt(value: object) -> datetime | None:
        return datetime.fromisoformat(value) if isinstance(value, str) else None

    return ProviderHealth(
        status=ProviderStatus(str(data["status"])),
        consecutive_failures=cast("int", data["consecutive_failures"]),
        cooldown_until=_dt(data.get("cooldown_until")),
        tokens_used=cast("int", data["tokens_used"]),
        total_requests=cast("int", data["total_requests"]),
        total_failures=cast("int", data["total_failures"]),
        last_error=cast("str | None", data.get("last_error")),
        last_used_at=_dt(data.get("last_used_at")),
    )


class InMemoryProviderStateStore:
    """Default store. Holds independent snapshots (no aliasing of live health)."""

    def __init__(self) -> None:
        self._data: dict[str, ProviderHealth] = {}

    async def save(self, name: str, health: ProviderHealth) -> None:
        self._data[name] = health.snapshot()

    async def load(self, name: str) -> ProviderHealth | None:
        stored = self._data.get(name)
        return stored.snapshot() if stored is not None else None

    async def load_all(self) -> dict[str, ProviderHealth]:
        return {name: h.snapshot() for name, h in self._data.items()}


class RedisProviderStateStore:
    """Redis-backed store (one hash field per provider, JSON-encoded).

    ``client`` is a ``redis.asyncio.Redis``-compatible object. Kept dependency-free
    here (duck-typed) so the package imports without redis installed.
    """

    def __init__(self, client: object, *, key: str = "providers:health") -> None:
        self._client = client
        self._key = key

    async def save(self, name: str, health: ProviderHealth) -> None:
        await self._client.hset(self._key, name, json.dumps(health_to_dict(health)))  # type: ignore[attr-defined]

    async def load(self, name: str) -> ProviderHealth | None:
        raw = await self._client.hget(self._key, name)  # type: ignore[attr-defined]
        if raw is None:
            return None
        return health_from_dict(json.loads(raw))

    async def load_all(self) -> dict[str, ProviderHealth]:
        raw = await self._client.hgetall(self._key)  # type: ignore[attr-defined]
        return {
            (k.decode() if isinstance(k, bytes) else k): health_from_dict(json.loads(v))
            for k, v in raw.items()
        }
