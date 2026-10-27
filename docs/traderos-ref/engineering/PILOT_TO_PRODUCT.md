# TraderOS — Pilot to Product: Gap Closure Plan (1st & 2nd order)

**Date:** 2026-08-04 · **Supersedes the qualitative gaps only; scores stay in
`GAP_READINESS.md`.** This document splits *what is a prerequisite for a
supervised pilot* from *what makes a real multi-trader product*, and separates
the work we can finish **now** (no trading account, no real order) from the
work that is **account-gated and deliberately left last**.

Method: every task is stated with its first-order goal, the second-order
consequences it *enables or newly requires*, and a precise "done" condition.
First-order thinking asks "what do I get if I do X?"; second-order asks "and
then what becomes possible or necessary?" We use it so the sequence closes each
gap once, in the right order, without gold-plating the pilot.

---

## 0. The hard boundary (estimated truth, verified below)

What counts as account-gated (deferred **last**, per the operator):

- Opening/credentialing any **trading account** at a broker/exchange.
- **Submitting or receiving a real order** through a broker API — live **or** paper.
- Touching real capital.

What is **NOT** account-gated (we can do it now, without a trading account):

- Public, unauthenticated market data (e.g. Binance public klines / WebSocket).
  *This is data, not an account.*
- Free-tier deployment hosts, a real URL + TLS, local/dev Postgres.
- Cloud *infrastructure* credentials (a deploy host's secrets) — these are not
  trading accounts and are fair game.
- All of the engineering, security, data, deployment, observability, and
  governance work below.

> Note: "no trading account" does not mean "no credentials at all." Deploying to
> a host and using a secret manager needs infra credentials. The boundary the
> operator set is about **trading** accounts and **real order execution** — that
> is what is deferred. Everything else is in scope now.

### Verified broker-contact truth (so we never overstate)

| Claim | Status | Evidence |
|---|---|---|
| Connected to a **real Alpaca paper API** and reconciled positions (a read/healthcheck) | **PROVEN once (2026-08-02)** | `docs/evidence/2026-08-02_dry_run_paper_rehearsal.log` — `mode=live paper=true dry_run=True`, `matched_positions 0`, `account_balance 100000.00`, `can_accept_orders True` |
| **Submitted/received a real order** through any broker API (fill, ack, partial) | **NEVER** | `dry_run=True` disabled live execution; the sprint-27 real-paper soak returned NO-GO (no credentials). Every order-path drill uses a simulated/fake broker behind the adapter seam |

So: real connectivity exists once. Real order execution has never happened. The
account-gated phase (last) is therefore a *validation* step, not a discovery
step — but only if the simulated-broker drills stay green forever, which they do
(`sprint27_real_paper_soak.log` fails closed; soak drills run in CI).

---

## 1. Two tracks & the ordering insight

Second-order thinking forces one split before we sequence anything:

- **Track A — Pilot gate** (prerequisite to the real soak and any live pilot).
  Everything a *single* supervised operator needs before touching capital. This
  is the critical path.
- **Track B — Product track** (what makes it a sellable, multi-trader, trusted
  product). Parallel or after A. **Deliberately NOT a pilot gate.**

Why split? First-order: "a product needs users and a UI." Second-order: adding a
user model and a retail UI before the pilot would gold-plate a single-operator
pilot — spending weeks on things that aren't prerequisites to a safe first
capital-touch. The pilot needs a *secured operator API*; it does not need
multi-tenancy. So Track B is real, but it is not on the critical path to the
pilot. This prevents us from marking the product "done" without the pilot ever
happening, and prevents the pilot from being blocked by product gold-plating.

---

## 2. Track A — Pre-account critical path (do now, in this order)

Each item: **Do (1st order) → Then (2nd order) → Done when** and
**breaks-if-skipped**.

### A1. Make the API fail closed (auth default)
- **Do:** No API endpoint is reachable unless an operator/admin key is set;
  refuse to boot with an exposed default. Today `auth.py`/`security.py` are
  fail-*open* with no key configured.
- **Then:** A deployed API is not an open hole; the operator can turn it on.
- **Done when:** `build_app()` refuses to expose live/risk surfaces without
  configured keys; a boot-without-key test asserts fail-closed.
- **Breaks if skipped:** any deployment (A4) is a live vulnerability.

### A2. Wire + harden the real public market-data feed into the daemon
- **Do:** Connect the existing Binance WebSocket streaming engine (currently
  test-only) into the orchestrator; consume real public candles. Add reconnect,
  backfill, stale-timestamp detection, and run the **data-gap breaker against a
  real feed**.
- **Then:** the runtime stops trading on synthetic `MockDataCollector` candles;
  the data-gap breaker finally has a real failure mode (reconnect storms,
  timestamp drift). This is the single biggest step away from "a simulation."
- **Also then (2nd order):** real persisted candles can feed the backtest
  engine → A3 becomes possible; BUT the **frozen oracle candles** the
  conformance tests depend on must be pinned + versioned so real data never
  silently mutates them (dataset-freeze discipline becomes mandatory).
- **Done when:** a ≥24h run on ≥1 symbol shows only real, time-ordered candles;
  forced feed drops recover via reconnect/backfill; the gap-breaker blocks live
  on stale feed and the conformance oracle is unchanged.
- **Breaks if skipped:** we stay a simulation; the trust claim is hollow.

### A3. Real-market cost-adjusted walk-forward (public data, no account)
- **Do:** Run the G-01 walk-forward on ≥1 year of real public candles (Binance
  REST historical), 35% withheld OOS, full costs (fee + slippage + latency).
- **Then:** G-01's evidence upgrades from frozen/synthetic to real markets. The
  honest verdict either (a) shows a cost-adjusted edge → the pilot can claim a
  validated, still-capped expectancy; or (b) confirms **DATA-VALIDATION ONLY** →
  the pilot is honestly a data-collection exercise with no PnL claim. Either
  way the **business** GO/NO-GO crux is resolved before any account exists.
  Also informs which strategies are promoted (the operator currently eyes four).
- **Done when:** a reproducible real-data walk-forward log is committed under
  `docs/evidence/`, with a clear, honest verdict and a frozen dataset pointer.
- **Breaks if skipped:** a pilot would trade an unproven edge on real capital.

### A4. Real deployment
- **Do:** Deploy to a free-tier host (Railway), real URL, TLS, healthz green,
  migrations-on-boot, secrets from a manager, and the daemon supervised.
- **Then:** the product has a reachable, always-on surface; monitoring is real.
- **Also then (2nd order / hard requirements it creates):** REQUIRES A1 (auth),
  A5 (Postgres complete), A6 (secrets) — which is why they precede it. And it
  makes A7 (on-call) meaningful.
- **Done when:** a public URL returns green healthz; a boot applies migrations;
  no secret is in the repo or the container image.
- **Breaks if skipped:** nothing is "runnable for real"; the paper soak (last)
  has no home to run on.

### A5. Postgres completeness
- **Do:** Implement strategy/workflow repos on Postgres (today they degrade to
  in-memory under PG), and standardize migration tooling. Make **PG-backed CI the
  primary path**, SQLite the dev/test path, with parity tests.
- **Then:** the production store is real and multi-process-safe; deployment A4
  has a durable backend that isn't a laptop file.
- **Done when:** `DATABASE_URL=postgres://…` runs the full migrated schema with
  no in-memory fallback for any repo; PG-backed CI is the gating path.
- **Breaks if skipped:** production runs on a single-file SQLite and a restart
  or multi-instance HA is fragile.

### A6. Secret-manager integration + rotation
- **Do:** Live keys live in a secret manager (Vault/KMS-class), injected at
  runtime; rotation rotates a running process; access events feed the existing
  `secret.accessed`/`secret.rotated` audit.
- **Then:** G-04's open exit test (secret manager + rotation) closes **without
  any trading account**.
- **Done when:** key rotation demonstrably reloads a live process; a secret
  access is audit-recorded with redacted values.
- **Breaks if skipped:** live keys in env at a deployed host is how they leak.

### A7. Observability → on-call transport
- **Do:** Route CRITICAL events (unclean death, gap breach, kill trip, secret
  rotation) to ≥1 external transport (webhook/PagerDuty/Slack/SMS) with severity
  routing, beyond today's single-optional-webhook/logs.
- **Then:** an operator is paged, not just logged; alerts become audit evidence.
- **2nd-order prerequisite:** an **unattended** soak (the last phase) is only
  trustworthy if it pages on failure. So A7 is a hard prerequisite for the
  account gate, not a nice-to-have.
- **Done when:** a drill sends a kill to the deployed instance and a CRITICAL
  alert reaches the transport (proven by packet/trace, not by "it printed").
- **Breaks if skipped:** the last-phase soak runs unattended and silent.

> **Track A completion = pilot-gate ready.** At this point, no trading account
> exists and no real order has been placed, but a secured, deployed, real-data,
> real-monitored, single-operator product is standing. The next phase is the
> account-gated validation (§4).

---

## 3. Track B — Product track (parallel or after; NOT a pilot gate)

Real, honest work for "trusted by traders," but not a blocker to the pilot.

- **B1. User/account model:** users, hashed credentials (argon2/bcrypt,
  constant-time compare), sessions with expiry, admin bootstrap via env seed,
  per-user API-key management, fail-closed default. 2nd order: attacker surface
  grows (brute-force → auth rate-limiting; session theft → rotate/expire).
- **B2. Per-user risk rails:** user-dimensioned exposure caps, allowlists,
  kill-switch scoping, and a `user_id` on audit attribution. 2nd order: the risk
  model changes from global to per-trader; governance red-lines extend per user.
- **B3. Retail-facing UI:** onboarding, per-trader view, order-entry (today the
  dashboard is read-heavy operator UI), risk preferences. 2nd order: order-entry
  UX becomes a new order path needing its own guardrails + tests.
- **B4. Attribution/regulator surfacing:** render per-strategy replay PnL and
  the causal chain in the dashboard (today it's a CLI/service result).

Deliberately deferred off the critical path: B gives a *product*; A gives the
*pilot*. We do A first because the pilot gate is the honest first true
milestone and B would otherwise gold-plate it.

---

## 4. Account-gated phase — DO LAST (the boundary the operator set)

These require a trading account and/or real order execution. Order:

- **C1. Real Alpaca paper soak (unattended, 24–72h):** the G-02 exit test.
  Exercises real fills, acks, partial fills, WS resync, reconcile. Expect bugs —
  budget iteration (Sprint 25 found a real one this way). The simulated-broker
  drills stay green so this is validation, not discovery. **Done when:** 0
  reconcile errors, 0 dup/lost across forced disconnects, journal recovery
  replays correctly on the live API, paged on failure (A7).
- **C2. Latency-model calibration:** tune `latency_bps` from real fill→ack
  timings, closing G-01's "latency estimated" caveat.
- **C3. Bounded live pilot:** per `LIVE_RUN_POLICY.md` — symbol + notional caps,
  a hard stop defined *before* launch, human-supervised, operator-acked, and gated
  by A1–A7 + C1. GO requires the walk-forward result (A3) to be understood before
  any claim of edge.

---

## 5. Risks of this plan itself (2nd order on the plan)

- **Gold-plating the pilot:** mitigated by the A/B split — B is not a gating
  milestone.
- **Doing the soak last surfaces a fundamental flaw late:** mitigated because A2
  (real data feed) and the always-green simulated drills exercise the same
  submission path continuously; the soak is a confirmation step, and rework is
  more likely adapter-local than systemic.
- **"No trading account" gets over-read:** clarified in §0 — infra/deploy
  credentials are still needed, just not trading ones.
- **Real-data work (A2/A3) could change behavior the frozen tests pin:** managed
  by mandatory dataset-freeze/version discipline before real candles flow.
- **Scope creep:** each track closes the gap once; done-conditions are explicit
  so we stop at "proven," not at "polished."

---

## 6. What I do next

Start **Track A at A1** (auth fail-closed, the cheapest and security-critical
step), then A2 (real data feed — the highest-value step). Execute one package at
a time, each with a test + committed evidence, exactly as the prior sprints were
delivered, and signal progress before moving on.
