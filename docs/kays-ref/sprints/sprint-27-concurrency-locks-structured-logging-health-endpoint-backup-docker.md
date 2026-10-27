# Sprint 27 — DB-Level Concurrency Locks, Structured JSON Logging, Health Endpoint, Docker, and S3 Backup

**Theme:** Production hardening: prevent double-bookings and double-payments via advisory locks,
replace ad-hoc console calls with structured JSON logging, add /api/health endpoint, containerize
with multi-stage Dockerfile, and implement automated S3 backup/restore.

## Pillars

### 1. DB-Level Concurrency Locks (SELECT FOR UPDATE)
- `src/lib/db.server.ts` — `getConcurrentLock(key)` / `releaseConcurrentLock(key)` using
  `pg_try_advisory_lock(hashtext(...))` with auto-expiry via setTimeout. Added `slot_reservations`
  table to `ensureSchema` for timed slot holds.
- `src/lib/api/scheduling.server.ts` — `bookSlot` acquires advisory lock on
  `slot:{orgId}:{timestamp}`, queries with `SELECT ... FOR UPDATE` to detect existing bookings,
  then atomically updates the lead. `reserveSlot` uses same lock pattern, inserts into
  `slot_reservations` with configurable TTL (30–600s).
- `src/lib/api/billing.server.ts` — `generateInvoice` locks on `invoice_seq:{orgId}` to prevent
  duplicate invoice numbers. `recordPayment` locks on `payment:{orgId}:{invoiceId}`,
  reads the invoice with `FOR UPDATE`, and rejects payments on already-paid invoices.

### 2. Structured JSON Logger
- `src/lib/logger.server.ts` — Production output writes a JSON envelope:
  `{ timestamp, level, message, traceId, orgId, userId, executionTimeMs, event, meta }`.
  Dev output shows coloured prefix with `[trace:xxx]` / `[org:xxx]`. Added `startTimer()` helper,
  `LOCK_ACQUIRED` / `LOCK_FAILED` events. `createLogger` now accepts optional `user_id`.
- `src/server.ts` — Replaced `console.error` calls with `logger.error`.
- `src/routes/__root.tsx` — ErrorComponent uses `logger.error` instead of `console.error`;
  imports `logger` and `startTimer`.

### 3. Health Endpoint
- `src/routes/api/health.ts` — `GET /api/health` returns:
  `{ status, dbAvailable, dbError, queueStatus, timestamp, uptime }`.
  Returns HTTP 503 when DB is unavailable.

### 4. Dockerfile & Containerization
- `Dockerfile` — Multi-stage: `node:22-alpine` build → `node:22-alpine` run.
  HEALTHCHECK hits `http://localhost:3000/api/health` every 30s. Runs as non-root `appuser`.
- `.dockerignore` — Excludes node_modules, .git, tests, etc.

### 5. Automated S3 Backup & Restore
- `scripts/backup-db.sh` — `pg_dump` → GPG AES256 encrypt → `aws s3 cp` into
  `s3://{bucket}/org={slug}/backup-{timestamp}.sql.gpg`. Supports single-org or full backup.
- `src/scripts/db-restore-test.ts` — Downloads encrypted dump from S3, decrypts, spins up
  ephemeral Postgres via Docker (port 25432), restores, runs integrity checks
  (table count, lead count, org count, invoice/payment counts), then tears down.
- `package.json` — Added `db:backup` and `db:restore-test` scripts.

## File Changes

| File | Change |
|------|--------|
| `src/lib/db.server.ts` | **Updated** — Added `getConcurrentLock`, `releaseConcurrentLock`, `slot_reservations` table |
| `src/lib/api/scheduling.server.ts` | **Updated** — Added `bookSlot`, `reserveSlot` with advisory locks + FOR UPDATE |
| `src/lib/api/billing.server.ts` | **Updated** — `generateInvoice` and `recordPayment` wrapped in advisory locks; FOR UPDATE on invoice row |
| `src/lib/logger.server.ts` | **Updated** — JSON envelope format with traceId/orgId/userId/executionTimeMs; startTimer(), new EVENTS |
| `src/server.ts` | **Updated** — `console.error` replaced with `logger.error` |
| `src/routes/__root.tsx` | **Updated** — ErrorComponent uses `logger.error` instead of `console.error` |
| `src/routes/api/health.ts` | **New** — GET /api/health returning structured health payload |
| `Dockerfile` | **New** — Multi-stage Alpine build + HEALTHCHECK |
| `.dockerignore` | **New** — Standard exclusions |
| `scripts/backup-db.sh` | **New** — pg_dump → encrypt → S3 upload |
| `src/scripts/db-restore-test.ts` | **New** — Ephemeral PG restore + integrity checks |
| `package.json` | **Updated** — Added `db:backup`, `db:restore-test` scripts |
| `src/__tests__/concurrency.test.ts` | **New** — 6 tests for lock helper + bookSlot/reserveSlot lock lifecycle |
| `src/__tests__/structured-logger.test.ts` | **New** — 7 tests for logger envelope, production JSON, EVENTS |
| `src/__tests__/health-endpoint.test.ts` | **New** — 4 tests for health response shape |
| `src/__tests__/billing-locks.test.ts` | **New** — 5 tests for lock failure/acquire/already-paid |
| `src/__tests__/billing.test.ts` | **Updated** — Mocks updated for new lock calls |

## Results
- **250 tests** passing (up from 228, +22 new tests)
- **34 test files** passing (up from 30)
- Build: zero errors (only pre-existing `use client` warnings from deps)
