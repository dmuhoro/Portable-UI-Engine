# Evidence — Sprint 40: Tier 3 E2E Smoke (Booking → Triage → Invoice → Payment)

**Date:** 2026-08-28
**Scope:** Full-stack browser smoke against the **production build**, embedded Postgres, two real
bugs found and fixed.

## 1. Playwright run (final)

```
$ npm run e2e
  ✓  1 revenue path smoke › client books an appointment through the contact widget (5s)
  ✓  2 revenue path smoke › contact page booking creates a tenant-scoped lead (6s)
  ✓  3 revenue path smoke › lead reaches the pipeline and is triaged to checked-in (12s)
  ✓  4 revenue path smoke › converted check-in generates an invoice in the ledger (5s)
  ✓  5 revenue path smoke › payment marks the invoice paid with a receipt number (5s)
  5 passed (53.9s)
```

The run boots the production build (`KWC_E2E_DB=1 vite build` → Nitro `node-server`) served by Node
on port 8080 and drives real Chrome. No test fixture or app process was mocked.

Intermediate iterations all passed once the real bugs were fixed; earlier failures were the bug
manifestations (below), not assertion defects.

## 2. Real bugs found by the smoke (all fixed)

### Bug A — converted check-in silently skipped invoice generation
- Observed: lead reached `converted` in the DB-backed pipeline; `invoices` table stayed empty; the
  finance page returned `{"status":"ok","invoices":[]}`.
- Root cause: `LeadCard.safeUpdate` passed `onSuccess`/`onError` as `mutate(variables, options)`.
  The installed React Query build returns `undefined` from `mutate` (its wrapper swallows the
  promise), so those callbacks never ran and the invoice call was a fire-and-forget `.catch(() => {})`.
- Fix: use `mutateAsync` and chain on the promise (`PipelineBoard.tsx`).
- Proof: after the fix the invoice RPC fires and the DB row appears (`INV-2026-00001`, `issued`,
  amount 2500) — asserted by E2E test #4.

### Bug B — billing ledger rendered encrypted lead-name blobs
- Observed: ledger rows showed `ENC:{iv:...}` for the customer name (the E2E `hasText` assert on
  the client name failed).
- Root cause: `getInvoices` decrypted `lead_phone` but not `lead_name`.
- Fix: decrypt both in `getInvoices`, same `decryptFields` read path used by
  `forecasting.server.ts` / `exports.server.ts` (`billing.server.ts`).
- Proof: E2E test #4 asserts the row contains the client's plaintext name.

## 3. Unit suite (unchanged strength)

`npm test` → **730 passing / 69 files** (18.4s). `npx tsc --noEmit` → exit 0.
ESLint on touched files → 0 errors (1 pre-existing hook-deps warning).

## 4. Sanity / hygiene

- `KWC_E2E_DB` is only ever set for the E2E build webServer; production builds use the `vercel`
  preset and real Postgres (grep-verified: no `KWC_E2E_DB` in any prod path).
- No dependencies added that an existing dependency could cover (PGlite is a new devDep for the
  embedded DB; Playwright + `@playwright/test` + `playwright` chrome already on the team stack).
- No existing test weakened or removed.

## 5. Artifacts

- Spec: `tests/e2e/revenue-path.spec.ts`
- Harness: `playwright.config.ts`, `vite.config.ts`, `src/lib/db.e2e.server.ts`,
  `src/lib/db.schema.server.ts`
- Fixes: `src/components/leads/PipelineBoard.tsx`, `src/lib/api/billing.server.ts`
- Docs: `docs/sprints/sprint-40-tier3-e2e-smoke.md`, `docs/release-readiness.md` (row #72),
  `docs/db-contracts.md`, `docs/sprint-cross-reference.md`, `CHANGELOG.md`