# API service image — extends base.
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

EXPOSE 8000

CMD ["uvicorn", "runtime.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
