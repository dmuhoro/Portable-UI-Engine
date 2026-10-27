# TraderOS — Test Strategy

The governing principle is not coverage. It is **"no claim of protection
without a check that can fail."** Coverage counts lines; this document is about
whether a test would actually catch the failure it claims to catch.

Authority: `docs/engineering/CONSTITUTION.md` and
`docs/engineering/OPERATIONAL_DOCTRINE_ADDENDUM_2026-10-03.md` (OD-1..OD-16,
governed by OD-15). Where this document and the Constitution disagree, the
Constitution wins.

---

## 1. The five test classes

Every test in this repository belongs to exactly one class. If a test cannot be
placed, it does not belong in the suite.

| Class | Lives in | Proves | May mock |
|---|---|---|---|
| **Unit** | `tests/test_*.py` | One function's logic in isolation | collaborators |
| **Wiring** | `tests/wiring/` | The real boundary composes correctly and a refusal stops real work | only leaf externals (network, clock) |
| **Drill** | `scripts/evidence/` | A named gate (G-xx) fails closed against real wiring | nothing on the rail under test |
| **Integration** | `tests/integration/` | Real adapters over real transports | credentials, declared via env |
| **Contract** | `tests/test_order_contract.py`, `tests/test_repository_contracts.py` | An external system's shape matches what we assume | the external system |

### 1.1 Wiring tests are the load-bearing class

A unit test of a service proves the service works. It does **not** prove
anything is wired to it. Every one of these real-path defects passed unit
tests and reached production:

- `DataIngestionService` produced a `str` timestamp, so the LIVE data-gap
  breaker could never evaluate (B-1, `bb90f1f`).
- `JournaledBroker` keyed idempotency on request shape, so a second emergency
  flatten replayed the first order and never reached the broker (B-2,
  `2bbd4ae`).
- `can_accept_orders` was a one-way latch, so the daemon traded through severe
  reconciliation drift while alerting on it (B-3, `3643453`).
- `assess_trade` defaulted `win_rate=0.5`, and both production callers omitted
  it, so LIVE position sizes were fabricated (`119576a`).

Each is now pinned by `tests/wiring/`. That is the argument for the class.

---

## 2. Rules for a test that counts

A test earns its place only if it satisfies all of these.

### 2.1 Prove the negative

A test that only proves the happy path cannot detect a rail that has stopped
refusing. Every rail test asserts the thing that must **not** happen:

```python
assert broker.submits == 0, "an order escaped while the rail was refusing"
```

The innermost adapter is a spy. Asserting on it proves the refusal propagated
all the way through; asserting on an intermediate mock proves nothing.

### 2.2 Prove the proof

A new regression test is shown to fail without its fix, and the negative result
is recorded. Evidence lives in `docs/evidence/` and is force-added
(`*.log` is gitignored):

```
python3 -m pytest tests/wiring/ -p no:randomly --no-cov -q   # 6 failed
# revert the fix, re-run, record, restore
python3 scripts/ci/check_docs_drift.py                       # 3 real drifts
```

Both B-2 and the win-rate fix had to have **both** halves reverted to
reproduce the original defect. Reverting only the visible half proved nothing
— the first win-rate proof attempt passed with the bug "restored" because the
caller had already been changed. A proof that cannot fail is not a proof.

### 2.3 Never weaken a test to go green

Forbidden, with no exception: raising a threshold, loosening a matcher, adding
`skip`/`xfail`, widening a type, or deleting an assertion. If a test is wrong,
the **test** is wrong and is fixed explicitly in its own commit with its
reason.

The corollary matters: **a pass count never implies a defect is resolved.** In
this repository, tests went `2385 → 2400 → 2408 → 2416 passed` while three
genuine false gates were found and fixed by hand.

### 2.4 Guard against the false gate

A test can pass while the code path it names never executes. Three ways this
happened here, all caught by inspecting *why* a test failed:

1. Stale candles tripped the upstream data-gap breaker, so the cycle refused
   before risk was consulted — the sizing test proved nothing.
2. `_data_ingestion = None` made the loop `continue` on the no-price path, so
   the cycle executor was never reached regardless of the gate.
3. A missing adapter method raised before the order, so "no order placed" was
   true for the wrong reason.

The defence is to **construct the negative deliberately**: make every unrelated
precondition favourable, then confirm the test fails when the rail is removed.
If a test passes for a reason other than the one it names, it is a false gate.

### 2.5 Prove the real path

```bash
# LIVE reachability: the broker spy must be reached on fresh data
python3 -m pytest tests/wiring/test_live_cycle_broker_reachability.py -q

# Refusal paths: the broker spy must NOT be reached
python3 -m pytest tests/wiring/test_reconciliation_blocks_orders.py -q
python3 -m pytest tests/wiring/test_win_rate_provenance.py -q
python3 -m pytest tests/wiring/test_journaled_broker_idempotency.py -q
```

Mocking the service under test is not a shortcut; it is a different test that
proves less.

---

## 3. What is deliberately not covered

Stated plainly, because an unstated exclusion is a hidden claim:

- **Concurrency invariants** under real multi-process contention. HA failover is
  tested at the lease level; it is not tested against clock skew or a real network partition.
- **Numerical convergence** for the O(n) indicator rewrites beyond a stated
  equivalence bound (`1e-12`); there is no property-based suite over 10⁶ paths.
- **The 24–72h unattended soak** (G-02). Operator-credentialed, cannot run in CI.
- **Broker behaviour under our own fault injection** beyond the disconnect
  drill — Alpaca's own retry semantics are trusted, not verified.

None of these is claimed as proven anywhere in `docs/`.

---

## 4. Running the suite

```bash
# Full suite (system python; the pinned .venv lacks pytest in this environment)
PYTHONPATH=src python3 -m pytest --no-cov -q

# With coverage — the release gate
make test-coverage          # fail_under = 100

# Gates that must all be green
python3 -m ruff check src tests scripts
python3 -m black --check src tests scripts
python3 -m isort --check src tests scripts
python3 -m pyright src tests

# Named-gate drills
python3 scripts/evidence/run_ci_drills.py
python3 scripts/governance/live_gate.py
python3 scripts/ci/check_docs_drift.py
```

`-p no:randomly` is used when reproducing evidence so ordering is deterministic.

Current baseline: **2416 passed, 7 skipped** (7 skips are credential/network
gated and listed in §3). Coverage gate: 100%.

---

## 5. Skips are a debt, not a convenience

The 7 skips are acceptable only because each names its blocker and owner
(Vault service absent; Binance WSS endpoint returns 404). A skip without a named
blocker is an undocumented hole. `docs/engineering/GAP_READINESS.md` carries the
current list.

---

## 6. Adding a test

1. Which class (§1)? If none, do not add it.
2. Does it assert the **negative** for a rail (§2.1)?
3. Have you shown it failing without the fix, and recorded that (§2.2)?
4. Have you checked it is not a false gate (§2.4)?
5. Does it exercise the real boundary rather than a helper only tests use?
6. If it documents a rail, does the doc now cite this test (§OD-14)?
