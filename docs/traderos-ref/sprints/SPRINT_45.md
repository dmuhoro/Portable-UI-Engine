# Sprint 45 — WS resync reconciliation: converge the live cache to exchange truth after reconnects

**Period:** 2026-08-22
**Objective:** Close the last engineering-open corner of G-02 flagged in
`GAP_READINESS.md`: *"WS resync vs live API untested"*. Today the stream
service reconnects after transport drops (bounded attempts + backoff,
`market_stream.py::run`) but nothing verifies that the candle cache
converged back to REST/exchange truth — outage-minute candles are missing
(interior gaps) and a candle that was mid-flight when the stream died closes
incomplete.

**Constraint:** zero changes to order-path logic. This is market-data
integrity only.

---

## Dependency-ordered plan

```
L1  Resync hook in StreamingMarketDataService (fires after a successful
    reconnection following >=1 failed attempt) — metered, never raises
    into the run loop
L2  Collector-side reconciliation against the REST backfill collector:
    fill interior gaps from REST klines (exchange truth), replace
    overlapping cached candles that diverge beyond tolerance, meter
    gaps_filled / divergences / failures
L3  Offline tests proving each behavior through the real service+collector
    chain (fake transports, injected REST truth)
L4  LIVE evidence drill against real Binance: connect WS, capture candles,
    force a disconnect, resume, compare cache vs REST klines -> VERDICT log
L5  Docs: GAP_READINESS residual update, CHANGELOG, sprint record
```

## Design decisions

- **REST is authoritative** for fully-closed intervals: Binance klines are
  the exchange's official record; WS-derived candles are aggregations of
  aggTrades and may differ microscopically when frames are missed. Replaced
  divergent candles are counted, never silently kept or silently swapped.
- **Tolerance, not exact equality**: divergence threshold is relative
  (`reconcile_tolerance_bps`, default 5 bps) because aggTrade aggregation vs
  official klines legitimately differs in the last decimals.
- **Fail-safe reconciliation**: any error inside the reconcile step is
  recorded as a failure counter and swallowed — the stream must never die
  because reconciliation failed; staleness/gap safety remains owned by the
  G-03 data-gap breaker as before.
- **Bounded work**: reconcile fetches only the outage window (last cached
  candle timestamp -> now) and runs synchronously once per reconnect, before
  tick consumption resumes — no concurrent snapshot mutation, no unbounded
  REST fan-out.

## Exit test

A forced disconnect on the LIVE Binance stream followed by automatic
reconnect leaves the collector's served candles **gapless over the outage
window and matching REST klines within tolerance**, proven by a committed
evidence log with a machine-checkable VERDICT line.

---

## Completion record (2026-08-22)

### L1 — Resync hook + silent-exhaust outage fix (DONE)

- `StreamingMarketDataService` gains optional `on_reconnect` callback +
  `resync_count` counter (`market_stream.py`).
- The hook fires **after** the first successfully ingested frame following ≥1
  failed attempt, so the interrupted pre-outage candle is closed first.
- Callback is wrapped in `try/except` — swallowed + counted, never fatal to
  the run loop.
- **Bonus defect found and fixed:** a connection that produces zero frames
  (proxy black-hole) previously respun forever. Now `frames_this_connection ==
  0` raises `ConnectionError` → bounded exponential backoff.
- The collector binds `stream.on_reconnect = self.handle_reconnect`.

### L2 — Collector reconciliation + mop-up (DONE)

- `handle_reconnect()`: reconciles the live cache against Binance REST klines
  (via the REST backfill collector) — fills interior gaps, replaces divergent
  candles beyond `reconcile_tolerance_bps` (default 5 bps), excludes
  still-forming klines.
- Meters: `reconcile_gaps_filled`, `reconcile_divergences`,
  `reconcile_failures` (+ `resyncs` from the service counter).
- **Mop-up pass:** a one-shot reconcile at the reconnect instant is not enough
  — the damaged candle's official kline is not mature at the exchange yet, so
  it gets excluded and never verified. A rate-limited mop-up (2× interval
  window after reconnect, at most once per interval) re-reconciles on the next
  candle-close event, once truth has matured.
- Mop-up reconcile runs outside the collector lock; failures are metered and
  swallowed (stream keeps flowing).

### L3 — Offline tests (DONE)

- `tests/test_ws_resync_reconcile.py` (23 tests): reconnect hook ordering,
  silent-exhaust detection, gap fill, divergence replacement, tolerance
  retention, metered failures, mop-up late-maturation verify, mop-up rate
  limiting, no mop-up outside window, mop-up reconcile failure swallowed.

### L4 — LIVE evidence drill (DONE, VERDICT PASS)

- `scripts/evidence/run_ws_resync_drill.py` (real Binance WS + REST).
- Forced 3 real websocket outages on the wire.
- **Finding during first run (FAIL):** reconcile fired once at reconnect
  instant; the damaged candle's official kline was not yet mature → excluded →
  never verified. Root cause confirmed: 631 bps volume divergence on the
  outage minute. → mop-up fix (L2).
- **Second run (PASS):** `resyncs=2, gaps_filled=0, divergences=1, failures=0`
  — the incomplete post-outage candle was detected and healed by the mop-up
  pass once its kline matured; final convergence **gapless** and every cached
  candle matching its official kline within tolerance.
- Evidence: `docs/evidence/2026-08-22_ws_resync_drill.log` (VERDICT: PASS).

### L5 — Docs (DONE)

- `GAP_READINESS.md` G-02 row updated (resync residual closed, score kept at
  80→85 with the soak window still the open operator gate), honesty note added.
- `CHANGELOG.md` Sprint 45 block appended.
- This record.

## Verification

| Check | Result |
|---|---|
| `pytest tests/test_ws_resync_reconcile.py` | 23 passed |
| Full suite (`make test`) | **2293 passed / 7 skipped / 100.00% coverage** |
| `ruff check src/ tests/ scripts/` | clean |
| `black --check` touched files | clean |
| `pyright` on touched modules | clean |
| Live drill (`run_ws_resync_drill.py`) | **VERDICT PASS** |

## Honest residuals

- Mop-up coverage depends on candle-close events while the window is open; if
  the feed stays silent after reconnect, G-03's data-gap breaker (unchanged)
  remains the backstop.
- The G-02 **72h soak window** (traderos-soak, ends ~2026-08-25T07:56Z) is
  still running and is the operator-run gate — Sprint 45 closes the resync
  residual only, not the soak.
- G-01's real-edge proof remains open (data-validation-only pilot).
