"""Typed configuration loader (Pydantic Settings).

Configuration is the **only** layer allowed to read environment variables.
Every other module receives an injected, typed settings object.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AINE_POSTGRES_", extra="ignore")

    host: str = "localhost"
    port: int = 5432
    db: str = "aine"
    user: str = "aine"
    password: SecretStr = SecretStr("aine")
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AINE_REDIS_", extra="ignore")

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: SecretStr | None = None

    @property
    def url(self) -> str:
        auth = f":{self.password.get_secret_value()}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AINE_CELERY_", extra="ignore")

    broker_url: str = "redis://localhost:6379/1"
    result_backend: str = "redis://localhost:6379/2"
    task_default_queue: str = "default"


class SandboxSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AINE_SANDBOX_", extra="ignore")

    default_timeout_sec: int = 120
    default_memory_mb: int = 1024
    default_cpu: float = 1.0
    network_policy: Literal["deny", "allow", "egress-only"] = "deny"


class ObservabilitySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AINE_OTEL_", extra="ignore")

    enabled: bool = True
    service_name: str = "aine-runtime"
    exporter_otlp_endpoint: str = "http://otel-collector:4317"
    sampler_ratio: float = 1.0


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AINE_API_", extra="ignore")

    host: str = "0.0.0.0"  # noqa: S104 — container-internal binding
    port: int = 8000
    workers: int = 1
    cors_origins: str = ""


class RuntimeSettings(BaseSettings):
    """Top-level settings aggregate. Inject this everywhere instead of
    reading env vars directly."""

    model_config = SettingsConfigDict(
        env_prefix="AINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    instance_id: str = ""

    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    api: APISettings = Field(default_factory=APISettings)


@lru_cache(maxsize=1)
def get_settings() -> RuntimeSettings:
    """Cached, process-wide settings accessor."""
    return RuntimeSettings()
