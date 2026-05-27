#!/usr/bin/env bash
# Quick-iteration loop: hot-reload API + worker + lint on save.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ ! -d .venv ]]; then
  echo "run scripts/bootstrap.sh first" >&2
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

exec uvicorn runtime.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000
