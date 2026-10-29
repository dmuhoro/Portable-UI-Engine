# Sprint 40 — Tier 3 E2E Smoke (Booking → Triage → Invoice → Payment)

**Theme:** Ship the remaining Tier 3 release safety net: a full-stack browser smoke that drives the
**real app** from client booking through triage to invoicing and payment, then close the two real
bugs it exposed. This is the last Tier 3 item.

**Result: 730 unit tests green, 5/5 Playwright E2E green, `tsc --noEmit` exit 0, ESLint 0 errors on
touched files.**

## Summary

| Before | After |
|--------|-------|
| No E2E test exercised a complete revenue path in a real browser | `tests/e2e/revenue-path.spec.ts` (5 tests) runs the production build served by Node with an in-process Postgres (PGlite) swap. Nothing is mocked — real `createServerFn` RPC, real HMAC session cookie, real schema/SQL. |
| Converting a lead to "checked-in" **silently generated no invoice** | Root cause: `useMutation().mutate` (this Stack's React Query build) **returns `undefined`** — it swallows the mutation promise. `safeUpdate` chained `onSuccess` on the call, so the invoice side-effect never ran. Fixed in `PipelineBoard.tsx` by using `mutateAsync` (`updateLeadAsync(...).then(...)`). |
| Billing ledger showed **encrypted `ENC:{...}` blobs as customer names** | `getInvoices` decrypted `lead_phone` but not `lead_name`. Now both are decrypted for ledger + STK prompt. |
| Forced to run browser tests against the dev server (blocked by a pre-existing TanStack import-protection error) | E2E runs against the **production build** (`KWC_E2E_DB=1` → Vite `node-server` preset + Nitro rollup external for PGlite, `db.server` aliased to the embedded `db.e2e.server.ts`). |

## Part 1 — E2E harness: production build + embedded Postgres

- `vite.config.ts`: when `KWC_E2E_DB=1` the build uses Nitro `node-server` preset and externalizes
  `@electric-sql/pglite` (bundling it leaves its data/wasm assets missing at runtime), and the root
  alias points `db.server → db.e2e.server.ts`. Production builds keep the `vercel` preset + real
  Postgres; `KWC_E2E_DB` must never be set in prod.
- `src/lib/db.e2e.server.ts`: drop-in `getDb` returning an `unsafe()` shim over **PGlite** (a WASM
  PostgreSQL). Reuses the real `db.schema.server.ts` (`SCHEMA_*` blocks). Client-safe (no
  `node:*` imports); data directory is `process.cwd()/.kwc-e2e-pglite`.
- `playwright.config.ts`: `webServer` runs `npm run build:e2e && node .output/server/index.mjs`
  on port 8080; workspace root; real Chrome channel; traces to `test-results/`.
- `package.json`: `build:e2e` (`KWC_E2E_DB=1 vite build`) and `e2e` (`playwright test`).

## Part 2 — The spec (`tests/e2e/revenue-path.spec.ts`, serial)

1. **Staff signs in** — real login → HMAC session cookie → lands on the Clinical Command Desk.
2. **Client books via the contact widget** — service → channel → details → "Request Booking"; the
   tenant-scoped lead lands in the real DB (widget also "succeeds" when queued, so the pipeline
   assert proves persistence).
3. **Lead triaged** — Move in the pipeline board: pending → contacted → scheduled → converted
   (terminal, explicit Confirm overlay).
4. **Invoice generated** — the ledger row for that client shows an `INV-` number, status `issued`
   (proves conversion side-effect fired).
5. **Payment** — "Pay" opens the prefilled modal → Record → toast "Payment recorded" → status flips
   to `paid` (asserts the receipt number in the payment history modal).

## Part 3 — Real bugs the smoke exposed (both fixed)

### Invoice generation silently skipped on converted check-ins

`LeadCard.safeUpdate` passed `onSuccess`/`onError` as `mutate(variables, options)`. The React Query
build in this stack returns `undefined` from `mutate` (its internal wrapper ignores the return
value), so nothing ever ran — and the invoice call was fire-and-forget `.catch(() => {})`, so the
failure was completely silent. **Fix:** use `mutateAsync` and chain `.then(...).catch(...)` on the
promise. The invoice generation now runs and the failure toast ("moved back") is real.

> Pre-existing behavior note: the same `mutate`-options pattern is used elsewhere in the pipeline
> (drag-and-drop rollback toasts). Optimistic rollback itself is unaffected (it runs on the
> hook-level `onError`, which fires reliably); wiring the drag path's per-call toasts to the promise
> is a follow-up, not part of this gap.

### Billing ledger rendered encrypted lead names

`getInvoices` decrypts `lead_phone` but not `lead_name` — the ledger row displayed
`ENC:{iv:...}` instead of the customer's name. **Fix:** `decryptFields(..., ["lead_name",
"lead_phone"])` (same read path pattern as `forecasting.server.ts` / `exports.server.ts`). The E2E
asserts the ledger row contains the client's plaintext name, so this cannot regress silently.

## Part 4 — Test evidence

| File | Kind | Count | What it proves |
|------|------|-------|----------------|
| `tests/e2e/revenue-path.spec.ts` | Playwright (real browser, prod build, embedded Postgres) | 5 | Full revenue path: sign-in → booking widget → pipeline triage to checked-in → `INV-` invoice issued in ledger → payment records receipt and flips to `paid`. Overlap-tolerant selectors (exact placeholders / overlay scoped confirms). |
| `npm test` / `tsc --noEmit` / ESLint | unit | 730/69 | Full suite green after the two app fixes (no assertion weakened, AGENTS.md rule 4). |

Selector notes: the contact page's reach-out form shares placeholders with the booking widget
(`Full name`, `you@example.com`) → widget fills are scoped to the `Book in 3 Steps` container; the
scheduled card's "Send confirmation message" button collides on `Confirm`/`Pay` accessible names →
`exact: true` + overlay scoping.

## Files Changed

- `tests/e2e/revenue-path.spec.ts` — new 5-step serial smoke.
- `playwright.config.ts`, `vite.config.ts`, `package.json` (`build:e2e`, `e2e`, devDeps),
  `src/lib/db.e2e.server.ts`, `src/lib/db.schema.server.ts` — harness.
- `src/lib/permissions.ts` / `permissions.server.ts`, `src/routes/admin/finance.tsx`,
  `src/routes/admin/dashboard.tsx` — client-graph-safe permission helpers (imports that previously
  pulled a `*.server.ts` chunk into the client graph).
- `src/components/leads/PipelineBoard.tsx` — `mutateAsync` fix (invoice side-effect runs).
- `src/lib/api/billing.server.ts` — `getInvoices` decrypts `lead_name` + `lead_phone`.
- Docs: this sprint doc, `docs/release-readiness.md` (row #72 → PASS), `docs/db-contracts.md`
  (invoices PII read-back note), `docs/evidence/2026-08-28_tier3_e2e_smoke.md`,
  `docs/sprint-cross-reference.md`, `CHANGELOG.md`.

## Status

- [x] 5/5 Playwright E2E green (`npm run e2e`, ~55s)
- [x] Invoice auto-generation on checked-in conversion un-silenced (mutateAsync)
- [x] Billing ledger shows decrypted customer names
- [x] 730 unit tests / 69 files green, `tsc --noEmit` exit 0, ESLint 0 errors on touched files
- [x] release-readiness row #72 → **PASS**

## Owner Follow-ups

- Drag-and-drop rollback toasts in the pipeline still use `mutate`-options; migrate to
  `mutateAsync` for parity (already safe — rollback fires on hook-level `onError`).
- The dev server remains unusable as an E2E target due to the pre-existing TanStack
  import-protection denial (`@tanstack/react-start/server` from `routes/admin/finance` →
  `permissions.server` → `session.server:67` `getCookie`). The production-build harness sidesteps
  it; a real fix would restructure `permissions.server` to not re-export node-bound session code
  into the route graph.