# =============================================================================
# Sandbox base image. Used by the sandbox adapter to run untrusted code.
# Intentionally minimal. Specialised language images extend this.
# =============================================================================
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/workspace

RUN groupadd -r sandbox && useradd -r -g sandbox -d /workspace -s /bin/bash sandbox \
 && mkdir -p /workspace \
 && chown -R sandbox:sandbox /workspace

WORKDIR /workspace
USER sandbox
