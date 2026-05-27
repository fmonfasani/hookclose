# CI/CD

The pipeline guarantees **reproducible, deterministic builds** and **runtime
stability**. All gates are mirrored locally by `make check`, so failures surface
before push.

## Pipeline ([.github/workflows/ci.yml](../.github/workflows/ci.yml))

Runs on every push to `main`/`master`, every PR, and manual dispatch.

| Job | What it enforces | Required gate |
| --- | --- | --- |
| `lint` | `ruff check` + `ruff format --check` (incl. bandit `S` rules) | ✅ |
| `typecheck` | `mypy --strict` over all 14 importable packages | ✅ |
| `test` | `pytest` (unit) + coverage, **`--cov-fail-under=70`** (currently ~74%) | ✅ |
| `smoke` | import surface + in-process end-to-end ([tests/test_smoke.py](../tests/test_smoke.py)) | ✅ |
| `security` | `pip-audit` dependency scan | advisory (non-blocking) |
| `docker-build` | builds every `docker/*/Dockerfile` (no push) | advisory |
| `ci-ok` | aggregate status — green only if all required jobs pass | ✅ |

`security` and `docker-build` are intentionally **advisory**: a new upstream CVE or a
registry hiccup must not block an unrelated PR. They are surfaced for triage, not used
as a merge gate.

### Determinism

- Concurrency cancels superseded runs; pip is cached by Python version.
- `ruff format --check` + pinned `.gitattributes` (LF) keep formatting identical across
  OSes, so the format gate is reproducible.
- The `smoke` job asserts the full runtime wires together (providers → routing →
  manager → chaining → self-healing) with no network or containers.

## Branch protection (recommended)

On GitHub: **Settings → Branches → add rule** for `main`:

- ✅ Require a pull request before merging (≥1 approval).
- ✅ Require status checks to pass → select **`CI passed`** (the `ci-ok` job). One check
  covers lint + typecheck + test + smoke.
- ✅ Require branches to be up to date before merging.
- ✅ Require conversation resolution.
- ✅ Do not allow force pushes / deletions.
- (Optional) Require signed commits.

## Semantic versioning

[SemVer](https://semver.org/): `vMAJOR.MINOR.PATCH`. Per
[CONTRIBUTING.md](../CONTRIBUTING.md), Conventional Commit types map to bumps:
`fix:` → patch, `feat:` → minor, `feat!:` / `BREAKING CHANGE:` → major.

## Releases ([.github/workflows/release.yml](../.github/workflows/release.yml))

```bash
# from a green main
git tag v0.2.0
git push origin v0.2.0
```

The release workflow then:

1. re-runs the full quality gate (releases are deterministic — never release red),
2. builds sdist + wheel (`python -m build`) and validates them (`twine check`),
3. creates a GitHub Release with auto-generated notes and attaches the artifacts.
