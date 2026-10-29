# Sprint: Hardening Phase Four — Test Coverage, Type Safety, Architecture, Bundle

**Version:** 5.5.0 → 5.6.0  
**Date:** 2026-07-22  
**Theme:** Eliminate all typecheck errors, add missing test coverage, fix architectural violations, optimize bundle

---

## Layer 1 — Fix Failing Tests + Typecheck Errors (Risk: 3 pre-existing typecheck errors)

**3 typecheck errors fixed:**

| File | Error | Fix |
|------|-------|-----|
| `RecordSale.test.tsx` | `waitFor` imported but unused | Removed unused import |
| `RecordSale.test.tsx` | `addTransaction` not in store mock type | Moved `addTransaction` into initial `storeState` object |
| `syncQueue.test.ts` | `Property 'mock' does not exist` on `db.sync_queue.add` | Refactored imports to use `any`-typed helper functions (`importDb()`, `importSupabase()`, `importSyncQueue()`) |

**Result:** `npm run typecheck` → EXIT 0 (zero errors, down from 3).

---

## Layer 2 — Integration Tests for Write Paths (Risk: 0 tests for pushNotifications, 3 untested repository functions)

### New repository tests (+6 tests)
| Function | Tests | What's covered |
|----------|-------|----------------|
| `updateCustomer()` | 2 | Success path, Dexie failure |
| `upsertPushSubscription()` | 2 | Supabase upsert success, Supabase error |
| `deletePushSubscription()` | 2 | Supabase delete success, Supabase error |

### New pushNotifications tests (+11 tests)
| Function | Tests | What's covered |
|----------|-------|----------------|
| `requestNotificationPermission()` | 3 | No API, granted, denied |
| `subscribeToPush()` | 5 | No serviceWorker, no PushManager, existing subscription, no VAPID key, error handling |
| `unsubscribeFromPush()` | 3 | No serviceWorker, no subscription, error handling |

---

## Layer 3 — Pure Function Test Coverage (Risk: csv, whatsapp, print untested)

### New csv tests (+7 tests)
| Function | Tests | What's covered |
|----------|-------|----------------|
| `transactionsToCSV()` | 7 | Empty array, single row, comma escaping, double-quote escaping, date/time extraction, optional fields present/absent |

### New whatsapp tests (+7 tests)
| Function | Tests | What's covered |
|----------|-------|----------------|
| `formatReceiptText()` | 4 | Income with description, expense, withdrawal, no description |
| `formatDailySummaryText()` | 1 | Full summary with all fields |
| `shareViaWhatsApp()` | 2 | No phone number, with phone number |

---

## Layer 4 — Architectural Violations Fixed

### Money safety (3 violations in PosScreen.tsx)
| Line | Before | After |
|------|--------|-------|
| 54 | `cart.reduce((s, i) => s + i.price * i.qty, 0)` | `cents(cart.reduce((s, i) => s + cents(i.price * i.qty), 0))` |
| 132 | `price: i.price * i.qty` | `price: cents(i.price * i.qty)` |
| 259 | `(item.price * item.qty).toLocaleString(...)` | `cents(item.price * item.qty).toLocaleString(...)` |

### setState-during-render (RecordSale.tsx)
- **Before:** `if (!paymentMethod && userPaymentMethods.length === 1) { setPaymentMethod(...) }` called during render body
- **After:** Wrapped in `useEffect` with proper dependency array

---

## Layer 5 — Bundle Optimization

### recharts vendor chunk
- Added `recharts` + `d3-*` to `manualChunks` as `vendor-charts`
- recharts is now independently cacheable (372 KB, loaded lazily)

### AddScreen useMemo
- Wrapped inline `cards` array in `useMemo` to prevent unnecessary re-creation on every render

---

## Layer 6 — Sync Architecture Cleanup

### Removed redundant `syncAllTables()` from `useSync`
- **Before:** Both `flushQueue()` and `syncAllTables()` ran on mount and reconnect
- **After:** Only `flushQueue()` runs — it processes the sync_queue table which is the single source of truth for pending syncs
- `syncAllTables()` still exists for manual/forced full sync, but no longer runs automatically

---

## CI Gate Results

| Stage | Status |
|-------|--------|
| `npm run typecheck` | ✅ 0 errors |
| `npm run test:run` | ✅ 182/182 passing (15 files) |
| `npm run build` | ✅ 201 KB main, 372 KB charts (lazy), 215 KB Supabase, 142 KB React |

**Test growth:** 151 → 182 tests (+20%), 12 → 15 test files.

---

## Files Changed

```
A  src/lib/csv.test.ts                  +76 lines (7 new tests)
A  src/lib/whatsapp.test.ts             +65 lines (7 new tests)
A  src/lib/pushNotifications.test.ts    +111 lines (11 new tests)
M  src/lib/repository.test.ts           +74 lines (6 new tests, vi.mock supabase)
M  src/lib/__tests__/syncQueue.test.ts  rewritten (any-typed import helpers)
M  src/features/transactions/RecordSale.test.tsx -1 line (unused waitFor)
M  src/features/transactions/RecordSale.tsx      +4 lines (useEffect for paymentMethod)
M  src/screens/PosScreen.tsx            3 lines (cents() wrapping)
M  src/screens/AddScreen.tsx            +2 lines (useMemo wrapper)
M  src/hooks/useSync.ts                 -2 lines (remove syncAllTables import/call)
M  vite.config.ts                       +3 lines (vendor-charts manual chunk)
M  CHANGELOG.md
M  package.json                         (5.5.0 → 5.6.0)
```
