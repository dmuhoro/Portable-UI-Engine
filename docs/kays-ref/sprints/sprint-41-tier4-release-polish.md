# Sprint 41 — Tier 4 Release Polish (Doc Accuracy + Public Contact Intake)

**Theme:** Clear the last pre-pilot hygiene items: make the required reading accurate
(`docs/architecture.md` gaps table was stale; `docs/current-state.md` did not exist) and replace
the decorative "Send us a message" form with a **real, tenant-scoped, anonymous** lead path.

**Result: 743 unit tests green (70 files), 5/5 Playwright E2E green, `tsc --noEmit` exit 0,
ESLint 0 errors on touched files, production build OK.**

## Summary

| Before | After |
|--------|-------|
| `docs/architecture.md` Known Gaps table claimed "No CI pipeline" and "No rate limiting on `login()`" were open; header claimed "verified as of Sprint 34". `docs/current-state.md` — referenced by AGENTS.md rule 6 — did not exist. | Gaps table refreshed against `src/`: both resolved rows are marked Resolved with evidence, the four still-true gaps are kept (config.server.ts Zod bypass, no CSRF headers, unscoped `processQueue` default mitigated at the call site, `registerOrganization` idempotency race). Header reads "Sprint 41", CI/CD row corrected, `registration.server.ts` one-liner fixed. `docs/current-state.md` created as the orientation + ASPIRATIONAL-rules doc. |
| Public contact form was decorative: `submit` toasted and cleared, nothing persisted. | `src/routes/contact.tsx` calls `submitContactMessage` (useMutation); every result is surfaced to the user, failures never silently drop or clear the form. |
| Genuinely anonymous visitors could not write a lead at all — `submitLead` requires `requireOrg()` (session cookie) and unauthenticated packets were parked in `localStorage` until the next session. | New `src/lib/api/contact.server.ts` public intake resolves the public org by slug fail-closed, rate-limits per email, encrypts PII (ADR-015), writes a pipeline-ready lead (`status='new'`, `channel='web_form'`), and fires the full side-effect set (interaction row, `lead:acquired` SSE event, audit, staff notification). |

## Part 1 — Item 10, documentation accuracy

- **`docs/architecture.md`**: gaps table rebuilt with a verify-on-source contract; the two stale
  rows are resolved with citations (`.github/workflows/ci.yml` runs `npm ci && npm test` on
  push/PR to main; `auth.server.ts:114` `checkRateLimit(login:*`, 5/60s)). `registration.server.ts`
  one-liner no longer claims a "12 MEDICAL_SERVICES single transaction" insert. Section 8 CI/CD
  row, Section 10 totals (634/54 → 743/70), and the "as of Sprint" date were all brought current.
- **`docs/current-state.md`** (new): the orientation doc AGENTS.md rule 6 already required —
  run/verify commands, the public lead-path reality, security posture (including the honest
  `ingestInboundLead` plaintext-PII inconsistency), and the **ASPIRATIONAL** list (WhatsApp live,
  M-Pesa live, Daraja STK, paywall UI, live deploy, Google auto-submit).

## Part 2 — Item 11, public contact intake

`src/lib/api/contact.server.ts`:
- `submitContactMessage` createServerFn (POST, Zod input) delegates to `ingestContactMessage`,
  the exported core the tests drive — the RPC wrapper is a one-line delegate, so the 13 tests
  exercise the **real** path.
- **Fail-closed tenant resolution**: `SELECT id FROM organizations WHERE slug = $1` with
  `PUBLIC_ORG_SLUG || "kays-wellness"`. No row → `{status:"unavailable"}`, logged, **no write**.
- **Rate limit**: `checkRateLimit(contact:<email>, 5, 60_000)` → `{status:"rate_limited"}`,
  INSERT never fires.
- **Encryption**: `name`/`email` via `encryptFields` (ADR-015). Tests assert encrypted values in
  the INSERT params and plaintext absent.
- **Payload**: `status='new'`, `channel='web_form'`, `service='Contact Message'`, message body in
  `raw_payload` (no message column exists), plus a `lead_interactions` `new` row, `lead:acquired`
  publish, `LEAD_INGESTED` audit, and staff notification enqueue.

## Part 3 — Test evidence

| File | Kind | Count | What it proves |
|------|------|-------|----------------|
| `src/__tests__/contact-message.test.ts` | Vitest (real core fn) | 13 | Schema rules (empty/whitespace name, bad email, empty/4000+ message cap); INSERT bound to the resolved org with encrypted PII (plaintext absent) and message in `raw_payload`; side effects fire (`lead:acquired`, audit, enqueue, interaction row); fail-closed proofs: missing org → `unavailable` with exactly one query, DB down → `db_unavailable` with `getDb` never called, rate-limit → `rate_limited` with the INSERT never fired |
| `npm test` / `tsc --noEmit` / ESLint | unit | 743/70 | Full suite green after the feature (one new test file; no assertion weakened — AGENTS rule 4) |
| `npm run e2e` | Playwright (prod build + PGlite) | 5/5 | Existing revenue-path smoke still green with the new public intake in the client graph |

## Files Changed

- `docs/architecture.md`, `docs/current-state.md` (new) — item 10 accuracy fix + orientation doc.
- `src/lib/api/contact.server.ts` (new), `src/routes/contact.tsx` — item 11 public intake + wiring.
- `src/__tests__/contact-message.test.ts` (new) — 13 tests proving the real path.
- `docs/db-contracts.md` (clinic_leads/lead_interactions writers + public-intake contract — AGENTS
  rule 2), `docs/release-readiness.md` (rows #78, #79 → **PASS**), this sprint doc,
  `docs/sprint-cross-reference.md`, `CHANGELOG.md`.

## Status

- [x] Item 10: `architecture.md` gaps table accurate against `src/`; `current-state.md` exists
- [x] Item 11: contact form persists a real, encrypted, rate-limited tenant-scoped lead
- [x] 13 new tests, 743 total green; tsc 0; eslint 0; build OK; E2E 5/5
- [x] release-readiness rows #78 + #79 → **PASS**

## Owner Follow-ups

- The booking widget shares the anonym guest's dead end: a cookie-less visitor on `/contact`
  still parks widget packets in `localStorage`. Re-pointing the widget at an anonymous-capable
  server function (or reusing `submitContactMessage`'s tenant-resolution) is the natural next
  step; it is deliberately out of scope for the contact-form item.
- `ingestInboundLead` still writes PII plaintext; a follow-up migrating that marketing intake onto
  `encryptFields` would close the remaining ADR-015 inconsistency (kept out of this change to
  avoid touching the pipeline path mid-smoke).