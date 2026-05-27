# Worker / beat image — extends base.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
RUN python -m pip install -U pip wheel \
 && pip install ".[dev]"

COPY . /app

RUN groupadd -r aine && useradd -r -g aine -d /app -s /sbin/nologin aine \
 && chown -R aine:aine /app

USER aine

CMD ["celery", "-A", "tasks.app", "worker", "--loglevel=INFO"]
