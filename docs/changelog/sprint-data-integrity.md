# Sprint: Data Integrity Triad

**Version**: 5.9.3
**Date**: 2026-07-26
**Theme**: Production error visibility → conflict detection → atomic writes

## Layer 1 — Production Error Visibility

### Changes
- `src/lib/logger.ts`: wired `logger.error()` → `captureError()` (Sentry). Every repository failure, sync failure, and store error now reaches Sentry in production. Previously errors were silently discarded (`// Production error tracking integration point:` was a comment).
- `src/lib/store.ts`: `addTransaction`, `updateTransaction`, `deleteTransaction` now check `Result<T,E>` return values and call `captureError` on failures. Before: all three discarded the Result.
- `src/components/SyncDot.tsx`: completely rewritten. Now polls both `getPendingCount()` and `getDeadLetterCount()`, shows a numbered badge on the dot, and displays a tap-to-open detail panel with pending/failed/conflict counts and status messages. Supports Kiswahili/English via `useTranslation`.
- `src/i18n/{sw,en}.json`: added 9 new keys for sync health messages (`sync_status`, `sync_pending`, `sync_failed`, `sync_healthy`, `sync_offline`, `sync_online`, `pending_sync`, `sync_dead_letter_tip`).
- `src/screens/DashboardScreen.test.tsx`: fixed stale mock path (`../features/sync/SyncDot` → `../components/SyncDot`).

### Files Changed
- `src/lib/logger.ts` — Sentry integration
- `src/lib/store.ts` — Result checking
- `src/components/SyncDot.tsx` — rewrite with dead-letter/conflict visibility
- `src/i18n/sw.json` — 9 new keys
- `src/i18n/en.json` — 9 new keys
- `src/test/mocks.ts` — added `transaction` mock

### Tests: 23 store tests pass, 33 logger/sentry tests pass

---

## Layer 2 — Optimistic Concurrency Control

### Changes
- `src/features/sync/syncQueue.ts`: added `detectConflict()` function. Before every upsert, SELECTs the remote record's `updated_at` and compares it with the `_expected_updated_at` stored in the queue payload. If mismatch → moves to dead-letter with `_conflict_reason: 'updated_at_mismatch'`. Falls back gracefully if the remote query fails or `updated_at` isn't set.
- `src/lib/store.ts`: `updateTransaction` now includes `_expected_updated_at` in queue payload (the `updated_at` from before the edit). `addTransaction` includes `updated_at` in the payload (was missing before — a bug).
- `src/features/sync/syncQueue.ts`: added `getConflictCount()` — counts dead-letter items with `_conflict_reason` in payload.
- `src/components/SyncDot.tsx`: shows conflict count in detail panel with warning message.

### Conflict Detection Flow
1. User edits transaction → store sets `_expected_updated_at: tx.updated_at` (the version before edit)
2. Queue item created with both `updated_at` (new) and `_expected_updated_at` (old)
3. On flush → `detectConflict()` SELECTs remote record's `updated_at`
4. If remote `updated_at` === `_expected_updated_at` → OK, proceed with upsert
5. If mismatch → another device wrote first → dead-letter with conflict tag
6. SyncDot shows "Conflicts: N" with warning banner

### Backward Compat
- No Supabase schema changes required — uses existing `updated_at` column
- If `_expected_updated_at` is undefined (new records / legacy data), conflict check is skipped
- If SELECT fails (e.g., table doesn't exist), falls back to regular upsert

### Files Changed
- `src/features/sync/syncQueue.ts` — `detectConflict()`, `getConflictCount()`
- `src/lib/store.ts` — `_expected_updated_at` + `updated_at` in payload
- `src/components/SyncDot.tsx` — conflict display

### Tests: 336 pass

---

## Layer 3 — Atomic Sync Queue

### Changes
- `src/lib/store.ts`: all three CRUD methods (`addTransaction`, `updateTransaction`, `deleteTransaction`) now wrap Dexie write + queue enqueue in `db.transaction('rw', db.transactions, db.sync_queue, ...)`. If either operation fails, both roll back — eliminates silent data loss from a crash between the two writes.
- `src/features/sync/syncQueue.ts`: `flushQueue()` now has a promise-based mutex (`flushLock`). Concurrent flushes are serialized — only one runs at a time. Subsequent callers await the in-progress lock.
- `src/test/mocks.ts`: added `transaction` mock to `mockDb` (calls the callback directly).

### Atomic Write Guarantee
Before: `saveTransaction(tx)` → ✅ | `addToQueue(...)` → 💥 crash → data in Dexie but never syncs
After: `db.transaction(rw, transactions, sync_queue, () => { saveTransaction(); addToQueue(); })` → both succeed or both roll back

### Files Changed
- `src/lib/store.ts` — `db.transaction()` wrappers
- `src/features/sync/syncQueue.ts` — `flushLock` mutex
- `src/test/mocks.ts` — `transaction` mock

### Tests: 336 pass

---

## Summary

| Metric | Before | After |
|---|---|---|
| Production errors visible? | No (comment placeholder) | Yes (Sentry for every logger.error) |
| CRUD Result values checked? | No (all discarded) | Yes (captureError on failure) |
| Sync health visible? | Green/amber dot only | Badge count + detail panel |
| Conflict detection? | None (last-write-wins silently) | `updated_at` comparison + dead-letter |
| Write atomicity? | No (crash → data in Dexie, not in queue) | Yes (Dexie transaction) |
| Concurrent flush protection? | None (dual paths fight) | Mutex (serialized) |
| Tests passing | 336 | 336 |
