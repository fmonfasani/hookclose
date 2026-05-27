#!/usr/bin/env bash
# Back up PostgreSQL (pg_dump) and the Redis AOF, with retention pruning.
# Schedule via cron, e.g. (daily 03:00):
#   0 3 * * * cd /opt/hookclose && deploy/scripts/backup.sh >> /var/log/hookclose-backup.log 2>&1
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
# shellcheck disable=SC1091
set -a; [[ -f deploy/.env.prod ]] && . deploy/.env.prod; set +a

BACKUP_DIR="${HOOKCLOSE_BACKUP_DIR:-/opt/hookclose/backups}"
RETENTION="${HOOKCLOSE_BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${BACKUP_DIR}"

echo "[backup] postgres -> ${BACKUP_DIR}/pg-${STAMP}.sql.gz"
docker exec hookclose-postgres pg_dump -U "${HOOKCLOSE_POSTGRES_USER:-hookclose}" \
  "${HOOKCLOSE_POSTGRES_DB:-hookclose}" | gzip > "${BACKUP_DIR}/pg-${STAMP}.sql.gz"

echo "[backup] redis AOF snapshot"
docker exec hookclose-redis redis-cli BGREWRITEAOF >/dev/null || true
docker cp hookclose-redis:/data "${BACKUP_DIR}/redis-${STAMP}" 2>/dev/null || true

echo "[backup] pruning backups older than ${RETENTION} days"
find "${BACKUP_DIR}" -maxdepth 1 -mtime "+${RETENTION}" -name 'pg-*.sql.gz' -delete || true
find "${BACKUP_DIR}" -maxdepth 1 -mtime "+${RETENTION}" -type d -name 'redis-*' -exec rm -rf {} + || true
echo "[backup] done"
