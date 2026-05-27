#!/usr/bin/env bash
# Watchdog: poll every service's health until healthy or timeout. Used by deploy.sh
# and runnable standalone (e.g. from a cron/monit watchdog).
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
COMPOSE=(docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml)
TIMEOUT="${HOOKCLOSE_HEALTH_TIMEOUT:-120}"
SERVICES=(postgres redis scheduler workflow-engine opencode-worker nginx)

deadline=$(( $(date +%s) + TIMEOUT ))
while :; do
  unhealthy=()
  for svc in "${SERVICES[@]}"; do
    cid="$("${COMPOSE[@]}" ps -q "${svc}" 2>/dev/null || true)"
    if [[ -z "${cid}" ]]; then unhealthy+=("${svc}:absent"); continue; fi
    status="$(docker inspect -f '{{ if .State.Health }}{{ .State.Health.Status }}{{ else }}{{ .State.Status }}{{ end }}' "${cid}")"
    [[ "${status}" == "healthy" || "${status}" == "running" ]] || unhealthy+=("${svc}:${status}")
  done
  if [[ ${#unhealthy[@]} -eq 0 ]]; then echo "[health] all services healthy"; exit 0; fi
  if [[ $(date +%s) -ge ${deadline} ]]; then
    echo "[health] TIMEOUT — unhealthy: ${unhealthy[*]}"; exit 1
  fi
  sleep 5
done
