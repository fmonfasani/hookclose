<!-- Keep PRs small, deterministic, and reviewable. -->

## Summary

<!-- What does this change do and why? Link the issue/prompt. -->

Closes #

## Type of change

- [ ] Runtime / orchestration
- [ ] Provider / adapter
- [ ] Workflow / state machine
- [ ] Observability
- [ ] Docs / tooling / CI
- [ ] Fix

## Checklist

- [ ] `make check` passes locally (lint + typecheck + tests)
- [ ] New behavior is covered by tests
- [ ] No new AI provider logic hardcoded into the runtime
- [ ] Public contracts (`contracts/`) unchanged, or change is documented
- [ ] Events emitted for new state transitions (if applicable)
- [ ] No secrets, credentials, or `.env` content committed

## Determinism & observability

<!-- Note any non-deterministic behavior introduced and how it is bounded.
     Note new metrics/traces/log events added. -->
