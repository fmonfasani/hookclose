# Architecture

AINE is an **AI-native operational runtime** for autonomous software
development. It orchestrates specialized agents under deterministic, observable,
event-capable workflows. The runtime is the system of record; LLMs are tools invoked
*inside* it, never the control plane.

## 1. Principles

| Principle | What it means in code |
| --- | --- |
| Determinism-first | Workflows are explicit state machines. LLM calls occur inside states. Transitions are pure functions of `(state, event)`. |
| Vendor-agnostic | LLMs, VCS, storage, vector stores sit behind `Protocol`s in `contracts/`. Swapping a vendor is an adapter change. |
| Event-capable | Every meaningful transition emits a versioned domain event (`events/`). |
| Operational-memory first | Episodic + semantic + operational memory are first-class subsystems. |
| Async-first | Every I/O contract is `async`. Sync is the exception. |
| Reproducible | Builds, runtime state, and tests are deterministic and re-runnable. |

## 2. Layered dependency direction

```
  adapters/  runtime/api/  tasks/        <-- frameworks & I/O (outermost)
        |
        v
  runtime/  scheduler/  sandbox/         <-- orchestration
        |
        v
  workflows/  agents/  memory/           <-- application
        |
        v
  contracts/  events/                    <-- domain (depends on nothing above)
```

**Rule:** no module imports from a layer above its own. Relative imports beyond the
parent are banned (`ruff` `TID`). `contracts/` and `events/` must not import adapters.

## 3. Bounded contexts

| Context | Responsibility |
| --- | --- |
| `runtime/` | Kernel, lifecycle, dispatcher, registry, FastAPI surface, runtime-state persistence. |
| `contracts/` | All `Protocol` definitions. Pure interfaces, no adapter imports. |
| `events/` | Versioned domain events + event-bus contract. |
| `workflows/` | Deterministic state machines and their definitions. |
| `agents/` | Agent descriptors, capabilities, registry. No business logic. |
| `memory/` | Episodic, semantic (pgvector), operational memory. |
| `sandbox/` | Isolated execution environments and resource policies. |
| `observability/` | Tracing, metrics, structured logs, audit, health. |
| `scheduler/` | Cron + trigger-based recurring jobs. |
| `tasks/` | Task model, queues, routing, executor (async work off the request path). |
| `adapters/` | LLM, VCS, vector store, storage, HTTP, event-bus, telemetry. |
| `infra/` | Postgres/Redis/OTEL configs. |
| `docker/` | Container definitions. |

## 4. Runtime planes

- **Control plane** — `runtime/` + `workflows/`. Owns orchestration and state. The only
  place transitions are decided.
- **Cognition plane** — providers/agents. Expensive reasoning (Claude) and execution
  (OpenCode/local) live here, reached through `contracts/llm_provider.py`. Selection is
  delegated to the routing engine; the control plane never names a vendor.
- **Execution plane** — `sandbox/` + workers. Runs untrusted/generated code under
  resource and network policies.
- **Memory plane** — `memory/`. Persists episodic events, semantic embeddings, and
  operational state.

## 5. State & persistence

- **Runtime state** — a single atomic snapshot in `SYSTEM_STATE.json`, owned by
  `runtime/state.py` (`RuntimeStateStore`). Writes are atomic (`os.replace`) and sorted
  for review-friendly diffs. This makes restarts reproducible and progress auditable.
- **Durable data** — PostgreSQL (+ pgvector) for relational + vector data.
- **Ephemeral / broker** — Redis for queues, pub/sub, cache, cooldown timers.

## 6. Observability conventions

See [docs/observability.md](docs/observability.md). In short:

- **Logs** are structured (`structlog`), JSON in non-local envs, always carry a
  `correlation_id`. No `print`.
- **Traces** follow OpenTelemetry. One span per state transition and per provider call.
- **Metrics** are namespaced `hookclose_<subsystem>_<name>`. Every subsystem exposes
  counters for attempts/failures and a latency histogram.
- **Audit** — security/decision-relevant actions (routing decisions, repairs, escalations)
  write to the audit trail.

## 7. Build phases

The runtime is built in deterministic phases tracked in `SYSTEM_STATE.json` and
[ROADMAP.md](ROADMAP.md): runtime core → providers → routing → workers → chaining →
self-healing → CI/CD → stable. **Deployment to a VPS happens only after the runtime
core is stable locally** (queues, workers, routing, retry loops, chaining all working).
