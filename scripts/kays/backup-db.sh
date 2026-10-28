#!/usr/bin/env bash
set -euo pipefail

# Required env vars: DATABASE_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
# Optional: S3_BUCKET (default: kwc-db-backups), ENCRYPTION_PASSPHRASE (default: auto-generated)
# Usage: ./scripts/backup-db.sh [org-slug]

ORG_SLUG="${1:-all}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DUMP_FILE="/tmp/kwc-dump-${ORG_SLUG}-${TIMESTAMP}.sql"
ENCRYPTED_FILE="${DUMP_FILE}.gpg"
S3_BUCKET="${S3_BUCKET:-kwc-db-backups}"
S3_KEY="org=${ORG_SLUG}/backup-${TIMESTAMP}.sql.gpg"

echo "[backup-db] Starting backup for org=${ORG_SLUG} at ${TIMESTAMP}"

# 1. Dump
if [ "${ORG_SLUG}" = "all" ]; then
  pg_dump "${DATABASE_URL}" --no-owner --no-acl -f "${DUMP_FILE}"
else
  pg_dump "${DATABASE_URL}" --no-owner --no-acl --schema="${ORG_SLUG}" -f "${DUMP_FILE}"
fi
echo "[backup-db] Dump size: $(wc -c < "${DUMP_FILE}") bytes"

# 2. Encrypt
PASSPHRASE="${ENCRYPTION_PASSPHRASE:-$(openssl rand -base64 32)}"
echo "${PASSPHRASE}" | gpg --batch --yes --passphrase-fd 0 \
  --symmetric --cipher-algo AES256 \
  -o "${ENCRYPTED_FILE}" "${DUMP_FILE}"
rm -f "${DUMP_FILE}"
echo "[backup-db] Encrypted to ${ENCRYPTED_FILE}"

# 3. Upload to S3
aws s3 cp "${ENCRYPTED_FILE}" "s3://${S3_BUCKET}/${S3_KEY}" --no-progress
rm -f "${ENCRYPTED_FILE}"
echo "[backup-db] Uploaded to s3://${S3_BUCKET}/${S3_KEY}"

# 4. Store passphrase if not custom (requires VAULT env var or prints warning)
if [ -z "${ENCRYPTION_PASSPHRASE:-}" ]; then
  echo "[backup-db] WARNING: Auto-generated passphrase = ${PASSPHRASE}"
  echo "[backup-db] Store this passphrase securely! Without it the backup cannot be restored."
fi

echo "[backup-db] Backup complete"
