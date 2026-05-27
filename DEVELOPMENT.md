# Development guide

Everything you need to run, test, and operate the runtime locally.

## 1. Prerequisites

- **Python 3.11+**
- **Docker + Docker Compose** (for Postgres, Redis, OTEL, runtime services)
- **make** (Git Bash / WSL on Windows, or use the PowerShell equivalents below)

## 2. First-time setup

```bash
make dev          # create .venv, install ".[dev]", install pre-commit hooks
```

Equivalent manual steps:

```bash
python -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
```

## 3. Environment & secrets

- Configuration is read **only** by `runtime/config.py` (Pydantic Settings). Never read
  env vars elsewhere — inject the typed settings object.
- Copy the template and edit locally:

  ```bash
  cp .env.example .env
  ```

- `.env`, `*.pem`, `*.key` are git-ignored. **Never commit secrets.** Local passwords in
  `.env.example` are placeholders for local-only use.
- In CI/prod, secrets come from the environment / secret store, not files.

## 4. Running locally

```bash
make up-data       # Postgres + Redis only
make bootstrap-db  # initialize schema
make up            # full stack via docker-compose
```

Endpoints:

- API health: <http://localhost:8000/health>
- Flower (Celery): <http://localhost:5555>
- Jaeger (traces): <http://localhost:16686>

CLI entrypoint (installed as `aine`):

```bash
aine --help
```

### Windows / PowerShell

```powershell
./scripts/bootstrap.ps1     # prerequisites + .env + data services + db init
```

## 5. Quality gates

| Command | What it does |
| --- | --- |
| `make lint` | `ruff check` + `ruff format --check` |
| `make format` | autofix lint + apply formatting |
| `make typecheck` | `mypy --strict` on application packages |
| `make test` | `pytest` with coverage (excludes integration) |
| `make test-all` | full suite incl. integration markers |
| `make check` | lint + typecheck + test (the CI gate) |
| `make hooks` | install pre-commit hooks |

Run `make check` before every push; it mirrors the CI pipeline exactly.

### Test markers

- `unit` — pure, no I/O, no containers (default in CI).
- `integration` — needs Postgres/Redis. Run with `make test-all`.
- `contract` — tests against a `Protocol` surface.
- `slow` — long-running.

## 6. Runtime state

The build/operational state lives in `SYSTEM_STATE.json` and is managed exclusively by
`runtime/state.py`:

```python
from runtime.state import RuntimeStateStore

store = RuntimeStateStore()
store.update(lambda s: s.mark_completed(19).transition("PROVIDERS"))
```

Writes are atomic and sorted, so the file diffs cleanly in review.

## 7. Logging & observability

- Use the structured logger; never `print`. Always carry a `correlation_id`.
- Add a span per state transition and per provider call.
- Metric names are `hookclose_<subsystem>_<name>`.

See [docs/observability.md](docs/observability.md).

## 8. Releases

1. Ensure `make check` is green on `main`.
2. Tag with SemVer: `git tag v0.2.0 && git push --tags`.
3. The release workflow builds artifacts and publishes the release.

Version bump rules follow Conventional Commits (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## 9. Deployment note

**Do not deploy to a VPS until the runtime core is stable locally** — queues, workers,
provider routing, retry loops, and task chaining all verified. VPS deployment is the
final phase, not a parallel track.
