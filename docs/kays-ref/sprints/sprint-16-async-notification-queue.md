# Sprint 16 — Async Notification Queue

## Objective
Decouple external notification dispatch (SMS/WhatsApp) from the lead submission request/response lifecycle by building a fault-tolerant Postgres-backed task queue with idempotency guarantees and exponential backoff retries.

## Deliverables

### 1. Notification Queue Table (`notification_queue`)
- Added to `ensureSchema()` in `db.server.ts` under the multi-tenant block.
- Columns: `id`, `tenant_id`, `lead_id`, `event_type`, `idempotency_key` (UNIQUE), `payload_json`, `status`, `retry_count`, `max_retries`, `next_retry_at`, `last_error`, `created_at`, `processed_at`.
- Composite index on `(status, next_retry_at)` for efficient polling.

### 2. Queue Engine (`src/lib/queue.server.ts`)
- **`ensureQueueSchema()`** — idempotent table/index creation (defensive; schema also created in `ensureSchema`).
- **`enqueueNotification({ orgId, leadId, eventType, payload? })`** — SHA-256 idempotency key from `(orgId, leadId, eventType)`; returns `"queued"` or `"already_pending"` on duplicate.
- **`dispatchNotification()`** — placeholder that logs `NOTIFICATION_DISPATCHED`; intended to be replaced with real Twilio / Africa's Talking gateway.
- **`processQueue({ batchSize?, dispatch? })`** — reads pending rows (`FOR UPDATE SKIP LOCKED`), invokes dispatch, handles failures with exponential backoff (1000ms × 2^retry_count, capped at 3 retries), marks `"failed"` when exhausted.
- **`processNotifications()`** — top-level wrapper that catches errors and returns `{ processed, failed }`.

### 3. Server Function API (`src/lib/api/notifications.server.ts`)
- **`triggerQueueProcessing`** — `createServerFn({ method: "POST" })` for client-side polling.

### 4. Lead Submission Integration (`src/lib/api/leads.server.ts`)
- `submitLead` now calls `enqueueNotification({ orgId, leadId, eventType: "lead_created", payload })` after successful INSERT. Failure to enqueue logs `QUEUE_SYNC_FAILURE` but does not block the response.

### 5. Logger Events (`src/lib/logger.server.ts`)
- Added: `NOTIFICATION_ENQUEUED`, `NOTIFICATION_DISPATCHED`, `NOTIFICATION_FAILED`, `NOTIFICATION_RETRY`, `NOTIFICATION_IDEMPOTENCY_SKIP`.

### 6. Environment Configuration (`src/lib/env.server.ts`)
- Added: `MAX_QUEUE_RETRIES` (default 3), `QUEUE_POLL_INTERVAL_MS` (default 5000).

### 7. Module Changes Summary

| File | Change |
|---|---|
| `src/lib/db.server.ts` | Added `notification_queue` table + index to `ensureSchema()` |
| `src/lib/queue.server.ts` | **New** — Full queue engine (enqueue, process, dispatch, retry) |
| `src/lib/api/notifications.server.ts` | **New** — `triggerQueueProcessing` server fn |
| `src/lib/logger.server.ts` | Added 5 notification event constants |
| `src/lib/env.server.ts` | Added `MAX_QUEUE_RETRIES`, `QUEUE_POLL_INTERVAL_MS` |
| `src/lib/api/leads.server.ts` | Enqueue notification on lead creation |
| `src/__tests__/notification-queue.test.ts` | **New** — 8 tests covering enqueue, idempotency, dispatch, retries, max retries |

### 8. Test Results
- 34 tests pass (26 existing + 8 new).
- Build succeeds cleanly (client + SSR + Nitro/Vercel).

## Key Design Decisions
- **Postgres polling, not message broker** — No additional infrastructure; works with existing `postgres` client. `FOR UPDATE SKIP LOCKED` prevents worker contention.
- **Idempotency via content-addressed key** — SHA-256 of `(tenantId, leadId, eventType)` prevents double-enqueue from network retries or duplicate submissions.
- **Injected dispatch** — `processQueue` accepts an optional `dispatch` parameter, defaulting to `dispatchNotification`. Tests inject a mock; production can swap in a real gateway.
- **Fire-and-forget enqueue** — `submitLead` does not `await` the notification; failure is logged but the lead response is unaffected.
- **No `createServerFn` in queue module** — `queue.server.ts` exports pure server-side functions; `notifications.server.ts` wraps `processNotifications` in a server fn for client access.

## Retrospective

### What went well
- Mock-based testing worked reliably — the dependency-injected `dispatch` parameter made the retry logic straightforward to test without a real Postgres instance.
- Adding the table to existing `ensureSchema()` kept schema management in one place.
- The idempotency key pattern required no schema migrations after initial creation.

### What could be improved
- `processQueue` uses `Date.now()` for `next_retry_at` — should use database-side `NOW()` for clock consistency across workers.
- Missing a `/admin/queue` UI route for monitoring pending/failed notifications.
- Exponential backoff delays are short (1s/2s/4s) — suitable for internal retries but could be longer for third-party API rate limits.

## Known Issues
- No real SMS/WhatsApp provider wired yet — `dispatchNotification` is a no-op that logs `NOTIFICATION_DISPATCHED`.
- `processQueue` is synchronous within a single request — long queue depth could block the response. In production, this should be invoked from a cron job or edge function.
