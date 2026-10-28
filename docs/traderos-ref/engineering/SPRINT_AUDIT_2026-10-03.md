# TraderOS — Engineering Audit & Sprint Plan

**Audit date:** 2026-10-03 · **Branch:** `main` · **HEAD:** `07a7a1f` · **Tag:** `v1.3.3`
**Method:** every claim below is derived from code read at the cited `file:line`, from a
command executed in this repo, or from a log committed under `docs/evidence/`. Nothing is
estimated. Where a measurement could not be taken, the gap is named as a gap rather than
filled with a plausible number.

**Reproduce every number in this document:**

```bash
cd TraderOS
PYTHONPATH=src python3 -m pytest --tb=short -q --no-cov -rA          # 2. Phase 2.4
PYTHONPATH=src python3 -m pytest --tb=short -q -p no:cacheprovider    # 2. Phase 2.4 + coverage gate
ruff check . && black --check . && isort --check . && pyright         # 2. Phase 2.4
PYTHONPATH=src python3 /tmp/opencode/trader-audit/profile_hotpaths.py # 2. Phase 2.1 (see 2.1.6)
python3 -m vulture src scripts --min-confidence 60                    # 2. Phase 2.5
```

> **D-1 — Environment caveat.** `.venv/` in this checkout does not contain `pytest`. All
> measurements below were taken with the system `python3` (3.14.4) and `PYTHONPATH=src`.
> Two dependency pins are violated by that interpreter and the measurements inherit it:
> `alpaca-py` **0.43.5** installed vs `0.30.0` pinned, `uvicorn` **0.51.0** installed vs
> `0.29.0` pinned. Neither is on the hot path profiled in 2.1 (the profile uses the in-memory
> broker and collector), but the suite result in 2.4 is *not* proof that the pinned environment
> is green. Closed by **3.6**.

---

## Phase 1 — In-flight work state

### 1.1 What actually landed

`git log` on `main`, newest first (release chain reconstructed):

| Commit | Meaning |
|---|---|
| `07a7a1f` | Frontend: Vercel static deploy config for the dashboard (L1). **After** `v1.3.3` — not in any release. |
| `4286171` / `acc30e4` | Release `v1.3.3` (signed tag). Honest deployment of the soak harness. |
| `98c3b5a` | Sprint 50: soak timing — fresh window per attempt. |
| `e3d18d4` | Sprint 50: checkpoint is not resumable across a change of *harness*. |
| `b65cf3c` / `8995054` | Release `v1.3.2` + G-02 soak position close-out. |
| `6b6d557` | Corrected a stale doc that still called G-02 "running" after it had ended CRASHED. |

Sprint 50's stated objective — close the soak harness's position leak — is **landed and
released**: the position-flatten harness (`docs/evidence/2026-10-01_soak_position_flatten_live.log`,
10 cycles, `still_resting=0`, `mismatches=0`, submit→ack median 307.3 ms), the account reset,
and the independent flatness check at t+0/+60/+120/+180s are all committed and cited in
`docs/engineering/GAP_READINESS.md:23`.

`configs/settings.yaml:4` and `configs/settings.production.example.yaml:17` both read
`version: "1.3.3"`, matching `pyproject.toml:3`. **Version bookkeeping is consistent in the
source tree.**

### 1.2 What is still open

| # | Open item | Owner | Source |
|---|---|---|---|
| 1 | The **continuous 24–72h unattended Alpaca-paper window** — the actual G-02 exit test — has never completed. Bounded runs pass; the window is operator-run and unwatched. | **Operator** | `GAP_READINESS.md:23,36`; `SPRINT_49.md` honest residuals |
| 2 | **G-01 genuine cost-adjusted edge.** All three strategies fail the all-folds-positive criterion on both the frozen oracle and real-market walk-forwards. | Engineer + operator data | `GAP_READINESS.md:22,37` |
| 3 | LIVE `allowed_markets` must be populated with pilot symbols at deploy time. | **Operator** | `GAP_READINESS.md:24,38` |
| 4 | Managed Vault/KMS rotation cadence and a live PagerDuty/Slack delivery to a real account. | **Operator** | `GAP_READINESS.md:25,39` |
| 5 | `07a7a1f` (dashboard deploy config) is unreleased — no version bump, no changelog entry, no tag. | Engineer (release discipline) | `git log` |

### 1.3 Working tree

Thirteen `docs/evidence/*.log` files are modified (observed at audit time; the count grew
during the audit as drill runs were re-executed elsewhere). Every diff inspected is a re-run
`started` timestamp on an unchanged result block. **No result in this audit depends on them, and none were
modified by this audit.**

---

## Phase 2 — Findings

### 2.1 Performance (measured on the real services, not estimated)

Harness: `/tmp/opencode/trader-audit/profile_hotpaths.py`. Real `CycleExecutor`, real
`RiskService`, real `SQLiteAuditService`/`Metrics`/`Health`, real `OrderEventJournal`, real
`DataIngestionService`, real `JournaledBroker`, real `BrokerStateReconciliationService`.
`CountingCollector` subclasses the **real** `MockDataCollector` and reverses its output so
the harness has the production (ascending, Binance-shaped) candle order — see 2.1.7.

#### 2.1.1 The cycle is dominated by synchronous external I/O, not by computation

| Measurement | Median | p95 |
|---|---|---|
| `CycleExecutor.run` (in-memory SQLite, 3 strategies, 2 signals) | **57.8 – 59.7 ms** | **67.7 – 70.7 ms** |
| Same, `LIVE` mode (adds the broker balance call) | 55.2 ms (1 cycle) | — |

In-process work inside that cycle:

| Component | Cost |
|---|---|
| `BreakoutDetectionService.analyze` | **15.93 ms** (27% of the cycle) |
| `compute_atr(14)` | 6.43 ms |
| `compute_bollinger_bands(20,2)` | 6.42 ms |
| `compute_sma(50)` | 4.04 ms |
| `compute_sma(20)` | 2.98 ms |
| `RegimeDetectionService.detect` | 0.001 ms |
| **Indicator total** | **≈ 36.8 ms** |

Every one of those indicators is recomputed from the full 100-candle window on **every
cycle for every market**, at `src/traderos/application/cycle_executor.py:149` — one
`fetch_candles(limit=100)` call, then a full recompute. Between consecutive cycles only the
newest candle changes. **This is the single largest in-process cost and it is almost entirely
redundant work.** The fix is memoization keyed on `(market_id, timeframe, last_candle_timestamp)`,
not a faster indicator.

#### 2.1.2 Two blocking Binance HTTPS round trips per market per cycle

- `src/traderos/infrastructure/collectors/binance_collector.py:32` — `urlopen(url, timeout=10)`
  is **synchronous**, with no connection reuse, no retry, and no circuit breaker.
- `src/traderos/application/daemon_controller.py` calls `get_latest_close(mid)` once per market
  per loop, then `CycleExecutor.run()` calls `fetch_candles()` (`cycle_executor.py:149`), which
  calls `fetch_historical()` again. **Measured: 1.1 collector calls per executor cycle, plus 1
  more per market from the daemon.**

Measured cost of that exact call from this host (`api.binance.com/api/v3/klines`), 3 samples each:

| `limit` | Median |
|---|---|
| 1 | **413.9 ms** |
| 100 | **412.1 ms** |
| 500 | **419.3 ms** |

The latency is **entirely round-trip dominated** — payload size is irrelevant. So per market,
per cycle, the synchronous loop blocks for roughly **0.8 s** across the two calls. At the
paper cadence this is survivable; it is also the mechanism by which a slow or hung exchange
stalls the whole trading loop for up to `timeout=10` per call, with the trading loop unable to
observe the stall.

Production runs the **synchronous** daemon (`src/traderos/interfaces/cli/main.py`, `run`/`daemon`
→ `run_forever`). `build_async_daemon` at `src/traderos/application/factory.py:659` is
referenced only by tests and evidence drills (see 2.5.3). The async path exists and is not wired.

#### 2.1.3 103 SQL statements per cycle, 56% of them transaction control

Traced live via `sqlite3.Connection.set_trace_callback` over one `CycleExecutor.run`:

| Count | Statement |
|---:|---|
| **29** | `BEGIN` |
| **29** | `COMMIT` |
| 8 | `SELECT hash FROM audit_log ORDER BY rowid DESC LIMIT 1` |
| 8 | `INSERT INTO audit_log (...)` |
| **4** | `SELECT * FROM positions WHERE quantity != 0` |
| 2 | `INSERT INTO signals (...)` |
| 2 | `INSERT INTO order_events (...)` |
| 2 | `UPDATE order_events SET status = 'confirmed', ...` |

- **58 of 103 statements (56%) are `BEGIN`/`COMMIT` pairs.** Every single-row write commits
  its own transaction. There is no unit of work around a cycle, so SQLite fsyncs ~29 times per
  cycle. One `BEGIN`/`COMMIT` per cycle would remove ~56 statements and the associated fsyncs.
- **8 hash-chain reads for 8 audit records.** `src/traderos/infrastructure/observability.py`
  reads the tail of `audit_log` to chain each new record. Within one cycle the chain head is
  known; reading it back 8 times is pure waste, and it makes the audit write path
  O(records²) over a cycle.
- **4 full scans of `positions`.** `cycle_executor.py:304` and `:324` each call
  `get_summary()`, once per strategy and once more per signal — **measured 4 `get_summary()`
  calls per cycle**. `PortfolioService.get_summary()` reads open positions with
  `SELECT * FROM positions WHERE quantity != 0`
  (`src/traderos/infrastructure/repositories/sqlite/trades.py:119`), and
  `positions` has **no index at all** — no index on `quantity`, none on `market_id`. A
  long-running paper/live instance accumulates closed positions (quantity → 0), so this is a
  scan whose cost grows without bound and is paid 4× per cycle.

#### 2.1.4 LIVE mode calls the broker for cash once per signal

Measured on one LIVE cycle: **`get_account_balance()` called 2 times**, `place_market_order()`
2 times — one of each per signal, from `cash = self._cash_balance()` at
`cycle_executor.py:342-343` inside the strategy loop. Preflight is likewise re-run per signal
(`cycle_executor.py:296-303` and `:342-349`) although its inputs cannot change mid-cycle.

All three account reads (two balances + `get_summary`) return **the same numbers** for the
same cycle. Hoisting portfolio snapshot, cash balance, and preflight to once-per-cycle is a
mechanical, behaviour-preserving change that removes 2 broker round trips and 3 of the 4
position scans.

#### 2.1.5 Order submission is fast; the *journal* is what costs

| Path | Median | p95 |
|---|---|---|
| `place_market_order`, fresh `client_order_id` | **0.255 ms** | 0.453 ms |
| `place_market_order`, no `client_order_id` | 0.079 ms | 0.159 ms |

Ten SQL statements per submission (3 `BEGIN`/`COMMIT` pairs + `SELECT` + `INSERT` + 2 `UPDATE`).
The 3× gap between the two rows is **not** broker latency — it is the derived-idempotency-key
replay path. See **B-2**: the no-id row is mostly *replays that never reach the broker*, so it
must not be read as "submissions are cheap."

#### 2.1.6 Reconciliation is linear and is not the bottleneck

| Positions / orders | Median | p95 |
|---|---:|---:|
| 10 / 5 | 0.100 ms | 0.215 ms |
| 100 / 50 | 1.546 ms | 2.136 ms |
| 1000 / 500 | 14.322 ms | 20.084 ms |
| 5000 / 2500 | **75.736 ms** | **102.739 ms** |

Clean O(n) with dict indexing — **no N+1 here**, unlike 2.1.3. At the two-symbol pilot scale
this is ~0.1 ms and irrelevant. It becomes a real cost only at thousands of open positions,
which a paper account accumulates. Recorded for completeness; **not** a P1.

#### 2.1.7 One correction to an earlier working assumption

`cycle_executor.py:160` reads the newest candle as `candles[-1]`. This audit checked that
assumption at every collector rather than asserting it:

| Collector | Order returned | `candles[-1]` is |
|---|---|---|
| `MockDataCollector` | newest-first | newest ✓ |
| `BinanceCollector` (`binance_collector.py:38-47`, preserves API order) | oldest-first (**verified against the live API**) | newest ✓ |
| `StreamingMarketDataCollector` (`streaming_collector.py:163` append, `:207` `live[-limit:]`) | oldest-first | newest ✓ |
| `AlpacaCollector` (`alpaca_collector.py:73`, iterates the SDK DataFrame) | oldest-first | newest ✓ |

**There is no candle-ordering bug.** The harness in this audit reverses `MockDataCollector`'s
output purely so the profile exercises the same ascending shape production uses; it is not
compensating for a defect.

### 2.2 Strategies and expectancy

#### 2.2.1 Every strategy implementation, and every subclass

`StrategyBase` is declared at `src/traderos/domain/services/strategy_framework.py:27`.
Repo-wide, exactly **nine** subclasses exist. **Three are production**; six are private
single-purpose fixtures inside `scripts/evidence/`.

| Class | Location | Registered | Live? |
|---|---|---|---|
| `MovingAverageTrend` | `strategy_framework.py:65` | `@registry.register` (`:64`) | **yes** |
| `VolatilityBreakout` | `strategy_framework.py:87` | `@registry.register` (`:86`) | **yes** |
| `MeanReversion` | `strategy_framework.py:107` | `@registry.register` (`:106`) | **yes** |
| `_Strat` | `scripts/evidence/run_paper_soak.py:124` | no | drill fixture |
| `_Strat` | `scripts/evidence/run_real_paper_soak.py:118` | no | drill fixture |
| `_Strat` | `scripts/evidence/run_partial_fill_reconnect.py:136` | no | drill fixture |
| `_Strat` | `scripts/evidence/run_causal_replay.py:93` | no | drill fixture |
| `_Strat` | `scripts/evidence/run_multirestart_replay.py:105` | no | drill fixture |
| `_AlwaysSignal` | `scripts/evidence/run_risk_rails_drill.py:100` | no | drill fixture |

**Decision logic, verbatim:**

- `MovingAverageTrend` — `(sma20 - sma50) / sma50`; long above `+0.02`, short below `-0.02`;
  confidence `min(|ratio| × 10, 1.0)`. **Note: no trend/regime filter, and the confidence is a
  linear function of distance-from-threshold, so a signal 0.021 away scores 0.21 and one 0.10
  away scores 1.00 — confidence saturates at a 10% SMA gap.**
- `VolatilityBreakout` — fires whenever `atr14 / close > 0.02`, direction long iff
  `sma20 > close`. **A volatility *threshold* with no breakout comparison and no lookback
  high/low: it is a volatility filter, not a breakout system.**
- `MeanReversion` — short if `close > bb_upper_20`, long if `close < bb_lower_20`; confidence
  `min(distance × 5, 1.0)`.

#### 2.2.2 All three trade simultaneously, with no cross-strategy coordination

`factory.py:885` `_sync_strategy_registry` inserts **every** registered strategy with
`status='active'`. `cycle_executor.py:233` iterates the whole registry when `_enabled_strategies`
is `None` — the production default. So in every cycle all three strategies evaluate the same
market, and each independently passes the per-order risk gate at `cycle_executor.py:324-351`.
The gross-exposure rail bounds the *total*, but **nothing coordinates correlated entries**: a
flat tape can produce a long from `MovingAverageTrend`, a long from `MeanReversion` (below the
lower band) and a short from `VolatilityBreakout` in the same cycle. Measured: 2 signals and 2
submissions per cycle in the profile. Whether three uncorrelated-looking strategies on one
symbol should be allowed to size independently is an open design question this audit does not
answer — it flags it as unanswered.

#### 2.2.3 Expectancy: no strategy has a demonstrated edge

`docs/evidence/2026-08-04_sprint27_walk_forward_evidence.log:8-21` — frozen oracle dataset,
5 folds, full costs, 35% withheld OOS:

| Strategy | Mean fold result | Folds positive |
|---|---:|---:|
| Moving average trend | 0 | **0 / 5** |
| Volatility breakout | +0.0009 | 3 / 5 |
| Mean reversion | +0.0001 | 3 / 5 |

Line 20 states the verdict: **no strategy meets the all-folds-positive criterion.**

`docs/evidence/2026-08-06_real_market_walk_forward.log:9-21` — real Binance data:

| Strategy | Mean fold | Folds positive | Sharpe | Max DD |
|---|---:|---:|---:|---:|
| Moving average trend | **+25.8237** | **2 / 5** | **−0.1991** | 0.7497 |
| Volatility breakout | −19.9095 | 1 / 5 | 0.1942 | 26.7148 |
| Mean reversion | −0.8408 | 3 / 5 | 0.2246 | 1.1636 |

`MovingAverageTrend` has the only positive mean, and it is **not** positive expectancy: 2/5
folds positive with a **negative** Sharpe means the average is carried by a minority of folds.
Line 20: none pass.

**Conclusion, unchanged from `GAP_READINESS.md:22`:** the *mechanics* are proven; the *edge* is
not. `LIVE_RUN_POLICY.md`'s DATA-VALIDATION-ONLY pilot posture is the correct posture and this
audit does not recommend relaxing it.

### 2.3 User-facing capability inventory

Counted from the live OpenAPI schema, the live argparse tree, and the served dashboard HTML —
not from documentation.

#### 2.3.1 Total

| Surface | Count |
|---|---:|
| HTTP API operations | **58** (across 56 paths; 36 GET, 22 POST, 0 PUT/DELETE/PATCH) |
| CLI leaf commands | **30** (plus 7 group nodes = 37 parser nodes) |
| Dashboard panels | **13** |
| **Total discrete user-facing surfaces** | **101** |

#### 2.3.2 What an operator can actually do — 58 API operations, by capability

| Capability | Ops | Endpoints |
|---|---:|---|
| **Trading control** | 3 | `POST /v1/orchestrator/start`, `POST /v1/orchestrator/stop`, `GET /v1/orchestrator/status` |
| **Risk control** | 4 | `GET /v1/kill-switch`, `POST /v1/kill-switch/engage`, `POST /v1/kill-switch/disengage`, `GET /v1/preflight` |
| **Readiness / health** | 4 | `GET /v1/readiness`, `GET /v1/live/check`, `GET /v1/health`, `GET /v1/healthz` |
| **Positions, orders, trades, portfolio** | 7 | `GET /v1/positions`, `GET /v1/orders`, `GET /v1/trades`, `GET /v1/portfolio`, `GET /v1/pnl`, `GET /v1/equity-curve`, `GET /v1/reports/session` |
| **Attribution / audit** | 2 | `GET /v1/attribution/replay`, `GET /v1/audit` |
| **Backtest / research** | 6 | `POST /v1/backtest`, `GET /v1/backtest/history`, `POST /v1/research/backtest`, `GET /v1/research/indicators`, `GET /v1/research/observations`, `POST /v1/research/observations` |
| **Strategy catalog lifecycle** | 9 | `GET/POST /v1/strategies`, `GET /v1/strategies/{name}`, `GET /v1/strategies/{name}/review`, and `POST` for `enable` / `disable` / `promote` / `archive` / `clone` / `compare` |
| **Market data** | 3 | `GET /v1/market/symbols`, `GET /v1/market/overview`, `GET /v1/market/candles` |
| **Governance workflow** | 2 | `GET /v1/workflow`, `POST /v1/workflow/advance` |
| **Paper trading** | 2 | `POST /v1/papertrade/session`, `GET /v1/papertrade/sessions` |
| **Observability** | 4 | `GET /metrics`, `GET /v1/metrics`, `GET /v1/manifest`, `GET /v1/events` (SSE) + `GET /v1/events/token` |
| **Broker probes** | 2 | `GET /v1/probes`, `GET /v1/probes/broker` |
| **Operator auth** | 3 | `GET /v1/auth/me`, `POST /v1/auth/login`, `POST /v1/auth/logout` |
| **Retail (self-service)** | 5 | `POST /v1/retail/register`, `POST /v1/retail/login`, `POST /v1/retail/logout`, `GET /v1/retail/me`, `POST /v1/retail/orders` |

#### 2.3.3 30 CLI leaf commands

`run`, `status`, `health`, `validate`, `signal`, `strategies`, `backtest`, `notify` (8 top-level)
· `audit query`, `audit verify` (2) · `db migrate`, `db check`, `db backup`, `db restore`,
`db rollback`, `db backup-scheduler`, `db list-backups` (7) · `metrics snapshot`, `metrics watch` (2)
· `papertrade create`, `papertrade list` (2) · `pilot readiness`, `pilot dry-run` (2)
· `risk status`, `risk check`, `risk kill`, `risk reconcile`, `risk reset` (5)
· `security audit` (1)

Sixteen of these take an enumerated `--mode` (backtest/paper/live) or `--source`/
`--timeframe`/`--level`/`--action` — those option values are **not** counted as separate
commands.

#### 2.3.4 13 dashboard panels

`src/traderos/interfaces/api/dashboard/index.html` — workflow, portfolio, risk, ops, positions,
orders, trades, strategies, market, research, attribution, report, events. Served as a static
SPA at `/dashboard` (`server.py:596-601`).

### 2.4 Bugs and test posture

#### 2.4.1 **B-1 — CRITICAL — production LIVE raises `TypeError` on every cycle with market data wired**

Reproduced. Not theoretical.

`DataIngestionService.fetch_latest` stringifies the timestamp at
`src/traderos/domain/services/data_ingestion_service.py:50` (`ts_str = ts.isoformat()`), and
`fetch_candles` assigns that string straight into `Candle(timestamp=r["timestamp"])` at
`:86` — while `Candle.timestamp` is typed `datetime`. Two independent consumers then do
`datetime - str`:

| Consumer | Site | Reproduced error |
|---|---|---|
| G-03 data-gap breaker | `cycle_executor.py:160-161` | `TypeError: unsupported operand type(s) for -: 'datetime.datetime' and 'str'` |
| Risk staleness gate | `cycle_executor.py:351` → `risk_service.py:260-261` | identical `TypeError` |

Reproduction output (real `MockDataCollector`, real `DataIngestionService`):

```
fetch_candles -> last timestamp: str = '2026-10-02T18:17:35.046875+00:00'
G-03 breaker  cycle_executor.py:161 -> TypeError: unsupported operand type(s) for -: 'datetime.datetime' and 'str'
risk gate     risk_service.py:261   -> TypeError: unsupported operand type(s) for -: 'datetime.datetime' and 'str'
```

**Why production reaches it:** `src/traderos/application/factory.py:352-360` registers a data
source per market and `factory.py:544-560` wires `data_ingestion` into the orchestrator, which
builds the executor.

**Why no test caught it — the test that should have.** There is exactly one test named for
this path: `tests/test_cycle_executor.py:492` `test_candles_processed_with_data_ingestion`.
It exercises **none** of the four things that break:

| What the test uses | Consequence |
|---|---|
| `data_ingestion = Mock()` (`:497`) | `fetch_latest`'s `.isoformat()` never runs |
| `timestamp=datetime.now(UTC)` hand-built (`:520`) | the string never reaches a `Candle` |
| `risk_service = Mock()` (`:537`) | the staleness arithmetic never runs |
| `mode=TradingMode.PAPER` (`:556`) | the G-03 breaker at `:156-165` is LIVE-only, so it is skipped |

Compounding this: the risk unit tests pass real `datetime` objects, bypassing
`fetch_latest`; and `scripts/evidence/run_real_paper_soak.py` constructs `CycleExecutor` with
**no** `data_ingestion` argument (verified), so the soak that reported PASS never exercised
this path either.

**Blast radius:** `TypeError` is not in `_CYCLE_EXCEPTIONS`. It escapes to the daemon's outer
handler, which reports unhealthy and — via the fatal rail — can flatten positions and exit.
So the honest severity is not "a crash": it is **"the data-gap safety breaker and the staleness
gate are both inoperable on the LIVE path, and their failure mode is a kill switch."**

**This is a safety control that does not provide the protection it appears to provide.** It is
the single most important finding in this audit.

#### 2.4.2 **B-2 — HIGH — derived idempotency key replays a second flatten instead of submitting it**

`JournaledBroker` derives its idempotency key from the order's own attributes when the caller
supplies no `client_order_id`. Probe result, real `JournaledBroker` + real `OrderEventJournal`:

```
flatten #1 -> filled=True order_id='ord-403'  broker submits=403
flatten #2 -> filled=True order_id='ord-403'  broker submits=403
second call REPLAYED instead of submitting: True
```

Two intentional flatten calls with identical market/side/quantity collapse into one. The
mitigating factor is real and worth stating: the live call path **does** thread a
caller-owned `client_order_id` end-to-end (credited in `GAP_READINESS.md:23`), so the shipped
submit path is not exposed. The exposure is the **API surface** — `POST /v1/retail/orders` and
`POST /v1/orchestrator/*` reach the broker through paths where a caller may omit the id. Either
the derived key must include a disambiguator, or the broker must **fail closed** when no
`client_order_id` is supplied rather than silently deriving one. Fail-open is the wrong default
here and violates the repo's own rule.

#### 2.4.3 **B-3 — HIGH — `can_accept_orders` is a one-way latch; periodic reconciliation failures are discarded**

- `src/traderos/domain/services/broker_state_reconciliation_service.py:85` —
  `can_accept_orders` returns `self._startup_reconciled`.
- `:276` is the **only** write, and it sets the flag `True`. It is never set back to `False`.
- `src/traderos/application/daemon_controller.py:467` —
  `self._run_periodic_reconciliation(*self._fetch_local_state())` — **the returned result is
  discarded.**

Consequence: once the first startup reconciliation succeeds, `can_accept_orders` is `True`
forever, and a later divergence detected by the periodic sweep raises an alert but does **not**
close the gate. `preflight_service.py:58` and `live_readiness.py:143` both consult
`can_accept_orders`, so **both report "reconciled" while a divergence is active.** Sprint 50
already fixed a related latent LIVE defect (reconciliation keyed on the wrong symbol,
`GAP_READINESS.md:23`); this is the same class of fail-open, one layer up, and it is the reason
that fix was not sufficient on its own.

#### 2.4.4 Suite is green — and what that green does and does not mean

```
2364 passed, 7 skipped, 277 warnings in 573.87s
Total coverage: 100.00%   (0 missing of 13,596 statements, fail_under=100 met)
```

| Gate | Result |
|---|---|
| `pytest` | **2364 passed, 7 skipped, 0 failed** |
| Coverage | **100.00%**, 0 / 13,596 statements missing, `fail_under = 100` satisfied (`pyproject.toml:107`) |
| `ruff check .` | All checks passed |
| `black --check .` | 381 files unchanged |
| `isort --check .` | clean (2 skipped) |
| `pyright` (`typeCheckingMode = "strict"`) | **0 errors, 0 warnings** |

**7 skips, every one justified and cross-referenced:**

| Skip | Count | Reason |
|---|---:|---|
| `tests/test_secret_provider_port.py:76,94,117,140,152,165` | 6 | no local HashiCorp Vault instance |
| `tests/test_programme_b_operational_trust.py:801` | 1 | Binance WSS endpoint returns HTTP 404 |

No `xfail`, no `skipif`-hidden assertions, and **zero** `TODO`/`FIXME`/`XXX`/`HACK` markers in
`src/`, `tests/`, or `scripts/`.

**Read the green honestly.** Three things it does not cover:

1. **B-1 is a typing lie.** `pyright --strict` passes *and* `Candle.timestamp` is annotated
   `datetime`, yet a `str` arrives at runtime from `data_ingestion_service.py:86`. The type
   checker is clean because the boundary is untyped (`fetch_latest` returns `list[dict]`), and
   100% line coverage is satisfied because both lines *are* executed — just never with a
   production-wired executor. **Coverage and strict typing both passed on the exact defect that
   breaks LIVE.** This is the clearest evidence that line coverage is the wrong gate for
   integration boundaries.
2. **275 `ResourceWarning: unclosed database` entries across 32 distinct tests** — plus the 2
   third-party deprecations, that accounts exactly for pytest's reported `277 warnings` in the
   `make test` / coverage run. They are **absent from the `--no-cov` run purely because GC
   timing differs without coverage tracing** (`pytest-randomly` is **not** installed, so this is
   not order luck). Leaking sites include `tests/integration/test_api.py::TestApiPaperTrade`,
   `tests/test_cli.py`, `tests/test_auth.py`, `tests/test_operator_api.py`,
   `tests/test_market_research.py`, `tests/test_order_contract.py`. On a long-running daemon —
   or a CI box that runs the suite repeatedly — an unbounded SQLite handle leak is a real
   failure mode, and it means several tests do not actually assert against a clean teardown.
3. The two third-party deprecations are real but third-party:
   `websockets.legacy` deprecated in 14.0, and `starlette.testclient` recommending `httpx2`.

### 2.5 Technical debt

#### 2.5.1 Gap register: six of seven gaps are below 90

`docs/engineering/GAP_READINESS.md:22-28`:

| Gap | Score | Risk | Exit test status |
|---|---:|---|---|
| G-01 Backtest realism | **85** | HIGH | mechanics proven; **edge not demonstrated** |
| G-02 Live order ops | **85** | CRITICAL | bounded runs pass; **the 24–72h window has never completed** |
| G-03 Portfolio risk rails | **85** | HIGH | drill + config + kill surface closed; live symbol set is operator-side |
| G-04 Firm ops (HA/alerting/keys) | **85** | HIGH | drills pass; **managed** Vault/KMS + live on-call account pending |
| G-05 Causal accountability | **85** | MEDIUM | proven across restarts; regulator view closed (WP12) |
| G-06 Test realism / oracle | **90** | MEDIUM | closed (WP13) |
| G-07 Governance | **85** | MEDIUM | proven; Vault integration done |

**Honest reading:** G-05 and G-07 are scored 85 while their own exit tests read "closed".
Per this document's own scoring legend, *the exit test is the only thing that moves the score* —
so those two scores are stale-low, and **G-01/G-02/G-04 are genuinely open.** Do not average
these into a single number; the register's stated purpose is to make GO/NO-GO auditable, and
averaging destroys exactly that.

#### 2.5.2 Documentation drift — three concrete stale claims

| # | Claim | Reality |
|---|---|---|
| 1 | `GAP_READINESS.md:3` — "**Generated:** 2026-08-13 · **HEAD:** `48f28b0` (Sprint 36)" | HEAD is `07a7a1f`; the body text already describes Sprint 50 and `v1.3.3`. The header and its own body disagree. |
| 2 | `GAP_READINESS.md:27` (G-06) — "**2139 tests**, 100% line coverage (0 missing of **12,139** statements)" | **2364 tests, 13,596 statements.** Sprint 35's numbers, presented as current. |
| 3 | `git log` — `07a7a1f` adds Vercel dashboard deploy config **after** the `v1.3.3` tag | Unreleased behaviour change. Violates the repo's own release discipline. |

#### 2.5.3 Dead code — `vulture 2.16`, `src` + `scripts`, `--min-confidence 60`

**Genuinely unreferenced production code** (all verified by hand; no decorator registration,
no framework binding):

| Symbol | Location | Note |
|---|---|---|
| `BrokerPort` | `domain/ports.py:48` | zero references repo-wide |
| `ReconciliationError` | `domain/services/reconciliation_service.py:14` | zero references repo-wide |
| `OrderEventEngine` | `application/order_event_engine.py:35` | superseded by `OrderEventJournal` |
| `DatabaseManager` | `infrastructure/database/db_manager.py:10` | superseded by `connection.py` |
| `LeaderElection`, `FileBasedLeaderElection` | `infrastructure/leader_election.py:15,84` | **the HA failover story in G-04 names `FailoverManager`, not this** |
| `StructuredLogger` | `infrastructure/logging/__init__.py:55` | |
| `DatabaseHealthMonitor` | `infrastructure/monitoring.py:153` | `SQLiteHealthService` is the live path |
| `ResearchEngine` | `domain/research/research_engine.py:9` | `ResearchService` is live |
| `DurableRunManifest` | `infrastructure/run_manifest.py:62` | |
| `VisualizationService` | `infrastructure/visualization.py:28` | |
| `CircuitHalfOpenError` | `infrastructure/resilience.py:39` | |
| 7 domain exception classes | `domain/exceptions.py:9,21,25,33,49,53` (+1) | never raised or caught |
| `build_async_daemon` | `application/factory.py:659` | **tests + drills only — the async daemon is not wired to production** |
| `pooled_connection` | `infrastructure/database/connection.py:295` | |
| `create_cache` | `infrastructure/cache.py:153` | |
| `create_message_queue` | `infrastructure/message_queue.py:189` | |
| `require_backend` | `infrastructure/boot.py:66` | |
| `image_excludes_secrets` | `infrastructure/deployment_hygiene.py:96` | |
| `parse_frame_text` | `infrastructure/async_streaming.py:383` | |
| `get_breaker_status` | `infrastructure/resilience.py:251` | |
| `validate_production_risk_settings` | `application/risk_config.py` | see note below |

**Note on `validate_production_risk_settings`.** `factory.py` calls
`risk_config.resolve_risk_rails` at the live boot gate, and `GAP_READINESS.md:24` credits
"the live gate runs the same validator." The *function vulture flags* is not the function the
gate calls. The gate is real; the dead symbol is a separate wrapper. Flagged so nobody "fixes"
the wrong thing.

**Verified false positives — do not "fix" these:**

- **Every FastAPI handler in `interfaces/api/*.py`** (`operator.py`, `retail.py`, `market.py`,
  `server.py`) is reported unused. They are registered via `@router.get(...)` /
  `register_*_endpoints(router, ...)`. The live OpenAPI schema proves all 58 operations resolve.
- `daemon_controller.py:371` `signum` — it is a signal-handler parameter, called by the OS.
- `daemon_controller.py:85` `_market_hours` — set and read via `getattr`-style access.
- 100%-confidence hits in `tests/` (`test_backup.py` fixture params ×13,
  `test_probe_scheduler_ext.py:163`, `test_api_security_edges.py:130`) are pytest fixture
  arguments — the framework supplies them.

**Net read:** roughly **19 classes and 10 functions of unreferenced production surface**, plus
one structurally significant item — `build_async_daemon`, which is the only thing standing
between this codebase and a non-blocking collector (2.1.2) and which is currently reachable
only from tests.

---

## Phase 3 — Dependency-ordered plan

Ordered so each layer's evidence closes before the next opens. **Track 1 needs no code and
unblocks the GO/NO-GO decision; Track 2 is the code work; Track 3 is hygiene.**

### Track 1 — Unblock the GO/NO-GO decision (operator, no code)

| # | Action | Depends on | Closes |
|---|---|---|---|
| 1.1 | Deploy `traders-soak` with `railway up -s traderos-soak --detach --yes` (**not** `railway redeploy` — the service has no GitHub source connection and redeploy re-runs a stale image; this already leaked 389.29 AAPL, `GAP_READINESS.md:23`) | operator credentials | G-02 |
| 1.2 | Run the 24–72h unattended window on that fresh image; confirm every batch green and independently confirm flatness at intervals | 1.1 | **G-02 exit test** |
| 1.3 | Populate LIVE `allowed_markets` with the pilot symbols | operator | G-03 residual |
| 1.4 | Run the rotation + on-call drills against the **managed** Vault/KMS and a live PagerDuty/Slack account (`SECRET_ROTATION.md`, `ONCALL_LIVE_DELIVERY.md`) | operator keys | G-04 residual |

### Track 2 — Correctness (engineer; B-1 must be first, alone)

| # | Action | Why it is here | Proof required |
|---|---|---|---|
| **2.1** | **Fix B-1.** Keep `Candle.timestamp` a real `datetime` end-to-end. Parse at the collector boundary in `data_ingestion_service.py:86`; type `fetch_latest` as a typed record instead of `list[dict]` so the boundary cannot lie again. | It is a **safety control that does not work**, and its failure mode is the kill switch. Nothing else matters until it is fixed. | A test that wires the **real** `DataIngestionService` + real `RiskService` into `CycleExecutor` and asserts a LIVE cycle with fresh candles **submits**, plus one with a stale candle **blocks via G-03**. Shown failing on `07a7a1f` first. |
| 2.2 | **Fix B-3.** Set `_startup_reconciled = False` on any periodic reconciliation that reports a divergence, and **consume** the result of `_run_periodic_reconciliation` at `daemon_controller.py:467` instead of discarding it. | B-3 is the reason B-1's kill switch would be the *only* thing standing between a divergence and a new order. Depends on nothing, but pairs with 2.1 as the fail-closed pair. | A test that reconciles clean → asserts `can_accept_orders is True` → injects a divergence → asserts `can_accept_orders is False` **and** that `preflight`/`live_readiness` report not-reconciled. |
| 2.3 | **Fix B-2.** Require `client_order_id` at the broker seam, or fail closed when absent — do not silently derive a key that can replay a flatten. | Second fail-open on the order path. Must land before any real-capital GO. | A test asserting two same-attribute flattens produce **two distinct** submissions, and that an id-less order is rejected rather than replayed. |
| 2.4 | Wire the **async** daemon to production (`factory.py:659` already exists) so the two blocking Binance calls per market per cycle (2.1.2, measured ~412 ms each) stop blocking the trading loop, with an explicit timeout + circuit breaker. | Depends on 2.1 being correct — making the feed non-blocking while the breaker is broken would trade *faster* on bad data. | A soak run showing cycle latency independent of collector RTT; a forced collector hang that trips a breaker instead of stalling the loop. |
| 2.5 | Wrap a cycle in **one** transaction; carry the audit hash-chain head in memory instead of re-reading `audit_log` 8× per cycle. | 2.1.3: removes ~56 of 103 statements and ~29 fsyncs per cycle. | Measured statement count per cycle drops from 103 to <50; the audit chain still verifies (`traders audit verify`). |
| 2.6 | Add indexes on `positions` (`quantity`, `market_id`) and hoist `get_summary` / `_cash_balance` / preflight to once per cycle. | 2.1.3 + 2.1.4: removes 2 of 4 full position scans and 2 broker round trips per cycle. Independent of 2.5; do it in the same commit only if both are separately provable. | `EXPLAIN QUERY PLAN` uses the index; broker `get_account_balance` count per LIVE cycle = 1, not 2. |
| 2.7 | Memoize indicators on `(market_id, timeframe, last_candle_timestamp)`. | 2.1.1: ≈36.8 ms of a ≈58 ms cycle is redundant recompute. Lowest-risk perf win in the document. | Measured indicator cost per cycle approaches zero on an unchanged candle and stays correct when the candle advances. |
| 2.8 | Decide and document **cross-strategy coordination** (2.2.2): do three strategies size independently on one symbol? | Must be an explicit decision before real capital; currently it is neither allowed nor prevented. | Written policy + a drill that demonstrates the chosen behaviour. |

### Track 3 — Honesty and hygiene (engineer; independent of Tracks 1–2)

| # | Action | Why |
|---|---|---|
| 3.1 | Fix the three doc drifts in 2.5.2: `GAP_READINESS.md:3` header, `:27` test/coverage counts, and release `07a7a1f` (bump + changelog + tag). | The repo's own principle is *a score/claim must be reproducible*. A stale header on the GO/NO-GO document is the most expensive kind of drift. |
| 3.2 | Reconcile the G-05/G-07 scores (85 vs "closed") against the register's own exit-test rule. | Do not average the register; make each score traceable to its exit test. |
| 3.3 | Close the 275 `ResourceWarning` SQLite-handle leaks across 32 tests. | Unbounded SQLite handles in a daemon is a real failure mode; today several tests do not prove clean teardown. |
| 3.4 | Delete or wire the ~29 unreferenced production symbols (2.5.3). **Deliberately exclude `build_async_daemon`** — 2.4 depends on it. | Dead code in a safety-critical order path is a review hazard. |
| 3.5 | Add an integration test that constructs the production object graph from `factory.py` and runs one LIVE-shaped cycle per collector type. | B-1 escaped 2364 tests and 100% coverage. The missing test is a *wiring* test, not a coverage gap. |
| 3.6 | Rebuild `.venv` from `pyproject.toml` and re-run the suite to prove the pinned environment is green (**D-1**). | The 0.43.5 / 0.51.0 drift means today's green is measured against unpinned dependencies. |

---

## README update section

*To be applied to `README.md`. Every number below is measured in this audit; none is aspirational.*

### Performance (measured, not estimated)

- A trading cycle costs **≈58 ms median / 68 ms p95** in-process (3 strategies, in-memory
  SQLite), of which **≈37 ms is indicator recomputation that repeats unchanged work every
  cycle**.
- The dominant real-world cost is external: **two synchronous Binance HTTPS round trips per
  market per cycle, ~412 ms each**, blocking the trading loop.
- **103 SQL statements per cycle**, 56% of them `BEGIN`/`COMMIT` around single-row writes;
  **4 unindexed full scans of `positions` per cycle**.

### Current status

- `2364 passed, 7 skipped` · **100.00% coverage** (0 of 13,596 statements) · `ruff`, `black`,
  `isort`, and `pyright --strict` all clean.
- **G-02 (live order ops, CRITICAL): bounded runs pass; the 24–72h unattended window is
  operator-run and has not yet completed.**
- **G-01 (edge): no strategy demonstrates positive cost-adjusted expectancy on out-of-sample
  data.** All three registered strategies fail the all-folds-positive criterion on both the
  frozen oracle and real Binance walk-forwards. The pilot is correctly scoped
  **DATA-VALIDATION-ONLY** — no PnL claim.
- Two **open fail-open defects** on the LIVE order path (`can_accept_orders` is a one-way
  latch; the derived idempotency key can replay a flatten) and one **broken safety control**
  (the data-gap breaker raises `TypeError` instead of blocking). See
  `docs/engineering/SPRINT_AUDIT_2026-10-03.md` §2.4.

### Capability

**101 user-facing surfaces**: 58 HTTP API operations, 30 CLI commands, 13 dashboard panels —
covering trading control, risk rails, readiness/health, positions/orders/trades/PnL,
attribution, backtest/research, a full strategy-catalog lifecycle, market data, a governance
workflow, paper trading, observability/SSE, and a retail self-service surface.

---

## Honest residuals of *this* audit

1. **The performance numbers come from a synthetic in-memory broker and collector.** The
   in-process costs (2.1.1, 2.1.3, 2.1.5, 2.1.6) transfer; anything network-bound does not.
   The Binance figure (2.1.2) is a real measured call to the live public API from this host,
   but it is **one host, one moment, and unauthenticated** — not a p95.
2. **B-1's blast radius was established by reproduction, not by a production soak.** The
   reproduction uses the real `MockDataCollector`; whether Alpaca/Binance/streaming hit the
   same line depends only on `fetch_latest`, which is shared — but a soak with a production
   collector would be stronger proof.
3. **`fetch_latest(limit=1)` timing is a proxy** for the daemon's `get_latest_close` path. The
   daemon calls it per market per loop; I measured the collector, not the daemon loop.
4. **The measurements were taken with unpinned `alpaca-py` 0.43.5 and `uvicorn` 0.51.0**
   (pins: 0.30.0 / 0.29.0) — finding **D-1**, closed by plan item **3.6**.
5. **No repository code was modified by this audit.** The only file created is this document;
   all measurements came from throwaway scripts in `/tmp/opencode/trader-audit/`. The thirteen
   pre-existing modified evidence logs were left untouched.
