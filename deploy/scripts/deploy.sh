#!/usr/bin/env bash
# Deploy / redeploy the production stack. Records the deployed commit so rollback
# can return to the previous good revision. Run from the repo root on the server.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
COMPOSE=(docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml)
STATE_DIR="${HOOKCLOSE_STATE_DIR:-/opt/hookclose/.deploy}"
mkdir -p "${STATE_DIR}"

[[ -f deploy/.env.prod ]] || { echo "missing deploy/.env.prod"; exit 1; }
[[ -f deploy/nginx/certs/fullchain.pem ]] || echo "WARN: no TLS cert at deploy/nginx/certs/ (HTTPS will fail)"

# Remember the currently-deployed commit before moving.
if [[ -f "${STATE_DIR}/current" ]]; then
  cp "${STATE_DIR}/current" "${STATE_DIR}/previous"
fi
git rev-parse HEAD > "${STATE_DIR}/current"

echo "[deploy] building + starting stack at $(git rev-parse --short HEAD)..."
"${COMPOSE[@]}" up -d --build --remove-orphans
"${COMPOSE[@]}" ps

echo "[deploy] waiting for health..."
deploy/scripts/healthcheck.sh
echo "[deploy] OK — deployed $(git rev-parse --short HEAD)"
