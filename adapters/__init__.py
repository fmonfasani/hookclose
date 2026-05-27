"""
adapters/ — Outbound integrations.

Adapters are the *only* layer allowed to import vendor SDKs. They translate
from `contracts.*` ports into concrete provider calls and back, raising
domain-level errors from `runtime.errors`.

Subpackages:
  - `llm/`           — LLM providers (OpenAI, Anthropic, vLLM, …)
  - `vcs/`           — Version control (GitHub, GitLab, Gitea, raw git)
  - `vector_store/`  — pgvector and other vector backends
  - `storage/`       — SQLAlchemy + repository implementations
  - `event_bus/`     — Redis Streams / NATS / Kafka
  - `sandbox/`       — Docker, gVisor, firecracker
  - `telemetry/`     — OpenTelemetry exporters
  - `http/`          — Outbound HTTP base (httpx wrapper)

No concrete adapter is implemented in the scaffolding commit.
"""
