# AINE — AI-Native Engineering Platform

> Operational infrastructure for **autonomous software development**.
> Not a chatbot. Not an agent. A runtime for orchestrating specialized agents under deterministic, observable, event-capable workflows.

---

## 1. Purpose

AINE is a **shared operational runtime** that lets specialized AI agents:

- generate code autonomously
- review pull requests automatically
- run, repair and validate tests
- coordinate across multi-agent workflows
- execute 24/7 with operational memory
- emit and react to events
- run inside isolated sandboxes
- be observed end-to-end via OpenTelemetry

The platform is **vendor-agnostic** (LLM providers, VCS, storage are adapters), **deterministic-first** (state machines drive behavior; LLMs are tools, not the runtime), and **event-capable** (every state transition is an emittable event).

---

## 2. Architectural Pillars

| Pillar | Decision |
| --- | --- |
| Determinism | All workflows are state machines; LLM calls happen *inside* states, never *between* them. |
| Event-capable | Every meaningful state change emits a versioned domain event. |
| Operational-memory first | Memory is a first-class subsystem (episodic + semantic + operational). |
| Multi-agent | Agents are registered capabilities, not hardcoded calls. |
| Vendor-agnostic | LLM, VCS, storage, vector — all behind ports. |
| Async-first | Every I/O contract is `async`; sync is the exception. |
| Clean Architecture | Domain (contracts/events/workflows) does not depend on adapters. |
| Docker-first | Local dev mirrors prod via `docker-compose`. |

### Dependency direction

```
  adapters/  api/  tasks/        <-- frameworks & I/O
        |
        v
  runtime/  scheduler/  sandbox/ <-- orchestration
        |
        v
  workflows/  agents/  memory/   <-- application
        |
        v
  contracts/  events/            <-- domain (no deps on anything above)
```

No module may import from a layer above its own.

---

## 3. Bounded Contexts

| Context | Responsibility |
| --- | --- |
| `runtime/` | Kernel, lifecycle, supervisor, dispatcher, FastAPI surface. |
| `agents/` | Agent descriptors, capabilities, registry. Zero business logic. |
| `contracts/` | All `Protocol` definitions. Pure interfaces. **No imports from adapters.** |
| `events/` | Versioned domain events + event-bus contract. |
| `workflows/` | Deterministic state machines. |
| `memory/` | Episodic, semantic (pgvector), operational memory. |
| `sandbox/` | Isolated execution environments and resource policies. |
| `observability/` | Tracing, metrics, structured logs, audit trail. |
| `scheduler/` | Cron + trigger-based recurring jobs. |
| `tasks/` | Celery integration. Async work outside the request path. |
| `adapters/` | LLM, VCS, vector store, storage, HTTP outbound. |
| `infra/` | Postgres/Redis/OTEL configs. |
| `docker/` | Container definitions. |
| `specs/` | Architectural decision records and design specs. |
| `reviews/` | Code review templates and artifacts. |

See [`specs/bounded-contexts.md`](specs/bounded-contexts.md) for context maps.

---

## 4. Tech Stack

- **Python 3.11+**, fully typed (mypy `strict`).
- **FastAPI** — HTTP surface for the runtime.
- **PostgreSQL 16** + **pgvector** — relational + vector storage.
- **Redis 7** — broker, cache, pub/sub.
- **Celery 5** — durable task execution.
- **SQLAlchemy 2.0** async — ORM + UoW.
- **Pydantic v2** — schemas, settings, validation.
- **OpenTelemetry** — traces, metrics, logs.
- **Docker Compose** — local-first dev.
- **Ruff + mypy + pytest** — quality gates.

---

## 5. Local bootstrap

```bash
# Linux/macOS
./scripts/bootstrap.sh

# Windows (PowerShell)
./scripts/bootstrap.ps1
```

Then:

```bash
docker compose up -d
# API:        http://localhost:8000/health
# Flower:     http://localhost:5555
# OTEL UI:    http://localhost:16686
```

---

## 6. Layout

```
.
├── runtime/         kernel, lifecycle, FastAPI surface
├── agents/          agent descriptors & registry (no logic yet)
├── contracts/       Protocols — the project's API surface
├── events/          domain events
├── workflows/       deterministic state machines
├── memory/          episodic + semantic + operational
├── sandbox/         isolated execution
├── observability/   tracing/metrics/logs/audit
├── scheduler/       cron + triggers
├── tasks/           Celery scaffolding
├── adapters/        outbound integrations
├── infra/           postgres/redis/otel configs
├── docker/          Dockerfiles
├── specs/           architecture & ADRs
├── reviews/         review templates
├── scripts/         bootstrap & ops
├── tests/           unit / integration / contract
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## 7. Engineering

| Doc | Purpose |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Principles, layering, bounded contexts, runtime planes. |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Local setup, env/secrets, quality gates, releases. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Workflow, commit convention, PR rules. |
| [ROADMAP.md](ROADMAP.md) | Phased build plan and the gate to VPS deployment. |
| [docs/observability.md](docs/observability.md) | Logging, tracing, metrics, audit conventions. |

```bash
make dev      # set up dev env + hooks
make check    # lint + typecheck + tests (the CI gate)
```

## 8. Status

**Runtime core in progress.** Foundation (contracts, events, deterministic workflows,
sandbox, memory, observability primitives, scheduler, tasks) is in place. Operational
engineering (CI/CD, tooling, runtime-state persistence) is established. Providers,
routing, workers, chaining, and self-healing are being built in phases — see
[ROADMAP.md](ROADMAP.md). Build state lives in `SYSTEM_STATE.json`.

> **Deployment:** VPS deployment is gated until the local runtime core is stable
> (queues, workers, routing, retry loops, chaining all verified).
