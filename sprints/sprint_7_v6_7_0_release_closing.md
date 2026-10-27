# Sprint 7: v6.7.0 Release Closing + Landing Marquee

**Status:** Completed  
**Version Target:** v6.7.0  
**Focus:** Close the release cleanly — fix the broken code that a prior AdminScreen parse error
had masked from the gates, add the animated niche marquee to the landing screen, and ship the
missing release documentation. Every gate (lint, typecheck, i18n parity, tests, build) is green
before the tag moves.

---

## Context

The v6.7.0 tag had been created on a commit (`1d84601`) whose working tree was **not** green:
`npm run typecheck` failed and the AdminScreen had a real JSX parse error that broke the whole
screen. The admin-role door was not actually enforced (no guard existed), the `store.role` field
was not typed on `AppStore`, `APP.VERSION` was stale at `6.6.0`, and `docs/user-guide.md` +
`docs/deployment-runbook.md` did not exist. Root cause traced to a botched WIP commit
(`0a02d91`) that had dropped `products?: string` from the db `Business` schema, leaving every
screen that called `updateBusiness(id, { products: … })` untypeable.

This sprint services the release back to green and re-points `v6.7.0` at the final green commit.

## Sprint Objectives

1. **Fix the layers** (in dependency order, committed individually):
   - `db.ts` — restore `products?: string` (`categories` removal reverted).
   - `store.ts` — type `role: 'user' | 'admin'` on `AppStore`, add `setRole`, restore missing
     `language: 'sw'` in initial state, fix indentation.
   - `throttleWrite.ts` — generic async debounce (`Args extends unknown[], R`), explicit vitest
     imports, drop `NodeJS.Timeout`.
   - `AdminScreen.tsx` — resolve the `))}` parse error, import the analytics
     `totalRevenue/totalProfit/activeUserCount/revenueLast7Days` helpers, and add the fail-closed
     role guard (`role !== 'admin'` → early "Not authorized" return after all hooks). New
     `AdminScreen.test.tsx` proves non-admins never see the Revenue or Businesses sections
     (2 tests, recharts mocked to stay deterministic in CI).
   - `OnboardingScreen.tsx` — restore the multi-select category state (`BusinessCategoryKey[]`)
     and the supabase import.
   - `PaymentMethodsScreen.tsx` — rebuild against the real repository/`AppShell` API (requires
     `onBack`, loads/saves via `getBusiness`/`updateBusiness` JSON), register `'payment-methods'`
     in the `AppShell` view union + title case, add `manage_payment_methods` to `en.json`/`sw.json`.
     Onboarding's "Payment Methods" link now lands on a working screen.
   - Build wiring — `APP.VERSION` → `6.7.0` (`constants.ts` + Settings test), `openUrl` imports in
     CustomerDetail + GrowthShare.
2. **Verification at every step**: `typecheck` then `lint` after each change; full suite
   `npm run test:run` → 42 files / 415 tests green.
3. **Landing marquee** (`LandingScreen.tsx`): implemented per the pinned design in
   `public/daftari_niche_marquee_demo.html` — two rows of emoji pill chips between the hero and
   the problem section, Kiswahili scrolling forward (28s) and English reverse (22s), beneath a
   combined bilingual header. Edges fade via CSS mask, tracks are `max-content` inside
   `overflow: hidden` (no horizontal scrollbar), dark mode via `dark:` variants, keyframes in a
   scoped `<style>` block, chips styled with inline-flex pill classes, no new dependencies and
   no new i18n keys. New `LandingScreen.test.tsx` (2 tests: doubled rows + bilingual header;
   keyframes + opposite-direction animations + edge masks).
4. **Documentation**: `docs/user-guide.md` (day-to-day usage) + `docs/deployment-runbook.md`
   (release sequence, CI gates, rollback, evidence log), both linked from `README.md`.
5. **CHANGELOG + sprint notes**: `## [6.7.0]` entry in `CHANGELOG.md`, this file, and
   `docs/changelog/sprint-v6-7-0-release-closing.md`.
6. **Release**: re-point the existing `v6.7.0` tag at the final green commit and push.

## Commit Set

* `bfd4d22` fix(db): restore products column on Business schema type
* `9815452` fix(store): type admin role, restore language initial state, add setRole action
* `d25db67` fix(throttleWrite): generic async debounce signature, explicit vitest imports
* `174281b` fix(admin): resolve JSX parse error, import analytics metrics, add fail-closed role guard + test
* `bf4e8c2` fix(onboarding): restore multi-select category state and supabase import
* `7b46f2b` fix(payment-methods): align screen with repository API, register view, add i18n key
* `2c0fe68` fix(build): sync APP.VERSION to 6.7.0, openUrl imports, test version assertion
* `6167733` feat(landing): animated niche marquee under hero with edge fade
* `20bdef8` docs: user guide and deployment runbook, link from README

## Final Gate State

| Gate | Result |
|------|--------|
| `npm run lint` | ✅ |
| `npm run typecheck` | ✅ |
| `npx tsx scripts/check-i18n.ts` | ✅ 245 keys (en ⇄ sw parity) |
| `npm run test:run` | ✅ 42 files / 415 tests |
| `npm run build` | ✅ (dist generated, PWA sw.js) |

**Honest note:** an earlier run-of-record summary claimed "everything green" while it was not;
the true green state was established by re-verification during this sprint, after the Settings
version assertion and AdminScreen tests were corrected and recharts was mocked for
deterministic CI runs.