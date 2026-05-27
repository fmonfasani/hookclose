# Contributing to HookClose / AINE Runtime

This is an **operational runtime**, not a library of one-off scripts. Contributions
are held to engineering standards that keep the system deterministic, reproducible,
and observable. Read this before opening a PR.

## Ground rules

1. **Deterministic-first.** State machines drive behavior. LLM calls happen *inside*
   states, never *between* them. If you add non-determinism, it must be bounded and
   documented.
2. **Vendor-agnostic.** LLM providers, VCS, and storage live behind ports
   (`contracts/`). Never hardcode a provider into the runtime or `WorkflowEngine`.
3. **Layered dependencies.** A module may not import from a layer above its own
   (see [ARCHITECTURE.md](ARCHITECTURE.md)). `contracts/` and `events/` import nothing
   from adapters.
4. **Typed and tested.** `mypy --strict` must pass. New behavior needs tests.
5. **Observable.** New state transitions emit events; new subsystems expose metrics,
   traces, and structured logs.

## Workflow

```bash
# 1. Set up the dev environment (creates .venv, installs dev deps, hooks)
make dev

# 2. Create a branch
git checkout -b feat/<short-name>      # or fix/, chore/, docs/

# 3. Make your change + tests

# 4. Run the full local gate (mirrors CI)
make check

# 5. Commit (Conventional Commits) and open a PR
git commit -m "feat(providers): add cooldown handling"
```

## Commit convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

types:  feat | fix | refactor | perf | test | docs | chore | ci | build
scope:  runtime | providers | routing | workers | workflows | events |
        observability | scheduler | tasks | adapters | ci
```

Commit type drives [semantic versioning](#versioning): `feat` → minor, `fix` → patch,
`feat!`/`BREAKING CHANGE:` → major.

## Quality gates

| Gate | Command | CI job |
| --- | --- | --- |
| Lint + format | `make lint` | `lint` |
| Type check | `make typecheck` | `typecheck` |
| Tests + coverage | `make test` | `test` |
| Everything | `make check` | `ci-ok` |

Pre-commit hooks run lint/format/mypy on staged files. Install with `make hooks`.

## Pull requests

- Keep PRs small and focused on one concern.
- Fill in the PR template, including the determinism & observability notes.
- A PR is mergeable when the `CI passed` status check is green.
- Do not commit secrets, `.env`, or generated artifacts.

## Versioning

The project follows [SemVer](https://semver.org/). Releases are cut from `main` via a
tag `vMAJOR.MINOR.PATCH`; see [DEVELOPMENT.md](DEVELOPMENT.md#releases). Tagging triggers
the release workflow.
