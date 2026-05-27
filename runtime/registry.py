"""Component registry — the runtime's small DI container.

Bindings flow contracts -> adapters. Tests can override bindings without
touching the rest of the codebase.
"""

from __future__ import annotations

from typing import Any, TypeVar, cast

from runtime.errors import ConfigurationError, NotFoundError

T = TypeVar("T")


class ComponentRegistry:
    """Type-keyed registry for runtime singletons.

    Usage:
        registry.bind(EventBusPort, redis_event_bus)
        bus = registry.resolve(EventBusPort)
    """

    __slots__ = ("_bindings",)

    def __init__(self) -> None:
        self._bindings: dict[type, Any] = {}

    def bind(self, contract: type[T], instance: T, *, replace: bool = False) -> None:
        if not replace and contract in self._bindings:
            raise ConfigurationError(
                f"contract {contract.__name__} already bound (use replace=True)",
            )
        self._bindings[contract] = instance

    def resolve(self, contract: type[T]) -> T:
        try:
            return cast(T, self._bindings[contract])
        except KeyError as exc:
            raise NotFoundError(f"no binding registered for {contract.__name__}") from exc

    def has(self, contract: type) -> bool:
        return contract in self._bindings

    def clear(self) -> None:
        self._bindings.clear()
