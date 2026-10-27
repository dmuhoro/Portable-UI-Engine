# Evidence — Sprint 41: Tier 4 Release Polish (Doc Accuracy + Public Contact Intake)

**Date:** 2026-08-28
**Scope:** Items 10 (accurate required-reading docs) and 11 (real public contact intake on the
marketing site).

## 1. Item 10 — doc accuracy (verified against `src/`)

- `docs/architecture.md` gaps table: two previously-listed gaps are **resolved**, with evidence:
  CI exists (`.github/workflows/ci.yml`, `npm ci && npm test` on push/PR to main) and login is
  rate-limited (`auth.server.ts:114` `checkRateLimit(login:${email}, 5, 60_000)`). The four
  still-true gaps were re-verified: `config.server.ts:19-25` (Zod bypass, Low), no Origin /
  Sec-Fetch-Site header enforcement on any server fn (Low), `processQueue` unscoped default branch
  `queue.server.ts:202-240` still present but call-site mitigated (Low), `registerOrganization`
  pre-check race `registration.server.ts:39-55` (Low).
- `docs/current-state.md` created (AGENTS.md rule 6).
- grep-verified: no `Sec-Fetch`/`Origin` header checks exist → CSRF row stays open.

## 2. Item 11 — public contact intake, real-path proofs

Run (final):

```
$ npx vitest run src/__tests__/contact-message.test.ts
  Test Files  1 passed (1)
  Tests       13 passed (13)
```

The 13 tests execute `ingestContactMessage` — the exact function the `createServerFn` RPC wrapper
delegates to — with mocked `db.server`/`encryption.server`/`rate-limit.server`:
- INSERT params carry `ENC:`-prefixed PII; plaintext `Jane`/`jane@example.com` absent; orgId bound
  to the resolved public org (`kays-wellness` row), not client input.
- Fail-closed: org row missing → `{status:"unavailable"}`, exactly one query ran, zero INSERTs;
  DB unavailable → `{status:"db_unavailable"}`, `getDb` never called; rate limit → `{status:
  "rate_limited"}`, INSERT never fired.
- Side effects: `lead:acquired` published, `LEAD_INGESTED` audited, notification enqueued,
  `lead_interactions` `new` row recorded.

Browser smoke (upstream Tier 3 suite, still green with the new client path):

```
$ npm run e2e
  ✓ client books an appointment through the contact widget (4.8s)
  ✓ contact page booking creates a tenant-scoped lead (8.0s)
  ✓ lead reaches the pipeline and is triaged to checked-in (2.5s)
  ✓ converted check-in generates an invoice in the ledger (573ms)
  ✓ payment marks the invoice paid with a receipt number (1.8s)
  5 passed
```

## 3. Full suite

`npm test` → **743 passing / 70 files**. `npx tsc --noEmit` → exit 0. ESLint on touched files →
0 errors. `npm run build` (production) → OK.

## 4. Sanity / hygiene

- No new dependency (AGENTS rule 5) — reuses `encryptFields`, `checkRateLimit`,
  `enqueueNotification`, `recordAudit`, `publishEvent`.
- No existing test weakened or removed (AGENTS rule 4).
- Tenant-scoping doc updated in the same change as the new org-scoped writes (AGENTS rule 2):
  `docs/db-contracts.md` gains `api/contact.server.ts` as a `clinic_leads`/`lead_interactions`
  writer and a "Public (anonymous) intake" contract block.
- `KWC_E2E_DB` untouched; production build verified.

## 5. Artifacts

- Feature: `src/lib/api/contact.server.ts`, `src/routes/contact.tsx`
- Tests: `src/__tests__/contact-message.test.ts`
- Docs: `docs/architecture.md`, `docs/current-state.md`, `docs/db-contracts.md`,
  `docs/release-readiness.md` (rows #78/#79), `docs/sprints/sprint-41-tier4-release-polish.md`,
  `docs/sprint-cross-reference.md`, `CHANGELOG.md`