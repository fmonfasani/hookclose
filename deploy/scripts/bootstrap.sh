#!/usr/bin/env bash
# Provision a fresh Hetzner Ubuntu 24.04 box for the HookClose runtime.
# Idempotent: safe to re-run. Run as root (or with sudo).
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hookclose}"
REPO_URL="${REPO_URL:-https://github.com/fmonfasani/hookclose.git}"

echo "[bootstrap] updating apt + installing prerequisites..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl git ufw

if ! command -v docker >/dev/null 2>&1; then
  echo "[bootstrap] installing Docker Engine + compose plugin..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
fi

echo "[bootstrap] firewall: allow ssh + http + https only..."
ufw allow OpenSSH || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
ufw --force enable || true

echo "[bootstrap] fetching app into ${APP_DIR}..."
if [[ -d "${APP_DIR}/.git" ]]; then
  git -C "${APP_DIR}" pull --ff-only
else
  git clone "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"
if [[ ! -f deploy/.env.prod ]]; then
  cp deploy/.env.prod.example deploy/.env.prod
  echo "[bootstrap] created deploy/.env.prod — EDIT IT (set passwords + API keys) before deploying."
fi

echo "[bootstrap] done. Next: edit deploy/.env.prod, add TLS certs to deploy/nginx/certs/, then run deploy/scripts/deploy.sh"
