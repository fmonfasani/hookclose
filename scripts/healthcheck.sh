#!/usr/bin/env bash
set -euo pipefail

probe() {
  local name=$1
  local url=$2
  echo -n "[hookclose] $name ... "
  if curl -fsS --max-time 5 "$url" >/dev/null; then
    echo "ok"
  else
    echo "FAIL"
    exit 1
  fi
}

probe "scheduler"      "http://localhost:8100/health"
probe "workflow-engine" "http://localhost:8101/health"
probe "opencode-worker" "http://localhost:8102/health"
echo "[hookclose] all services healthy"
