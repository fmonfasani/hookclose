"""HTTP middleware installation."""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from runtime.config import RuntimeSettings


def install_middleware(app: FastAPI, settings: RuntimeSettings) -> None:
    """Attach middleware in the canonical order.

    Order (outermost first):
      1. CORS
      2. Tracing / correlation-id propagation  (added when telemetry is wired)
      3. Auth                                   (added when authn/z is in)
      4. Request log                            (added when telemetry is wired)
    """
    origins = [o.strip() for o in settings.api.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
