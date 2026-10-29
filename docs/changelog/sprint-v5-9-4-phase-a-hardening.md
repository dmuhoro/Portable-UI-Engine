# Sprint: Phase A Hardening — Tenant Isolation & Launch Gate

**Version:** 5.9.4  
**Date:** 2026-08-11  
**Theme:** Pareto-compressed Month 1 hardening + Real-World Scenario Test Plan (Phase B gate)

## Layer 1 — Real-World Scenario Test Plan (Phase B deliverable)

### Added
- `docs/scenario-test-plan.md`: 30 scenarios with pass/fail criteria across auth, ledger, offline/sync, multi-business, performance, daily close, and backup. Includes automation mapping and launch gate (all 🔴 PASS on staging).

## Layer 2 — Business identity (`local_id` as canonical id)

### Added
- `src/lib/businessId.ts`: `businessLocalId()`, `mapBusinessToStore()`, `resolveActiveBusiness()`
- `src/lib/businessId.test.ts`: 6 unit tests

### Changed
- Business store `id` is now always `local_id` (never Supabase `user_id`)
- `OnboardingScreen`: generates `local_id` on first business creation
- `SettingsScreen` / `DashboardHeader`: new business and switcher use `local_id`; persist preference per user
- `src/lib/e2e.ts`: E2E seed uses `local_id` as active business id

## Layer 3 — Tenant-scoped reads & session cleanup

### Added
- `repository.getBusinessesForUser(userId)` — filters Dexie businesses by `user_id`
- `repository.getTransactionsForUser(userId)` — transactions for user or their business `local_id`s
- `store.activeBusinessIdByUser` — persisted map `userId → businessLocalId`
- `store.getPreferredBusinessId(userId)` — resolves preference on login
- `store.clearSessionState()` — clears in-memory business/transactions on logout

### Changed
- `App.tsx`: loads scoped data on session; clears session on sign-out; uses `resolveActiveBusiness`
- Cloud restore in Settings reloads tenant-scoped data only

## Layer 4 — Sync integrity (carried from 5.9.3 branch)

### Fixed
- `syncAll.ts`: mark only `succeededIndices` as synced (non-consecutive failure safe)
- Regression test in `syncAll.test.ts`

## Tests added/updated
- `businessId.test.ts`: +6
- `repository.test.ts`: +2 (tenant scoping)
- `store.test.ts`: +3 (per-user prefs, clearSessionState)
- `syncAll.test.ts`: +1 (early failure marking)

## Launch gate (from scenario plan)
- All 🔴 P0 scenarios PASS on staging
- `npm run typecheck && npm run lint && npm run test:run && npm run build` green
- Playwright E2E green in CI

## Next (Phase B execution)
- Run manual checklist in `docs/scenario-test-plan.md` against localhost + staging
- Record results in execution log table
