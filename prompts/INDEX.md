# Build Prompts — Index

The deterministic, phase-by-phase build plan for HookClose / AINE. Each file is one
prompt; numbers are preserved from the original sequence (gaps at 08–18 are intentional —
those were empty or superseded, see below). Execute **in numeric order**. Build state is
tracked in [`../SYSTEM_STATE.json`](../SYSTEM_STATE.json); the phase map is in
[`../ROADMAP.md`](../ROADMAP.md).

| # | File | Topic | Status |
| --- | --- | --- | --- |
| 00 | [00-master.md](00-master.md) | Orchestrator meta-instructions | reference |
| 01 | [01-repo-skeleton.md](01-repo-skeleton.md) | Repo skeleton / architecture | ✅ done |
| 02 | [02-workflow-engine.md](02-workflow-engine.md) | WorkflowEngine (state machine core) | ✅ done |
| 03 | [03-event-bus.md](03-event-bus.md) | Internal EventBus | ✅ done |
| 04 | [04-task-system.md](04-task-system.md) | AI-native Task system | ✅ done |
| 05 | [05-sandbox-runtime.md](05-sandbox-runtime.md) | Sandbox runtime | ✅ done (scaffold) |
| 06 | [06-agent-contracts.md](06-agent-contracts.md) | Agent contracts / registry | ✅ done |
| 07 | [07-claude-code-adapter.md](07-claude-code-adapter.md) | ClaudeCodeAdapter | ⚠️ precursor of #23 |
| 19 | [19-operational-infra.md](19-operational-infra.md) | Operational engineering infra | ✅ **done** |
| 20 | [20-provider-manager.md](20-provider-manager.md) | ProviderManager REAL | ⏳ **next** |
| 21 | [21-complexity-routing-engine.md](21-complexity-routing-engine.md) | ComplexityRoutingEngine | ⏳ pending |
| 22 | [22-openclaw-worker.md](22-openclaw-worker.md) | OpenClawWorker REAL | ⏳ pending |
| 23 | [23-claude-architect-worker.md](23-claude-architect-worker.md) | ClaudeArchitectWorker | ⏳ pending |
| 24 | [24-autonomous-task-chaining.md](24-autonomous-task-chaining.md) | AutonomousTaskChaining | ⏳ pending |
| 25 | [25-self-healing-runtime.md](25-self-healing-runtime.md) | SelfHealingRuntime | ⏳ pending |
| 26 | [26-github-cicd.md](26-github-cicd.md) | GitHub CI/CD (finalize) | ⏳ pending |
| 27 | [27-vps-production.md](27-vps-production.md) | VPS production runtime | 🔒 **gated** (post-26) |

## Consolidation notes (2026-05-27)

This folder replaces prompts scattered across the repo root and `tasks/`. During
consolidation the following were removed as **empty or superseded**:

- **08, 09** — empty (0 bytes).
- **10 SelfRepairEngine** & **17 Self-Repair/Self-Healing** — superseded by **25**.
- **12 ProviderManager** — superseded by **20**.
- **13 OpenClaw Worker** — superseded by **22**.
- **14 Claude High-Intelligence Worker** — superseded by **23**.
- **15 Autonomous Scheduler** — folded into **24** (+ existing `scheduler/`).
- **16 Docker AI Factory** — folded into **26** (CI/Docker) and **27** (prod compose).
- **11 VPS production** & **18 VPS Production Runtime** — duplicates, merged into **27**.

The active execution line is therefore: **01–07 → 19 → 20 → 21 → 22 → 23 → 24 → 25 → 26 → 27 (gated)**.
