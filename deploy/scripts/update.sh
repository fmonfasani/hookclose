#!/usr/bin/env bash
# Pull the latest main and redeploy. The default update path for routine releases.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
BRANCH="${HOOKCLOSE_BRANCH:-main}"

echo "[update] fetching origin/${BRANCH}..."
git fetch --prune origin "${BRANCH}"
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

exec deploy/scripts/deploy.sh
