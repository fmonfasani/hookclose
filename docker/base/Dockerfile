# =============================================================================
# AINE base image — shared by api, worker, scheduler.
# Multi-stage build keeps the final image lean.
# =============================================================================

ARG PYTHON_VERSION=3.11-slim-bookworm

# --- build stage -------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml README.md ./
RUN python -m pip install -U pip wheel \
 && pip wheel --wheel-dir /wheels .

# --- runtime stage -----------------------------------------------------------
FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd -r aine && useradd -r -g aine -d /app -s /sbin/nologin aine

WORKDIR /app

COPY --from=build /wheels /wheels
RUN python -m pip install -U pip \
 && pip install --no-index --find-links=/wheels aine-platform \
 && rm -rf /wheels

COPY --chown=aine:aine . /app

USER aine
