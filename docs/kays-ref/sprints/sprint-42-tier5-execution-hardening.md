# Sprint 42 — Tier 5 Execution Hardening (Honest Delivery + App-Wide Revocation)

**Theme:** Execute the residual audit gaps that touch the real money/ops path: make every
automation send **honest** (breaker + no double-send + fail-closed provider), enforce session
**revocation app-wide** (not just at the diagnostics gate), remove the dead client-side
`PasscodeGate`, make the dashboard's "Live telemetry" **actually live**, harden the cron
endpoints so they cannot run with a secret fallback in production, ship a three-mode theme and
real-UI tests for the previously untested screens, gate data export/import behind the paywall,
and hand the owner an **access + screen-tour guide**.

**Result: 756 unit tests green (74 files), `tsc --noEmit` exit 0, ESLint 0 errors on touched
files, production build OK, Playwright E2E 5/5.**

## Summary

| Before | After |
|--------|-------|
| Automation sent WhatsApp via raw `sendWhatsApp` **and** double-enqueued `msg_*` notifications; sending wasn't honest about failures. | Every automation send branch routes through `dispatchWithBreaker` and writes the `message_ledger` (with `{automation, stage, provider}` metadata); the `enqueueNotification` `msg_*` writes are removed — a test asserts `enqueueNotification` is never called for automation sends. |
| In production with no WhatsApp provider configured, `sendWhatsApp` claimed `{success:true}` (log provider). | Production + missing tokens → honest `{success:false, provider:"unconfigured"}` + ERROR log; breaker records the failure; owner is paged. Dev/test keep the `{success:true, provider:"log"}` harness. |
| Failed M-Pesa STK callbacks were logged but not surfaced to the owner. | `handleStkCallback` pages the owner (`stk_callback_failed`, deduped by `stk:<requestId>`). |
| Session revocation (`isSessionActive`) was checked at the diagnostics gate only; `requireOrg()` was sync and never touched the session row. | `requireOrg()` is **async** and verifies the `user_sessions` row on every tenant-scoped call (fail closed); `requireRole()` awaits it. All ~48 call sites updated. A revoked/logged-out token is rejected app-wide. |
| `PasscodeGate.tsx` (hardcoded `"0726"`) was dead code claiming to be auth. | Deleted; docs updated. Diagnostics gated by server RBAC + session revocation only. |
| Dashboard showed a "Live telemetry" badge but did one-shot fetch; no SSE refresh. | `useLiveEvents` silently refetches on live-relevant event types; badge tooltip explains the behaviour. |
| Cron endpoints fell back to a known `dev-cron-secret` in production (`CRON_SECRET || "dev-cron-secret"`) — a guard that could be bypassed by knowledge of the repo. | Production + missing `CRON_SECRET` → 503 (no bearer value to compare). Automation orchestrator added to Vercel cron (`*/15 * * * *`). |
| Theme was a binary light/dark toggle; UI had export-shape-only tests. | Three-mode theme (light/dark/system) with live OS-follow + pre-paint script; BookingWidget, PipelineBoard, and ThemeToggle now have real happy-dom render tests. |
| Export/import on `/admin/settings/data` was free for any owner/admin; upgrade buttons were inert. | Both sections wrapped in `SubscriptionGuard feature="bulk_operations"`; `PaywallModal` upgrade buttons are real `mailto:ceo@kayswellnesscentre.org` links (no fake checkout). |

## Part 1 — Tier 1: notification honesty

`src/lib/api/automation.server.ts`: the three send branches (UNTOUCHED / TRIAGING / STALLED
stages) now call `dispatchWithBreaker(orgId, phone, text)` and write a `message_ledger` row with
metadata `{automation: true, stage, provider}`. The duplicate `enqueueNotification` `msg_*`
writes are gone — a lead can never be blast twice for one automation decision.

`src/lib/api/dispatch.server.ts` `sendWhatsApp`: in **production** with no
`WHATSAPP_TOKEN`/`WHATSAPP_PHONE_NUMBER_ID` the result is
`{ success: false, provider: "unconfigured", error: "WhatsApp provider not configured" }` with
an ERROR log. `NODE_ENV` is read directly (not via `getEnv()`, which would pull the full env
schema in tests). Dev/test continue to resolve to the `{ success: true, provider: "log" }`
harness.

## Part 2 — Tier 2: app-wide revocation, clean-up, live dashboard, cron hardening

- **`requireOrg()` is now async** (`tenant.server.ts`): after the `getCurrentOrgId()` tenant
  check it calls `getSession()` + `await isSessionActive(session)`; a missing/revoked `sid`
  throws `TenantError("Session is inactive or revoked — please sign in again")` with an
  `AUTH_FAILURE` warn log. DB hiccup → `isSessionActive` returns `false` → **fail closed**.
- **`requireRole()` is now async** and awaits `requireOrg()`, so the role gate also carries the
  revocation check. All call sites (18 files `requireOrg()`, 16 `requireRole()`; ~48 calls)
  updated with `await`; `tsc` green across the whole repo, full suite green.
- **`getServerStatus` stays unauthenticated** (documented in `tenant-isolation-p0.test.ts`) —
  keeping that assertion; the revocation boundary lives in `requireOrg()`, which the diagnostics
  gate already flows through.
- **`PasscodeGate.tsx` deleted**; `auth-components.test.ts` no longer asserts it. Docs updated in
  the same change (AGENTS rule 2): `security.md`, `decisions.md` D3, `release-readiness.md` #16,
  `code-standards.md`.
- **Dashboard live telemetry**: `src/routes/admin/dashboard.tsx` subscribes via `useLiveEvents`
  and rewrites the analytics snapshot on `lead:acquired`, `lead:stage_changed`, `lead:updated`,
  `invoice:created`, `payment:recorded`, `stk_push:paid`, `reconciliation:matched` — silently
  (no loading flash), with the badge tooltip stating the behaviour.
- **Cron fail-closed**: both `server/routes/api/cron/*` compute
  `CRON_SECRET = NODE_ENV === "production" ? (process.env.CRON_SECRET ?? null) : (process.env.CRON_SECRET || "dev-cron-secret")`
  and return 503 when null. `vercel.json` schedules automation-orchestrator `*/15 * * * *`.

## Part 3 — Tier 3: theme 3-mode + real-UI tests + paywall

- **Three-mode theme** (`src/hooks/use-theme.ts`): `Theme = "light"|"dark"|"system"`;
  `resolveTheme()` follows `matchMedia("(prefers-color-scheme: dark)")` with a live `change`
  listener; `ThemeToggle` cycles Light → Dark → System (Monitor icon); `__root.tsx` pre-paint
  script also respects system mode. `resolvedTheme` exposed on the context.
- **Real-UI tests** (happy-dom + real `createRoot` + real `QueryClient`):
  - `booking-widget.test.tsx` (2) — step gating (Continue disabled), full 3-step flow, and the
    exact `submit({name, email, service, channel, preferred_language})` payload + success screen.
  - `pipeline-board-render.test.tsx` (4) — five columns with counts, follow-up message through
    the real mutation path, terminal confirm → `updateLeadAsync` + `logDrag` + invoice
    generation, priority change.
  - `theme-toggle.test.tsx` (3) — system default, full light→dark→system→light cycle applying
    the `dark` class + persisting, stored-preference load.
- **Paywall on data management**: `/admin/settings/data` export + bulk-import are wrapped in
  `SubscriptionGuard feature="bulk_operations"`; `PaywallModal` upgrade buttons →
  `mailto:ceo@kayswellnesscentre.org` (no fake checkout).

## Part 4 — Tier 4: operator guide

`docs/kwc-os-access-guide.md` — env + login + roles/tiers, the end-to-end screen tour
(public funnel → login → dashboard → triage → finance → settings → diagnostics), the automation
& owner-paging story, and the honest "not live" table (what credentials are owner-held and what
happens instead — including the new fail-closed WhatsApp behaviour).

## Test evidence

| File | Kind | Count | What it proves |
|------|------|-------|----------------|
| `automation.test.ts` | Vitest | 9 | Sends route through `dispatchWithBreaker`; `message_ledger` carries `{automation, stage, provider}`; **`enqueueNotification` never called** (no double-send) |
| `dispatch.test.ts` | Vitest | 16 | Production + missing tokens → `{success:false, provider:"unconfigured"}`; dev/test → `{success:true, provider:"log"}` |
| `mpesa-stk-push.test.ts` | Vitest | 12 | Non-success `ResultCode` → `pageOwner({type:"stk_callback_failed", fingerprintKey:"stk:<id>"})` |
| `require-org-revocation.test.ts` | Vitest (real `requireOrg`/`requireRole`) | 3 | Revoked session → reject; live session → resolves org context; revoked role gate → reject (fail closed) |
| `session-revocation.test.ts` + `tenant-isolation-p0.test.ts` | Vitest | 30 | Diagnostics gates + P0 isolation assertions still green after the async conversion |
| `booking-widget.test.tsx` / `pipeline-board-render.test.tsx` / `theme-toggle.test.tsx` | happy-dom | 9 | Real-DOM behaviour (see Part 3) |
| `npm test` / `tsc --noEmit` / ESLint | unit | 756/74 | Full suite green; tsc 0; ESLint 0 on touched files |
| `npm run e2e` | Playwright (prod build + PGlite) | 5/5 | Revenue path still green end-to-end |

## Files Changed

- **Tier 1:** `src/lib/api/automation.server.ts`, `src/lib/api/dispatch.server.ts`,
  `src/__tests__/automation.test.ts`, `src/__tests__/dispatch.test.ts`.
- **Tier 2:** `src/lib/tenant.server.ts`, `src/lib/permissions.server.ts`,
  `src/lib/api/{scheduling,analytics,billing,leads,mpesa,clinic-config,automation,dispatch,
  subscription,org-settings,webhooks,interactions,resources}.server.ts`,
  `src/lib/{import,exports,telemetry}.server.ts`, `src/lib/api/{diagnostics,notifications}.server.ts`,
  `src/lib/owner-alerts.server.ts`, `src/lib/api/mpesa.server.ts`,
  `server/routes/api/cron/{automation-orchestrator,heartbeat}.ts`, `vercel.json`,
  `src/routes/admin/dashboard.tsx`, `src/__tests__/require-org-revocation.test.ts`,
  `src/__tests__/auth-components.test.ts` (PasscodeGate assertion removed with the artifact).
- **Tier 3:** `src/hooks/use-theme.ts`, `src/components/ThemeToggle.tsx`,
  `src/routes/__root.tsx`, `src/routes/admin/settings/data.tsx`, `src/components/PaywallModal.tsx`,
  `src/__tests__/{booking-widget,pipeline-board-render,theme-toggle}.test.tsx`.
- **Docs (AGENTS rules 2/7):** `docs/db-contracts.md` (new `user_sessions` read contract),
  `docs/release-readiness.md` (#16, #39, #62, new rows 80–89), `docs/current-state.md`,
  `docs/security.md`, `docs/decisions.md`, `docs/code-standards.md`, `CHANGELOG.md`,
  `docs/kwc-os-access-guide.md` (new), this sprint doc, `docs/sprint-cross-reference.md`.

## Status

- [x] Tier 1: honest WhatsApp sends; automation never double-sends; breaker on the real path
- [x] Tier 2: app-wide session revocation (async `requireOrg`/`requireRole`, ~48 call sites);
  PasscodeGate removed; dashboard live telemetry wired; cron fail-closed + scheduled
- [x] Tier 3: three-mode theme; real-UI tests (BookingWidget/PipelineBoard/ThemeToggle);
  paywall-gated data export/import with honest mailto upgrade
- [x] Tier 4: `docs/kwc-os-access-guide.md` access + screen tour
- [x] 756 tests / 74 files green; tsc 0; ESLint 0; build OK; E2E 5/5
- [x] `docs/db-contracts.md` updated in the same change as the tenant-scoping edit (rule 2)

## Owner Follow-ups

- Set `WHATSAPP_TOKEN` / `WHATSAPP_PHONE_NUMBER_ID`, Daraja `MPESA_*`, Supabase `DATABASE_URL`,
  and `CRON_SECRET` before the production deploy; until then the fail-closed paths are the
  correct, honest behaviour.
- One manual browser check on `/admin/settings/data` as a starter-tier org to see the paywall
  card + mailto click-through (row #60).
- Drag-and-drop on the pipeline board uses HTML5 drag events, which the happy-dom harness does
  not simulate; board drag behavior remains covered by the pipeline-board export tests + the
  E2E revenue path.