# Sprint: E2E CI Green (v5.9.2)

**Goal:** Fix all 10 Playwright E2E tests to pass consistently in CI.

## Root Cause Analysis

The E2E tests had been failing since the Playwright framework was introduced (v5.9.0). Three compounding issues:

1. **Module-level Supabase crash**: `src/lib/supabase.ts` called `createClient(undefined, undefined)` at module import time because `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` env vars were not set in CI. In supabase-js v2.57+, this throws "supabaseUrl is required" — prevents React from even mounting.

2. **Async race in E2E data seeding**: The original approach seeded test data inside a `useEffect` IIFE. React showed `<LoadingScreen />` while seeding ran; Playwright timed out waiting for "Test Shop" before the re-render completed.

3. **Env var propagation unreliable**: `VITE_E2E=true` set via npm script + CI step env was inconsistently reaching `import.meta.env.VITE_E2E` in the browser context.

## Changes

### New Files
- `src/lib/e2e.ts` — Seeds Dexie (1 business + 3 transactions) and Zustand store synchronously before React mount

### Modified Files

#### `src/main.tsx`
- E2E seeding moved out of React: `seedE2eData()` called in `bootstrap()` before `createRoot()`
- Triple-check E2E detection: `import.meta.env`, URL param, `window.__E2E__`
- Try-catch around seeding to render app even if seeding fails

#### `src/App.tsx`
- Initial state for E2E mode: `session: true`, `loadingDexie: false`, `loadingBusiness: false`
- First `useEffect` returns early in E2E mode (skips Supabase auth setup)
- Second `useEffect` returns early in E2E mode (skips business loading)

#### `src/lib/supabase.ts`
- Fallback URL to prevent module-level `createClient(undefined, undefined)` crash
- Creates dummy client `http://localhost:0` when env vars missing

#### `src/components/AppShell.tsx`
- `DailyClose` bottom sheet skipped in E2E mode (was triggered after 8 PM Nairobi time, intercepting navigation clicks)

#### `e2e/*.spec.ts` (all 4 test files)
- Uses `page.addInitScript()` to inject `window.__E2E__ = true` before module execution
- Fixes: `text=Faida` strict mode violation → `getByLabel('Faida KES')`
- Fixes: sale form locator `getByRole('textbox')` → `[inputmode="decimal"]` (`type=number` has implicit `role=spinbutton`)
- Adds receipt overlay dismissal step after saving a sale
- Service worker test expects `false` in dev mode (VitePWA doesn't register in dev)

### Tests
- 336 unit tests pass (30 files)
- 10 E2E tests pass in ~9.3s
- All CI gates green: typecheck, lint, i18n, test, build, bundle, Playwright, deploy
