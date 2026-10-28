# KWC Engineering Constitution

> The non-negotiable operating rules for every task in the Kay's Wellness Centre engine.
> This document is the highest-authority engineering governance. It overrides convenience,
> speed, and scope-creep in favour of correctness. Conflicts with any other doc resolve here.

---

## Article I — Execution-Safety Guarantees

1. **Never let code claim a protection it does not actually provide.** False confidence is worse
   than no protection. If an "evidence" gate, grep, or test can pass while the real production path
   stays unguarded, the work is not done.
2. **Enforcement goes at the real boundary.** Before wiring any guard into the money/patient path,
   read the actual code and find the true submission path (e.g. where `bookSlot`, `recordPayment`,
   `sendWhatsApp`, or a webhook handler runs in the live flow). Insert protection there, not in a
   shared helper only the backtest/paper path uses.
3. **Fail closed, never fail open.** Defaults must refuse, not silently allow. When unsure, choose
   the conservative cap.
4. **Proof must exercise the real path.** A unit test of a standalone service does not prove wiring.
   Tests must assert that the actual production function is invoked (or refused) on the real path.
5. **Say no early, loudly.** If a plan has a flaw (wrong insertion point, false gate, scope that
   contradicts its own constraints), say so explicitly and propose the corrected version before
   executing.
6. **No silent drops.** Rejections are explicit: caller gets a clear reason, an audit record, and a
   metric.

---

## Article II — Tenant Isolation (The Highest-Priority Invariant)

1. Every `createServerFn` handler must call `requireOrg()` and bind the returned `orgId` in **every**
   SQL query that touches tenant-scoped data. There is no automatic scoping — this is manual by design (D7).
2. A cross-tenant read or write is a **P0 defect** regardless of environment or who introduced it.
3. Tenant-scoping changes to any `*.server.ts` file MUST be accompanied by a `docs/db-contracts.md`
   update in the same change (AGENTS.md rule 2).
4. New tables MUST be `organization_id`-scoped. The `tenant_id` pattern on `notification_queue`,
   `audit_logs`, and `live_events` is a known inconsistency (documented in db-contracts.md); do not
   replicate it in new tables.

---

## Article III — Money Integrity

1. Every payment path must be idempotent. A replayed webhook/callback must not create a second payment.
2. Every invoice/payment sequence number is minted under `getConcurrentLock()`. Never mint outside a lock.
3. Invoice status transitions are `draft → issued → paid → void`. A paid invoice is never re-opened by
   a payment path.
4. M-Pesa callbacks must be authenticated (callback secret), matched by `CheckoutRequestID`, and
   written through the same `recordPayment`/`reconcilePayment` locks used by manual entry.
5. A rejected or failed payment is logged to `reconciliation_log`/`payments` with a clear status. No silent drops.

---

## Article IV — Security

1. Secrets (API tokens, consumer keys, passkeys, database URLs) live in environment variables or a
   secret manager. **Never commit secrets to the repository.**
2. `SESSION_SECRET` must never be the default value in production (app refuses to boot — enforced by
   `env-production-guard.test.ts`).
3. All auth is server-side. Client-side role checks are UI cosmetics only (D8).
4. PII encryption: when a field is marked encrypted, the write path encrypts before insert and the
   read path decrypts before returning. `ENC:`-prefixed values are the canonical ciphertext marker.
5. Rate limits are enforced at the boundary for: login, lead submission, WhatsApp dispatch,
   reconciliation, and any new money path.

---

## Article V — Testing

1. The test suite must pass (all green) before any push. `npm test`.
2. Production code ships with tests for: money paths (billing, STK push, reconciliation),
   tenant isolation (adversarial), RBAC gates, and idempotency.
3. A test that asserts current behavior as "proof a bug exists" is a diagnostic artifact. Either fix
   the bug and update the test, or mark `xfail`/`skip` with a linked issue (AGENTS.md rule 9).
4. Never weaken an existing assertion to make a build pass (AGENTS.md rule 4).
5. New `*.server.ts` functions touching leads, scheduling, or notifications MUST include tests in
   `src/__tests__/` (AGENTS.md rule 3).

---

## Article VI — Process

1. Work sequentially in layers. Finish one layer (code + tests + docs) before starting the next.
2. Every task is committed individually with an explicit message stating what changed and which doc
   (if any) needs a corresponding update (AGENTS.md rule 7).
3. All commits are SSH-signed (`commit.gpgsign=true`, `gpg.format ssh`). A missing signature is an
   invalid commit (AGENTS.md rule 10).
4. New dependencies require justification against existing packages (AGENTS.md rule 5).
5. `src/routeTree.gen.ts` is auto-generated — never edit directly (AGENTS.md rule 1).
6. Read `docs/current-state.md` (when it exists) and `docs/architecture.md` before starting a task.
   If a task assumes a capability marked **ASPIRATIONAL**, stop and say so (AGENTS.md rule 6).
7. Feature freeze: no new subsystem (payments, encryption, RBAC, external webhooks) while any P0 from
   `docs/db-contracts.md` or `docs/release-readiness.md` is open (AGENTS.md rule 8).
8. Honesty over optimism: report gaps accurately. Closing one gap never means "risk is complete."

---

## Article VII — Evidence

1. Every release/verification produces an evidence file under `docs/evidence/` (or a referenced log).
2. A "PASS" in release-readiness requires a cited test or a cited manual verification step — never
   narrative alone.
3. Live-system verification (WhatsApp, M-Pesa, SSE) is recorded as an evidence log with the date,
   the exact command/step, and the observed result.

---

## Article VIII — Pareto Execution

1. When closing a gap, identify the 20% of work that produces 80% of the value and execute that first.
2. Value ordering for pilot-readiness: money-path integrity → live-channel verification → tenant
   isolation → core clinic workflows → polish.
3. Descoped items are descoped deliberately and documented (see decisions.md). Do not silently
   re-include them; re-include only by an explicit decision.

---

*Constitution effective as of the pilot-hardening sprint. Any amendment is an edit to this document
accompanied by a decision entry.*