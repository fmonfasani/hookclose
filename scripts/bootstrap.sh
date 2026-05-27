#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[hookclose] checking prerequisites..."
for bin in python3 docker; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "[hookclose] missing dependency: $bin" >&2
    exit 1
  fi
done

if [[ ! -f .env ]]; then
  echo "[hookclose] creating .env from .env.example"
  cp .env.example .env
fi

echo "[hookclose] starting data services..."
docker compose up -d postgres redis

echo "[hookclose] waiting for postgres..."
sleep 10

echo "[hookclose] initializing database..."
python3 scripts/init_db.py

echo "[hookclose] starting runtime services..."
docker compose up -d scheduler workflow-engine opencode-worker

echo "[hookclose] runtime status..."
docker compose ps

echo "[hookclose] HookClose Runtime Started."
