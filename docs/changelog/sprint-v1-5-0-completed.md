# Sprint v1.5.0 — Auth Polish, Password Reset, i18n Cleanup, Beta Prep

**Date:** 2026-07-19  
**Version:** 1.5.0  
**Status:** Completed ✅

## Objective
Polish auth flows for production readiness, add password reset/recovery, clean tech debt, and prepare for beta launch.

## Scope

### Section A — Auth Flows
- "Forgot Password?" link on sign-in form triggering `supabase.auth.resetPasswordForEmail()` with redirect
- `PASSWORD_RECOVERY` event listener in `App.tsx` setting `authMode='recovery'` on redirect with `type=recovery`
- Inline `ResetPasswordScreen`-style recovery UI in `AuthScreen.tsx`
- Signed-in state badge showing email in Settings screen
- Resend confirmation email on sign-up error (`email_not_confirmed`)
- `authMode` prop routed through `App.tsx` to `AuthScreen.tsx`

### Section B — Auth Edge Cases
- Reset email sent confirmation screen
- Recovery redirect handling (token in URL → Supabase session recovery)
- Error states for expired/invalid reset links

### Section C — Ops Readiness
- `public/robots.txt` — search-engine crawl rules for production
- OG meta tags (`og:title`, `og:description`, `og:type`, `og:url`, `og:image`) in `index.html`
- Self-hosted Sentry integration with DSN config via `VITE_SENTRY_DSN`
- CSP header in `vercel.json`
- Vercel SPA rewrites in `vercel.json` for client-side routing
- CI pipeline: `.github/workflows/ci.yml` with typecheck, lint, i18n check, test, build

### Section D — Tech Debt
- `scripts/check-i18n.ts` — i18n coverage linter for CI
- `DYNAMIC_KEYS` exclusion list for programmatically-used keys (`sale_recorded`, `expense_recorded`, `withdrawal_recorded`)
- 28 unused translation keys removed from both `sw.json` and `en.json`
- `src/test/mocks.ts` wired into vitest `setupFiles` via `src/test/setup.ts`
- Missing `track(EVENTS.TRANSACTION_RECORDED)` call added to `handleAddAllTemplates` in `RecordSale.tsx`
- Global Dexie mock factory for unit tests

### Section E — Verification
- TypeScript check: 0 errors
- ESLint: 0 warnings
- Tests: 53/53 pass
- i18n linter: 149 keys, clean
- Build: succeeds with PWA generation
- Changelog updated, pushed to GitHub

## Files Created
- `public/robots.txt`
- `public/404.html`
- `scripts/check-i18n.ts`
- `src/components/OnboardingSessionCounter.tsx`
- `src/lib/analytics.ts`
- `src/lib/sentry.ts`
- `src/test/mocks.ts`
- `supabase/migrations/002_create_daftari_analytics.sql`

## Files Modified
- `src/screens/AuthScreen.tsx` — reset password, recovery mode, resend confirmation
- `src/App.tsx` — PASSWORD_RECOVERY event, authMode routing
- `src/screens/SettingsScreen.tsx` — signed-in badge
- `src/i18n/sw.json` — 10 new keys, 28 removed
- `src/i18n/en.json` — 10 new keys, 28 removed
- `index.html` — OG meta tags
- `vercel.json` — CSP, SPA rewrites
- `src/test/setup.ts` — mocks import
- `src/features/transactions/RecordSale.tsx` — track() call
- `package.json` — version 1.1.0 → 1.5.0
- `CHANGELOG.md` — v1.5.0 section

## Acceptance Criteria
- [x] Password reset flow sends email and handles recovery redirect
- [x] Resend confirmation email on signup error
- [x] Signed-in badge in Settings
- [x] OG tags present in index.html
- [x] robots.txt served at /robots.txt
- [x] Sentry captures errors
- [x] 28 unused i18n keys removed
- [x] 0 unused i18n keys reported
- [x] Test mocks wired and working
- [x] All verification stages pass
- [x] Changelog updated
- [x] Git: committed and pushed

## Dependencies
- Sprint v1.4.0 completed (Sentry, analytics, CI)

## Next
- Edit/delete transactions
- Monthly P&L reports
- CSV export
- Customer 360 view
