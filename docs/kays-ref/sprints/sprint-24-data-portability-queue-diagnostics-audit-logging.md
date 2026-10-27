# Sprint 24 — Data Portability, Queue Diagnostics Console, and Immutable Audit Logging

**Theme:** CSV data export engine, real-time queue telemetry with force-retry, and an immutable AuditLog schema with interceptor-based recording on every lead/invoice/payment mutation.

## Pillars

### 1. Data Portability — CSV Export Engine
- `src/lib/exports.server.ts` — `generateExport` (`createServerFn`) supporting 4 datasets: `leads`, `invoices`, `interactions`, `audit_logs`.
- Each dataset maps to a named query function with column projection and optional `startDate`/`endDate` filtering.
- Returns CSV string + auto-named file (`kwc-{dataset}-{date}.csv`). Automatically records a `DATA_EXPORT` audit entry on success.
- `/admin/settings/data` — radio-button dataset selector, two date inputs, "Download CSV" button; client-side blob download after server response.

### 2. Queue Diagnostics Console
- `getQueueTelemetry` — aggregate counts by status (pending/dispatched/failed/stalled), returns `QueueTelemetry` struct.
- `forceRetryQueueItems` — `UPDATE ... FOR UPDATE SKIP LOCKED` resets failed/stalled items to pending with zero retry count (capped at 100).
- `getFailedQueueItems` — last 50 failed/stalled items with error details.
- `/admin/system/diagnostics` — stat boxes, stalled-count indicator, "Force Retry" button, live item list; auto-refresh every 15 s.

### 3. Immutable Audit Logging
- `src/lib/audit.server.ts` — `AuditLog` schema, `recordAudit`, `queryAuditLogs`.
- `audit_logs` table in `ensureSchema` with indexes on `(tenant_id, created_at DESC)` and `(tenant_id, action_type)`.
- Audit interceptors:
  - `updateLead` — logs `PATIENT_TRIAGED` on status change; logs `CONFIG_CHANGED` on triage action.
  - `deleteLead` — logs `RECORD_DELETED`.
  - `generateInvoice` — logs `INVOICE_UPDATED`.
- All interceptors use `getSession()` for userId when available; `recordAudit` silently no-ops when DB is unavailable.

## File Changes

| File | Change |
|------|--------|
| `src/lib/audit.server.ts` | **New** — AuditLog schema, recordAudit, queryAuditLogs, ensureAuditSchema |
| `src/lib/exports.server.ts` | **New** — CSV generation engine, generateExport createServerFn |
| `src/lib/api/diagnostics.server.ts` | **Updated** — getQueueTelemetry, forceRetryQueueItems, getFailedQueueItems |
| `src/routes/admin/settings/data.tsx` | **New** — Data export UI |
| `src/routes/admin/system/diagnostics.tsx` | **New** — Queue diagnostics UI |
| `src/lib/db.server.ts` | **Updated** — audit_logs table in ensureSchema |
| `src/lib/logger.server.ts` | **Updated** — AUDIT_LOG_CREATED, AUDIT_LOG_FAILED, DATA_EXPORT events |
| `src/lib/api/leads.server.ts` | **Updated** — Audit interceptors on updateLead/deleteLead |
| `src/lib/api/billing.server.ts` | **Updated** — Audit interceptor on generateInvoice |
| `src/routeTree.gen.ts` | **Updated** — Two new routes registered |
| `src/__tests__/audit.test.ts` | **New** — 7 tests for audit schema, recordAudit, queryAuditLogs |
| `src/__tests__/exports.test.ts` | **New** — 16 tests for exportSchema, toCsvValue, rowsToCsv |
| `src/__tests__/queue-diagnostics.test.ts` | **New** — 7 tests for telemetry shape, retry result shape, failed items shape |

## Results
- **148 tests** passing (up from 118)
- **21 test files** passing
- Build: zero warnings/errors
