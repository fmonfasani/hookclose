# Observability conventions

These conventions are mandatory for every subsystem. They are what make the runtime
debuggable in production without a debugger.

## Logging

- Use the structured logger (`observability/logging.py` → `structlog` adapter). **No
  `print`, no stdlib `logging` directly.**
- Format: `json` in `dev`/`staging`/`prod`, `console` allowed in `local`
  (`HOOKCLOSE_LOG_FORMAT`).
- Every log line carries a `correlation_id`. Bind it once at the entry point:

  ```python
  log = logger.with_correlation(correlation_id).bind(component="providers")
  log.info("provider.call.start", provider="claude", task_id=task_id)
  ```

- Event names are dotted, lowercase, `subsystem.noun.verb` (`routing.decision.made`,
  `repair.loop.exhausted`).
- Never log secrets, tokens, raw prompts containing credentials, or full `.env` values.

## Tracing (OpenTelemetry)

- One span per **state transition** and per **provider/LLM call**.
- Span names match the log event noun (`provider.call`, `workflow.transition`).
- Propagate `correlation_id` as a span attribute and across async boundaries.
- Sampling ratio is configurable (`HOOKCLOSE_OTEL_SAMPLER_RATIO`); default 1.0 locally.

## Metrics

Namespace: `hookclose_<subsystem>_<name>`. Every subsystem exposes at minimum:

| Metric | Type | Labels |
| --- | --- | --- |
| `hookclose_<sub>_attempts_total` | counter | `outcome` |
| `hookclose_<sub>_failures_total` | counter | `reason` |
| `hookclose_<sub>_latency_seconds` | histogram | `operation` |

Routing and providers additionally track: tokens consumed, cooldowns entered, failovers,
and per-provider health.

## Audit trail

Decision- and security-relevant actions write an audit record (`observability/audit.py`):
routing decisions, provider failovers, repair attempts, escalations, and any human-in-the-loop
override. Audit records are append-only and carry actor, correlation id, and a deterministic
reason.

## Health

- Liveness: process is up.
- Readiness: required dependencies (Postgres, Redis, at least one healthy provider) reachable.
- Exposed via the API health router and consumed by the runtime smoke tests in CI.
