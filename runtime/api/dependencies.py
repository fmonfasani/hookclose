"""Common FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from runtime.config import RuntimeSettings, get_settings
from runtime.registry import ComponentRegistry


def get_registry(request: Request) -> ComponentRegistry:
    return request.app.state.registry  # type: ignore[no-any-return]


SettingsDep = Annotated[RuntimeSettings, Depends(get_settings)]
RegistryDep = Annotated[ComponentRegistry, Depends(get_registry)]
