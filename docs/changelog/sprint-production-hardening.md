# Sprint: Production Hardening (v5.9.1)

**Date**: 2026-07-25
**Focus**: CI E2E, bundle optimization, monitoring, security headers, code quality

---

## Layer 1: E2E Enabled in CI
- Uncommented Playwright install + run steps in `.github/workflows/ci.yml`
- Increased `playwright.config.ts` test timeout to 30s, webServer timeout to 60s
- E2E tests now run in CI on every push/PR to main

## Layer 2: Bundle Optimization
- Lazy-loaded `WeekSection` in `DashboardScreen.tsx` (was eagerly importing 376KB recharts)
- All 3 recharts consumers now lazy: WeekSection, MonthlyReportScreen, ProductProfitabilityScreen
- Recharts chunk (376KB) only fetched on-demand when user navigates to chart views
- Zero recharts in main `index.js` bundle

## Layer3: Monitoring — Web Vitals + OTLP
- Created `src/lib/monitoring.ts`: CLS, LCP, FCP tracking with OTLP export
- Integrated with Sentry for error capture (unhandled errors, promise rejections)
- Configurable via `VITE_OTLP_ENDPOINT` env var (Dash0, Grafana, any OTLP backend)
- Created `src/lib/monitoring.test.ts`:2 tests
- Initialized in `main.tsx` alongside Sentry

## Layer4: Production Hardening
- CSP headers updated: added `sentry.io` to connect-src, `worker-src 'self'`
- Added security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`
- Fixed stale URLs: `robots.txt` sitemap → `daftari-amber.vercel.app`, OG URL updated
- Updated `.env.example` with `VITE_OTLP_ENDPOINT`

## Layer5: Code Quality Tools
- Created `.coderabbit.yaml`: path-specific review instructions (money safety, Dexie, i18n)
- Created `.sourcery.yaml`: custom rules (no raw money arithmetic, no direct Dexie imports, no console.log)
- Created `.github/CODEOWNERS`: ownership rules for money safety, DB schema, CI/CD, i18n

## Quality Gates (all passing)
- `typecheck`: 0 errors
- `lint`: 0 errors, 2 pre-existing warnings
- `check:i18n`:194/194 keys
- `test:run`: 336 tests (was 334 — added2 monitoring tests)
- `build`: success

## Test Count
- Unit tests: 336 across 30 files
- E2E tests:4 test suites (running in CI)
