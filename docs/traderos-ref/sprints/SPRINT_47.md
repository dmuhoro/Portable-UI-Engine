# Sprint 47 — Launch-prep: transient-broker-error hardening, rotation cadence, pilot charter

**Period:** 2026-08-23
**Objective:** Execute the launch-prep plan (Priorities 1–3) while the G-02
soak window finishes — fix the batch-005 defect the soak surfaced, prepare the
G-04 managed-instance items, and make the pilot charter launch-ready. G-01/
G-02 remain untouched (running/open on their own timeline).

---

## Soak region confirmation

- The operator moved `traderos-soak` US → **EU**: `railway service list`
  reports **region: EU West**; the service was redeployed 2026-08-22T16:46Z
  (new deployment SUCCESS, old REMOVED) and restarted a fresh 72h window at
  16:48Z (batch numbering reset to 001).
- **Batch 005 FAILED** (11:57Z) — Alpaca paper API returned
  `APIError: service temporary unavailable` (503) during the open-orders
  reconcile. Root cause and fix below.

## P1 — Transient-broker-error hardening (DONE)

### Root cause (the batch-005 defect)

`alpaca.common.exceptions.APIError` is a **bare `Exception`** subclass. It was
not in any boundary:
- `retry_with_backoff` retried only `(ValueError, RuntimeError, OSError,
  TimeoutError, ServiceError)`.
- `AlpacaBrokerAdapter` caught `(ValueError, RuntimeError, OSError,
  InfrastructureError, ServiceError)` and the read paths had **no** handling.
- `BrokerStateReconciliationService.reconcile` caught
  `(RuntimeError, ValueError, OSError)`.

So a transient 503 escaped every boundary and **crashed the cycle/daemon**
instead of failing closed. This is exactly what the G-02 soak is for: it
caught a real production-path defect.

### Fix

- `retry_with_backoff` gains a `should_retry` predicate: transient exceptions
  NOT in the base set (e.g. `APIError` with status 429/5xx) are retried with
  backoff; a predicate-false exception propagates immediately (fail fast, a
  permanent 400 must not burn retries).
- `AlpacaBrokerAdapter`:
  - `_is_transient_api_error`: `APIError.status_code in {429, 500, 502, 503,
    504}` → retryable; permanent 4xx → not retried.
  - All submit paths pass `should_retry=_is_transient_api_error` to
    `retry_with_backoff`; all `except` tuples now include `APIError` (dynamic
    `_broker_error_types()`), so a persistent broker error is a clean rejected
    `FillResult`, never a crash.
  - Read paths (`get_account_balance`, `get_positions`, `get_open_orders`)
    convert a persistent broker error to `ServiceError` (surfaced to the
    reconcile, never an uncaught `APIError`).
- `BrokerStateReconciliationService.reconcile` now catches
  `ServiceError`/`InfrastructureError` → BROKER_FAILURE mismatch, orders
  blocked (fail closed), never a crash; the next cycle recovers.

### Evidence

- `scripts/evidence/run_transient_broker_error_drill.py` — 5/5 PASS
  (`docs/evidence/2026-08-23_transient_broker_error_drill.log`): 503 storm on
  the reconcile read fails closed not crash; 429 storm on submit retries then
  clean reject; sustained 429 retries exhaust → rejected; permanent 400 fail
  fast → rejected; reconcile recovers once the storm lifts. Registered in the
  CI credential-free drill set.
- Tests: 6 new adapter `APIError` tests, 3 new `retry_with_backoff` predicate
  tests, 1 new reconcile `ServiceError` fail-closed test.

## P2 — G-04 managed-instance preparation (DONE)

- **Rotation cadence mechanism proven** against a real Vault:
  `scripts/evidence/run_vault_rotation_drill.py` 5/5 PASS
  (`docs/evidence/2026-08-23_vault_rotation_drill.log`): the rotator picks up a
  **changed** KV-v2 secret on `rotate()` (version bump), `rotate_all` counts,
  reads/rotations are value-redacted in the audit, a missing key fails closed.
  Operator steps for a **managed** instance:
  `docs/runbooks/SECRET_ROTATION.md`. Registered in KEY_GATED.
- **On-call live delivery**: the PagerDuty/Slack transport mechanism is already
  proven on the real HTTP wire (`test_oncall_providers.py`, `run_oncall_drill.py`
  6/6). The remaining managed-account delivery is an operator step:
  `docs/runbooks/ONCALL_LIVE_DELIVERY.md` (create accounts, set env, trigger a
  real CRITICAL via kill-switch engage/disengage, confirm delivery + audit +
  metrics).

## P3 — Pilot launch-readiness (DONE)

- **Allowlist (G-03 operator step):** `configs/settings.production.example.yaml`
  now names the fed markets (`BTCUSDT`, `ETHUSDT`) instead of un-fed forex
  (`EURUSD`/`GBPUSD`), with a comment tying the allowlist to the deployed
  feed and to the operator's arming action.
- **Orphaned Postgres volume (Sprint 46 finding):** the exact verification +
  deletion + post-check commands are in `docs/runbooks/OPERATIONS.md`
  (operator action; not executed by this sprint).
- **Pilot charter (G-01):** `LIVE_RUN_POLICY.md` §6 rewritten as a definitive
  DATA-VALIDATION-ONLY charter — fixed symbol set, per-order/gross/daily-loss/
  position caps, dollar-loss + calendar + kill-zero hard stops defined before
  launch, supervision cadence, no-PnL-claim posture, and the escalation
  condition to an edge-seeking pilot.

## Verification

| Check | Result |
|---|---|
| Transient-broker-error drill | **5/5 PASS** |
| Vault rotation drill (real Vault) | **5/5 PASS** |
| `test_alpaca_broker.py` | 41 passed (6 new APIError tests) |
| `test_retry.py` | 8 passed (3 new predicate tests) |
| `test_broker_state_reconciliation.py` | 19 passed (1 new ServiceError fail-closed test) |
| P1 slice (retry+alpaca+reconcile+daemon+cycle) | 131 passed |
| ruff / black / isort / pyright | clean |

## Honest residuals

- Batch 005 itself was a **transient Alpaca outage**, not a data-integrity
  issue; the fix makes the process survive such outages fail-closed. The soak
  window continues; the operator must confirm every remaining batch (incl. a
  re-check of the 005 window) is green for the G-02 verdict.
- The managed Vault/KMS and live PagerDuty/Slack runs remain **operator-run**
  (need managed credentials) — the mechanism is proven; only the managed
  instance is left.
- The orphaned `postgres-volume` deletion is documented, not executed (operator
  action).
