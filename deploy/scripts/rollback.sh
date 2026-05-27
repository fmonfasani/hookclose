#!/usr/bin/env bash
# Roll back to the previously deployed commit (recorded by deploy.sh), or to an
# explicit ref:  deploy/scripts/rollback.sh [git-ref]
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
STATE_DIR="${HOOKCLOSE_STATE_DIR:-/opt/hookclose/.deploy}"

TARGET="${1:-}"
if [[ -z "${TARGET}" ]]; then
  [[ -f "${STATE_DIR}/previous" ]] || { echo "no previous deployment recorded; pass a git ref"; exit 1; }
  TARGET="$(cat "${STATE_DIR}/previous")"
fi

echo "[rollback] checking out ${TARGET}..."
git checkout --detach "${TARGET}"
exec deploy/scripts/deploy.sh
