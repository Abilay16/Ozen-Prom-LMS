#!/usr/bin/env bash
#
# Backs up the production PostgreSQL database to ./backups/, rotating out
# anything older than $RETENTION_DAYS. Meant to be run from the repo root
# on the server (where docker-compose.prod.yml and .env live), via cron.
#
# One-time setup on the server:
#   chmod +x scripts/backup_db.sh
#   crontab -e
#   # add (daily at 03:00 server time):
#   0 3 * * * cd /opt/ozen-lms && ./scripts/backup_db.sh >> /var/log/ozen_lms_backup.log 2>&1
#
# Restore from a backup (destructive — overwrites the current DB):
#   gunzip -c backups/ozen_lms_2026-09-02_030000.dump.gz | \
#     docker exec -i ozen_lms_db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

RETENTION_DAYS="${RETENTION_DAYS:-14}"
BACKUP_DIR="$REPO_ROOT/backups"
CONTAINER_NAME="${DB_CONTAINER_NAME:-ozen_lms_db}"

# Load POSTGRES_USER / POSTGRES_DB from .env
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER not set — check .env}"
POSTGRES_DB="${POSTGRES_DB:?POSTGRES_DB not set — check .env}"

mkdir -p "$BACKUP_DIR"

timestamp="$(date +%Y-%m-%d_%H%M%S)"
out_file="$BACKUP_DIR/ozen_lms_${timestamp}.dump.gz"

echo "[$(date)] Starting backup of ${POSTGRES_DB} -> ${out_file}"

# -Fc = custom format (compressed, supports pg_restore --clean/--if-exists,
# selective table restore, etc.) — piped through gzip for extra shrinkage.
docker exec "$CONTAINER_NAME" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
  | gzip > "$out_file"

size="$(du -h "$out_file" | cut -f1)"
echo "[$(date)] Backup complete: ${out_file} (${size})"

# Rotate old backups
find "$BACKUP_DIR" -name 'ozen_lms_*.dump.gz' -mtime "+${RETENTION_DAYS}" -print -delete

echo "[$(date)] Done. Backups older than ${RETENTION_DAYS} days removed."
