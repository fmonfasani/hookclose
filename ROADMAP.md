# AINE Runtime — Build Roadmap

Deterministic, phase-by-phase build. The full prompt set lives in [`prompts/`](prompts/INDEX.md)
(numbers preserved; 08–18 were removed as empty/superseded). State is tracked in
`SYSTEM_STATE.json` (`runtime/state.py`). **VPS deployment happens only after the runtime
core is stable locally.**

## Phase 1 — Foundation runtime ✅
- [x] Prompts 01–07 — Repo skeleton, WorkflowEngine, EventBus, Task system, sandbox,
  agent contracts, Claude code adapter (scaffold). See [`prompts/INDEX.md`](prompts/INDEX.md).

## Phase 2 — Operational engineering (`RUNTIME_CORE`) ✅
- [x] Prompt 19 — Production-grade repo: docs, CI/lint/test/type pipelines, pre-commit,
  Makefile, runtime-state persistence, logging/observability conventions. *(no new AI
  features)*

## Phase 3 — Providers & routing ✅
- [x] Prompt 20 — ProviderManager REAL (Base/Registry/Manager, Claude/OpenCode/Gemini/Local,
  failover, cooldown, token budgeting, persistence). → `providers/`
- [x] Prompt 21 — ComplexityRoutingEngine (complexity scoring, cost/priority/context-aware,
  deterministic + auditable). → `providers/routing.py`

## Phase 4 — Workers ✅
- [x] Prompt 22 — OpenClawWorker REAL (consumer, sandbox exec, git branch-per-task, patching,
  test/lint, retry loops, artifacts). *Executes tasks; does not control workflows.* → `workers/`
- [x] Prompt 23 — ClaudeArchitectWorker (architecture/review/spec/refactor handlers).
  *Expensive cognition layer, not execution.* → `workers/architect.py`

## Phase 5 — Autonomy ✅
- [x] Prompt 24 — AutonomousTaskChaining (dependency graph, auto task generation, repair/
  escalation/review/deploy tasks; bounded — no infinite loops). → `orchestration/`
- [x] Prompt 25 — SelfHealingRuntime (failure analysis, stacktrace parsing, bounded repair
  loops, rollback, escalation). → `orchestration/self_healing.py`

## Phase 6 — CI/CD & release ✅
- [x] Prompt 26 — Full CI/CD: lint, pytest, mypy, security scan, Docker build validation,
  runtime smoke tests, release workflow, coverage gate, branch protection. → `.github/workflows/`

## Phase 7 — Deployment (gated)
- [ ] Prompt 27 — VPS (Hetzner) deployment (merged ex-11/18) — **only after** local
  runtime core is stable: queues, workers, provider routing, retry loops, task chaining
  all verified.

---

### Gate to leave the runtime core

Before VPS deployment, all of the following must be green locally:
runtime stable · queues working · workers working · provider routing working ·
retry loops working · task chaining working.
