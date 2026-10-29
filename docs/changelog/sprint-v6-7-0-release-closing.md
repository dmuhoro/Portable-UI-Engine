# Sprint v6.7.0 — Release Closing + Landing Marquee + Docs Set

**Status:** Completed — all gates green, tag re-pointed to the final green commit.

## Objective

Service the v6.7.0 release back to green. The tag had been cut on a commit that failed
`typecheck` (an AdminScreen JSX parse error had masked the errors from earlier runs), the admin
role guard did not exist, `store.role` was untyped, `APP.VERSION` was stale at 6.6.0, and the
user/operator docs did not exist. Root cause: a botched WIP commit dropped `products?: string`
from the db `Business` schema, breaking every product-write call site.

## Work completed

- **fix(db)** restore `products?: string` on `Business`.
- **fix(store)** type `role: 'user' | 'admin'`, add `setRole` (not persisted — fail-closed),
  restore `language: 'sw'` in initial state.
- **fix(throttleWrite)** generic async debounce + explicit vitest imports.
- **fix(admin)** resolve the `))}` parse error, import analytics metrics, add fail-closed guard;
  `AdminScreen.test.tsx` (2 tests, recharts mocked) proves non-admins see no Revenue/Businesses.
- **fix(onboarding)** restore multi-select category state + supabase import.
- **fix(payment-methods)** rebuild against the repository API; register the view in `AppShell`;
  `manage_payment_methods` key added to en/sw.
- **fix(build)** `APP.VERSION` → 6.7.0; `openUrl` imports; Settings test version assertion.
- **feat(landing)** emoji-pill niche marquee per `public/daftari_niche_marquee_demo.html`:
  fwd SW row (28s) + rev EN row (22s), bilingual header, CSS edge masks, no horizontal scroll,
  dark-mode-ready, no new deps or i18n keys; `LandingScreen.test.tsx` (2 tests).
- **docs** pristine user/operator/programmer guides + deployment runbook, cross-linked from
  README and from each other.

## Final gate state (v6.7.0)

typecheck ✅ · lint ✅ · check-i18n ✅ (245 keys) · test:run ✅ 42 files / 415 · build ✅