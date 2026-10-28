# Sprint: Hardening Phase Five — Test Coverage Expansion

**Version:** 5.6.0 → 5.7.0  
**Date:** 2026-07-22  
**Theme:** Expand test coverage from 56% to 74% lines, add tests for untested lib/ modules

---

## Layer 1 — Baseline Verification

| Gate | Status |
|------|--------|
| `npm run typecheck` | ✅ 0 errors |
| `npm run test:run` | ✅ 182/182 passing (15 files) |

---

## Layer 2 — print.ts Tests (+25 tests)

| Function | Tests | What's covered |
|----------|-------|----------------|
| `formatReceiptText()` | 15 | Business name, receipt ID, amount, date, customer name (present/absent), items (present/absent), description (present/absent), payment method omission, loyalty earned/redeemed, discount lines, thank you message |
| `printBrowserReceipt()` | 5 | Window open, HTML write with business name, document close, print call, early return on null window |
| `printBluetoothReceipt()` | 5 | No Bluetooth API, GATT connection failure, no writable characteristic, writeValue call, non-Error exception wrapping |

---

## Layer 3 — useToast.ts Tests (+3 tests)

| Component | Tests | What's covered |
|-----------|-------|----------------|
| `useToast()` | 3 | Default no-op from context, provided toast function via context provider, context value shape |

---

## Layer 4 — analytics.ts Tests (+8 tests)

| Function | Tests | What's covered |
|----------|-------|----------------|
| `track()` | 3 | Logger integration, auto-flush at 10 events, no flush below 10 |
| `flush()` | 4 | Supabase insert, empty queue returns, error requeue, exception handling |
| `EVENTS` | 1 | 23 event constants exported |

---

## Layer 5 — backup.ts Tests (+6 tests)

| Function | Tests | What's covered |
|----------|-------|----------------|
| `exportAllData()` | 6 | All 8 Dexie tables read, JSON blob creation, download trigger via anchor, URL create/revoke, empty tables, table read error handling |

---

## Layer 6 — referral.ts Tests (+10 tests)

| Function | Tests | What's covered |
|----------|-------|----------------|
| `generateReferralUrl()` | 6 | Ref code (first 4 chars), canonical domain, category param present/absent, lowercase, short names |
| `shareViaWhatsApp()` | 4 | Swahili message, English message, URL inclusion, analytics tracking |

---

## Layer 7 — logger.ts Tests (+9 tests)

| Method | Tests | What's covered |
|--------|-------|----------------|
| `logger.info()` | 2 | Dev prefix, no-data variant |
| `logger.warn()` | 2 | Dev prefix, no-data variant |
| `logger.error()` | 3 | Error objects, non-Error values, no-data variant |
| `logger.track()` | 2 | Analytics prefix, no-data variant |

---

## Layer 7 — sentry.ts Tests (+15 tests)

| Function | Tests | What's covered |
|----------|-------|----------------|
| `initSentry()` | 5 | No DSN skips init, DSN present calls init, beforeSend strips user PII, passes events without user, ignoreErrors list |
| `captureError()` | 3 | No DSN skips, DSN calls withScope, sets feature/action tags |
| `captureBreadcrumb()` | 3 | No DSN skips, DNS adds breadcrumb, defaults category to "app" |
| `setSentryUser()` | 2 | No DSN skips, DSN sets user |
| `clearSentryUser()` | 2 | No DSN skips, DSN clears user |

---

## Coverage Improvement

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Statements | 54.57% | 72.88% | +18.31% |
| Branches | 43.6% | 61.38% | +17.78% |
| Functions | 68.18% | 84.41% | +16.23% |
| Lines | 56.33% | 74.4% | +18.07% |

---

## CI Gate Results

| Stage | Status |
|-------|--------|
| `npm run typecheck` | ✅ 0 errors |
| `npm run test:run` | ✅ 258/258 passing (22 files) |
| `npm run build` | ✅ 40 entries precached |

**Test growth:** 182 → 258 tests (+42%), 15 → 22 test files.

---

## Files Added

```
A  src/lib/print.test.ts           +219 lines (25 new tests)
A  src/lib/analytics.test.ts       +102 lines (8 new tests)
A  src/lib/backup.test.ts          +104 lines (6 new tests)
A  src/lib/referral.test.ts        +92 lines  (10 new tests)
A  src/lib/logger.test.ts          +78 lines  (9 new tests)
A  src/lib/sentry.test.ts          +186 lines (15 new tests)
A  src/hooks/useToast.test.ts      +28 lines  (3 new tests)
M  src/lib/backup.test.ts          (fixed URL spy type with as any)
```
