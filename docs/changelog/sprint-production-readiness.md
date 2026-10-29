# Sprint: Production Readiness (v5.9.0)

**Date**: 2026-07-24
**Focus**: Deployment consolidation, performance, E2E testing, CI hardening

---

## Layer 1: Deployment URL Consolidation
- Updated `SECURITY.md`: `daftari-olive.vercel.app` → `daftari-amber.vercel.app`
- Updated `ai-context/devops.md`: production URL reference corrected
- Production identified as `daftari-amber.vercel.app` (verified live); `*-daniel-muhoros-projects.vercel.app` URLs are private preview deployments

## Layer 2: Performance — Cached Nairobi Timezone
- Created `src/lib/dates.ts`: cached UTC+3 offset utilities (`nowInNairobi`, `todayNairobi`, `nairobiHour`, `nairobiISO`)
- Replaced7 inline `new Date(x.toLocaleString('en-US', { timeZone: 'Africa/Nairobi' }))` calls across the codebase
- Each call was creating a new `Intl.DateTimeFormat` (~91ms in Chrome DevTools traces)
- Files changed: `DashboardScreen.tsx`, `AppShell.tsx`, `WeekSection.tsx`, `DailyClose.tsx`, `useRecordingStreak.ts`, `HistoryScreen.tsx`, `receiptId.ts`
- Created `src/lib/dates.test.ts`: 8 tests covering UTC+3 offset, midnight boundary, format validation

## Layer 3: Playwright E2E Setup
- Installed `@playwright/test`
- Created `playwright.config.ts`: Chromium project, dev server integration, CI-friendly settings
- Created `e2e/` directory with 4 test suites:
  - `app.spec.ts`: App loads, shows test data, displays profit card
  - `navigation.spec.ts`: Tab navigation (Add, History, Settings)
  - `record-sale.spec.ts`: Opens sale form, fills and submits
  - `pwa.spec.ts`: Service worker registration, IndexedDB access
- Added `VITE_E2E=true` mode to `App.tsx`: bypasses Supabase auth, seeds test business + transactions
- Added `test:e2e` and `test:e2e:ui` scripts to package.json
- Excluded `e2e/` from vitest config
- Note: Playwright browsers require system deps — works in CI with `--with-deps` or on dev machines

## Layer 4: Sentry Verification
- Confirmed `@sentry/react` fully wired:
  - `initSentry()` called in `main.tsx` before render
  - `captureError` used in `useSync.ts`, `repository.ts`
  - PII scrubbing in `beforeSend` (removes email, username, IP)
  - 20% trace sampling in production
  - `captureBreadcrumb`, `setSentryUser`, `clearSentryUser` utilities available
- No changes needed — already production-ready

## Layer 5: CI Enhancements
- Added bundle size budget check to `.github/workflows/ci.yml`:
  - Reports `index.js` size, warns if >300KB
  - Reports total `dist/` size
- Added commented E2E step template for when Playwright is enabled in CI

## Quality Gates (all passing)
- `typecheck`: 0 errors
- `lint`: 0 errors, 1 pre-existing warning
- `check:i18n`: 194/194 keys
- `test:run`: 334 tests across 29 files
- `build`: success, 40 precache entries, PWA generated

## Test Count
- Unit tests: 334 (was 326 — added8 dates tests)
- E2E tests: 4 test suites (ready to run when Playwright browsers available)
