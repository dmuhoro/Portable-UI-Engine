# Daftari hardening — anti-fragility audit (2026-09-05)

Maps Daftari's actual defenses to the ecosystem's anti-fragility rules. Honest: what is proven here
at the real boundary, and what needs real credentials/hardware to prove.

## Proven at the code boundary (existing, audited today)

| Invariant | Where enforced | Notes |
|---|---|---|
| Money math is integer-cents only | `src/lib/money.ts` (ADR-007) | no floats on any amount path |
| Cross-tenant isolation at write | repository writes scope by `business_id`/`user_id` | task data integrity |
| Local-first write always succeeds offline | `saveTransaction` → Dexie, returns `Result` | never throws/never silent-swallows failures |
| No silent drops on sync | `syncAll` keeps per-record errors + `succeededIndices`; `syncQueue` retries with exponential backoff + circuit breaker + `MAX_RETRIES`, then **dead-letter kept** (never removed) | failed records stay in IndexedDB pending |
| Failure is surfaced to the user | `OfflineBanner` ("No internet — data saved locally"), history shows pending state | explicit, not silent |
| Render crashes contained + reported | `ErrorBoundary` wraps `App` + every screen (AppShell case map); `captureError` → Sentry | restart/reset UI |
| Auth/FK consistency | `&local_id` unique indexes, `onConflict:'local_id'` upsert | idempotent sync |

## Proven at the production-build boundary (new in v6.4.0)

`e2e/pwa-prod.spec.ts` (runs `vite preview` against the real `vite build`):

1. **Installability**: manifest serves PNG `192x192` + `512x512` (+ `maskable` 512), `standalone`,
   `start_url '/'`, apple-touch-icon linked and reachable — the fixes that turn the "opens in
   browser" symptom into a real install prompt.
2. **Offline shell**: full offline reload keeps the app shell + seeded IndexedDB ledger alive —
   no crash, offline banner shown.
3. **Offline write is never dropped**: an offline-recorded sale is in IndexedDB with `synced=0`,
   survives the reload, and survives sync failure — the queue retains it, it is never removed.

## Not yet provable in CI (honest, documented)

- **Remote sync success** against real Supabase — needs `VITE_SUPABASE_URL`/`ANON_KEY` + a tenant;
  CI deliberately has none. The local contract (persist → retry → never drop) is proven; the
  *uploads* are not under CI.
- **Real on-device install gesture** — Android "Install app" is a human Chrome step; headless
  Chromium cannot click it. Manual device checklist: `docs/offline-verified.md`.
- **iOS specifics** — needs a physical iPhone; apple-touch-icon shipped, eviction behavior
  documented in ADR-011.

## Anti-fragility posture

The failure modes that would hurt a street vendor (lost sale entry, double-billed amounts, lost
ledger) are each owned by exactly one mechanism that **fails closed**: money.ts (cents), repository
(Result + retry portal), syncQueue (circuit breaker + dead-letter), ErrorBoundary (contained crash +
Sentry). New surfaces must keep the same contract; ADR-011 keeps the core data contract the one
platform boundary.