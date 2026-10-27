# Sprint 7.5: v6.8.0 Subscription and Billing

**Status:** Completed
**Version Target:** v6.8.0
**Branch:** `feat/subscription-billing` (off `origin/main` @ b7f83ec)
**Focus:** Ship the subscription/billing layer end to end — schema, tier model, feature gating,
upgrade/payment flow, trial surface, write path instrumentation, load testing, and docs. All
gates green before any merge.

---

## Scope Note (deviation from directive)

- **Version bump is 6.8.0, not the directive's 6.0.0.** The repo is already past 6.x tagging;
  6.0.0 would be a silent downgrade of the version string. 6.8.0 is the honest next release.
- **Branch-push workflow:** the directive said `git push origin main`. Per `devops.md` there are
  NO direct pushes to main (follow-up gets force-pushed, e.g. v6.7.0). We built on
  `feat/subscription-billing` off main and will merge to main once green.
- **Unreleased ai-branch Q3–Q6 work must not ship with billing** — billing is built on
  `origin/main`, so that separation is guaranteed by construction.
- **Fail-closed default deviation:** the directive's `DEFAULT_SUBSCRIPTION` used
  `is_active: true` (would grant premium to any subscription that fails to load). We ship the
  fail-closed default (`msingi` / `cancelled`, unlocks nothing). A row that cannot be loaded must
  never be read as full access.
- **`requireReauth` is infrastructure, not a wired flow.** The directive asked to prepend a
  reauth gate before account deletion, but the app has **no** `deleteAccount` flow to gate.
  Per the execution guardrails, claiming a gate over a nonexistent path is fake protection.
  We ship the tested helper (fails closed on missing/expired session) and document that it awaits
  a real caller — the delete-account i18n keys were therefore not shipped.

## Migration notes (operator must apply)

Migrations are committed under `supabase/migrations/` and must be applied to Supabase project
`rjedivbpldkroffswoyb` (SQL editor or `supabase db push`). No credentials live in the repo.

- `20260922000000_create_subscriptions.sql`
  - Enums `subscription_tier`, `subscription_status` (idempotent `DO` blocks).
  - `daftari_subscriptions` (PK `user_id`) with trial defaults, ON DELETE CASCADE.
  - RLS enabled; select = owner only; insert/update/delete = `with check (false)` (app never
    mutates records directly; signup trigger owns the seat).
  - Security-definer trigger `create_subscription_on_signup` on `auth.users` AFTER INSERT with
    `on conflict (user_id) do nothing` — every brand-new auth user gets a 30-day trial.
  - **P0:** `user_subscription` view is created `WITH (security_invoker = true)` so the owning
    role cannot peek past RLS; grants select to `authenticated` and `service_role`.
- `20260922000001_create_subscription_requests.sql`
  - `daftari_subscription_requests` (pending/verified/rejected) with `amount_kes > 0` CHECK.
  - RLS: owner inserts + selects own rows only; no update/delete.

## What shipped

### Data + access
- `types.ts` — `SubscriptionTier`, `SubscriptionStatus`, `FeatureKey` (12), `TIER_FEATURES`
  (`as const satisfies Record<FeatureKey, readonly ('biashara'|'biashara_plus')[]>`),
  `FREE_TIER_TRANSACTION_LIMIT = 100`, `Subscription` mirroring the view.
- `constants.ts` — `VERSION 6.8.0`, `TABLES.SUBSCRIPTIONS/SUBSCRIPTION_REQUESTS`,
  `VIEWS.USER_SUBSCRIPTION`, `STORAGE_KEYS.SUBSCRIPTION`, `PRICING` (0 / 299 / 799, placeholder
  pay number, TRIAL_DAYS 30).
- `lib/subscription.ts` — pure `hasFeature`/`isPaid`/`isOverFreeLimit`/`trialDaysLeft` +
  `isSubscription` runtime guard + fail-closed `DEFAULT_SUBSCRIPTION`.
- `hooks/useSubscription.ts` — cache-first, refresh-on-mount from the view, malformed row →
  fail closed, fetch error → keep stale cache, loading → render nothing premium.

### UI
- `FeatureGate` — locked `Card` (lock + CTA → upgrade) vs. children; empty placeholder while
  loading so premium content never flashes.
- `UpgradeScreen` — plan cards from `TIER_FEATURES` reverse-map, M-Pesa bottom sheet (copy pay
  number, WhatsApp receipt line, "I have paid" → inserts `subscription_request`), pending toast.
- `AppShell` — `'upgrade'` view, trial countdown banner (exported as
  `TrialCountdownBanner.tsx`), 5 gated screens (monthly-report, suppliers, purchase-orders, pos,
  customers); product-profitability/stock-adjustments/batch-entry deliberately ungated.
- `SettingsScreen` — subscription card (tier, status chip, price, manage → upgrade).

### Operations / safety
- `supabase.ts` — `requireReauth(): Promise<Result<boolean>>` (getUser + `reauthenticate`,
  fails closed on any doubt, `SUPABASE_AUTH_FAILED` code).
- `scripts/load-test.js` + `test:load` + `CONTRIBUTING.md` load-testing section (k6 static-shell
  GET; k6 not installed locally, so the script is authored, not executed).
- `check-i18n.ts` registers UpgradeScreen + SettingsScreen as dynamic-key sites (labelKey maps);
  i18n now 290 keys per language, zero unused.

## Gates

| Gate | Result |
| --- | --- |
| `npm run typecheck` | ✅ |
| `npm run lint` | ✅ (0 problems) |
| `npm run check:i18n` | ✅ 290/290, 0 unused |
| `npm run test:run` | ✅ 49 files / 476 tests |
| `npm run build` | ✅ |

## Honest gaps (not closed)

- `requireReauth` has no caller yet (no account-deletion flow exists in the app). Helper is
  tested and fail-closed; wiring it to a fabricated boundary would be fake protection.
- Free-tier cap (`FREE_TIER_TRANSACTION_LIMIT`) is enforced client-side AT the real
  remote-write boundary (`flushQueue` + `syncAllTables` refuse transaction upserts for a
  free account at/over the cap; blocked records stay local and flush after upgrade — proven
  by boundary tests asserting Supabase is never called). Server-side enforcement on the
  proxy/service layer is still absent — a hostile client can bypass; that gap is not closed.
- M-Pesa number is a placeholder (`YOUR_MPESA_NUMBER_HERE`) — operator must replace it.
- Payment request status is manual (pending → verified by operator); no auto-verification.
- Migrations are NOT applied to the live Supabase project (manual operator step).