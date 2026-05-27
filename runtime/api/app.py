"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from runtime.api.middleware import install_middleware
from runtime.api.routers import agents as agents_router
from runtime.api.routers import events as events_router
from runtime.api.routers import health as health_router
from runtime.api.routers import workflows as workflows_router
from runtime.bootstrap import build_lifecycle, build_registry
from runtime.config import get_settings


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    app.state.registry = await build_registry(settings)
    app.state.lifecycle = build_lifecycle()
    # NOTE: app.state.lifecycle.startup() is intentionally NOT called yet.
    # Concrete adapters are not wired in the scaffolding commit.
    try:
        yield
    finally:
        # await app.state.lifecycle.shutdown()
        pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AINE Runtime",
        version="0.1.0",
        description="AI-Native operational platform — runtime API.",
        lifespan=_lifespan,
        docs_url="/docs" if settings.env != "prod" else None,
        redoc_url=None,
    )

    install_middleware(app, settings)

    app.include_router(health_router.router)
    app.include_router(workflows_router.router, prefix="/v1")
    app.include_router(agents_router.router, prefix="/v1")
    app.include_router(events_router.router, prefix="/v1")
    return app
