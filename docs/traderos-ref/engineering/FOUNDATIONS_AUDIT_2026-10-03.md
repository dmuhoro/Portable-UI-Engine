# TraderOS — Engineering Foundations Audit

**Audit date:** 2026-10-03 · **Branch:** `main` · **HEAD:** `07a7a1f` · **Tag:** `v1.3.3`
**Companion:** `docs/engineering/SPRINT_AUDIT_2026-10-03.md` (correctness + performance audit)
**Questions answered:** (1) performance-optimization infrastructure, (2) testing infrastructure —
strategy, scale, flakiness, (3) CodeRabbit code review, (4) product quality and launch
readiness, (5) algorithms, data structures, CS foundations, and analytical/communication craft.

**Method:** every claim is a command run in this repo or a `file:line` citation. Numbers labelled
*measured* were produced by executing the code. Where something is absent, absence is stated as
absence — not as a weak smell.

---

## Verdict at a glance

| # | Question | Verdict | One-line reason |
|---|---|---|---|
| 1 | Performance-optimization infrastructure | **Absent** | No profiling harness, no baseline benchmarks, no perf gate in CI. `.ai/agents/performance-agent.md` is prose that promises baselines which do not exist. |
| 2 | Testing infrastructure | **Strong, with three real gaps** | 9 CI jobs, 32 evidence drills as a gate, 2364 tests, 100% coverage — but **zero** flaky-test infrastructure and **no** written test strategy. |
| 3 | CodeRabbit | **Not present at all** | No `.coderabbit.yaml`, no CI job, no mention in any file in the repo. |
| 4 | Product quality / launch readiness | **Not ready for real capital** | Governance and process are mature; the runtime has 3 fail-open defects on the LIVE order path and G-02's exit test has never been run. |
| 5 | Algorithms / data structures / CS foundations | **Doctrine is right; implementation does not follow it** | `CONSTITUTION.md` Principle 10 names two of this repo's actual patterns as *violations*. Declared `numpy`/`pandas` are used by legacy-test-only dead code. Money is float end-to-end. |

**The single most useful thing in this document:** the gap is **not** knowledge and **not**
intent. `CONSTITUTION.md` and `BUILD_PRINCIPLES.md` already state the correct engineering
discipline in unusually precise language. What is missing is the machinery that makes the
doctrine binding. Section 6 proposes exactly that machinery.

---

## 1 Performance-optimization infrastructure

### 1.1 What exists

| Artifact | Reality |
|---|---|
| `tests/performance/test_benchmarks.py` | 1,924 bytes, dated Jul 27. **3 wall-clock assertions.** |
| `tests/performance/test_sprint9_benchmarks.py` | 738 bytes, dated Aug 7. |
| `.ai/agents/performance-agent.md` | 55 lines of prose. Mission, responsibilities, decision process, success criteria. No tooling. |
| CI performance gate | **None.** 9 jobs, none measure performance. |

The three committed assertions:

```python
# tests/performance/test_benchmarks.py:36-43
def test_backtest_1000_candles_under_1s(self):
    ...
    assert elapsed < 1.0, f"Backtest took {elapsed:.2f}s"

# :45-53
def test_execution_1000_orders_under_100ms(self):
    ...
    assert elapsed < 0.1, f"1000 orders took {elapsed:.2f}s"
```

### 1.2 Why this is not performance infrastructure

1. **It does not cover the hot path.** The profiled trading cycle
   (`cycle_executor.run`, order submission, reconciliation, the collector) has **no**
   benchmark. The two assertions cover a backtest and an order-construction loop.
2. **It cannot detect regression.** Raw `time.perf_counter()` against a hardcoded ceiling, with
   no stored baseline, no statistics, no `pytest-benchmark`, no history. A 2× regression that
   stays under the ceiling is invisible; a slow shared CI runner produces a red build for no
   reason. **These three tests are a flaky-test generator, not a gate.**
3. **They run in the coverage job** (`make test-coverage`), so timing asserts are coupled to the
   correctness gate. They belong in a separate, non-blocking job.
4. **`--min-confidence`-style profiling tooling is entirely absent.** Repo-wide search for
   `cProfile`, `py-spy`, `line_profiler`, `memory_profiler`, `pytest-benchmark`, `locust`,
   `yappi` across `*.py`, `*.toml`, `*.cfg` returns **zero** results outside `.git`/`.venv`.
   The companion audit had to build a profiler from scratch to answer the performance question.

### 1.3 The performance agent never ran

`.ai/agents/performance-agent.md` is referenced only by `.ai/context/` cross-reference tables
and historical sprint docs. Its charter is explicit:

> **Responsibilities:** "Identify N+1 queries, missing indexes, inefficient algorithms"
> **Outputs:** "Baseline benchmarks"

Both deliverables it was chartered to produce are absent — and both defects it was chartered to
find **were present**:

- **N+1**: `PortfolioService.get_summary()` called **4× per cycle** (measured) —
  `cycle_executor.py:304`, `:324`.
- **Missing indexes**: the `positions` table (`repositories/sqlite/trades.py:119-129`) has **no
  index at all** — no index on `quantity`, none on `market_id` — and is full-scanned 4× per
  cycle.

This is not a criticism of the document. It is evidence that **a written agent charter is not
an enforcement mechanism.** There is no hook, no job, no artifact that makes the agent's
"Success Criteria" binding.

### 1.4 Doctrine says performance is a feature. The doctrine's own examples are false.

`docs/engineering/CONSTITUTION.md:250` — **Principle 10: Performance is a Feature**:

| Principle 10 states | Actual |
|---|---|
| "The data pipeline uses vectorized operations (pandas/numpy) instead of loops" | **False.** All six indicators in `analysis_service.py` are hand-written pure-Python loops. `numpy`/`pandas` are imported in exactly **one** file repo-wide (`db_manager.py`). See §5.1. |
| "Database queries are indexed and EXPLAIN-planned" | **False.** `positions` has no index. No `EXPLAIN` query exists in the repo. |
| "A 1-year backtest on 1-hour data completes in under 10 seconds" | **True — measured 4.98 s for 8,760 candles.** |
| Violation example: "Using Python lists instead of numpy arrays for numerical computation" | This **is** `compute_sma`, `compute_atr`, `compute_bollinger_bands`. |
| Violation example: "Adding caching without measuring the cache hit rate" | `cache.py` tracks `hits` but is **unused anywhere in `src/`** — no caching at all on any path. |

Principle 10 is a well-written principle that the codebase does not satisfy, with two of its
three positive examples contradicted by the code. **That gap is an enforcement gap, not a
comprehension gap.**

### 1.5 What performance work is actually warranted (from measured baselines)

Full numbers in `SPRINT_AUDIT_2026-10-03.md` §2.1. Ranked by measured cost:

| Rank | Bottleneck | Measured | Root cause |
|---:|---|---|---|
| 1 | Two blocking Binance round trips per market per cycle | **~412 ms each**, RTT-dominated (payload size irrelevant) | synchronous `urlopen`; `build_async_daemon` exists at `factory.py:659` but is wired only to tests |
| 2 | Indicator recomputation | **≈36.8 ms of a ≈58 ms cycle** | O(n·w) algorithms recomputed on an unchanged window every cycle |
| 3 | SQL statement count | **103/cycle**, 56% `BEGIN`/`COMMIT` | one transaction per single-row write |
| 4 | `positions` full scans | **4/cycle**, unbounded growth | no index; `get_summary()` called per-strategy and per-signal |
| 5 | Redundant broker reads | 2 `get_account_balance()`/cycle in LIVE | portfolio snapshot + preflight hoisted per-cycle, not per-signal |

**Infrastructure conclusion:** the measurement discipline exists as an *idea* (`.ai/agents`,
Principle 10) and as *one-off effort* (the companion audit). It does not exist as a **system**.
There is no baseline artifact, no regression detector, no budget enforced in CI, and no owner
tasked with it.

---

## 2 Testing infrastructure

### 2.1 What is genuinely strong

This deserves to be said plainly, because it is unusual and it is real.

`.github/workflows/ci.yml` defines **nine jobs**, and they are well chosen:

| Job | What it actually enforces |
|---|---|
| `version-check` | `pyproject.toml` and `configs/settings.yaml` must agree; no legacy `VERSION` file |
| `lint` | `ruff 0.16.0` |
| `typecheck` | `pyright 1.1.411` — **`typeCheckingMode = "strict"`** (`pyproject.toml:111`) |
| `test` | full suite **with a real provisioned Postgres 16 on port 5433** so PG-backed tests run the *pass* path, not the skip path (explicitly commented in the workflow) |
| `evidence-drills` | `scripts/evidence/run_ci_drills.py` — 18 credential-free drills, each proving a fail-closed rail through real wiring; runner exits non-zero if any fails |
| `security` | `pip-audit --skip-editable` **and** `bandit -r src/traderos/ -lll` |
| `docker` | builds and pushes to GHCR, gated on the four jobs above |
| `deploy-check` | builds the image, runs `db migrate` against **fresh Postgres**, asserts `Schema version: 9`, boots the container and polls `/v1/healthz` to 200 |
| `governance` | runs `live_gate.py` in paper mode (must pass) **and** in live mode (must be **blocked**) — a negative test of the gate itself |

Plus `scripts/evidence/` holds **32 drill scripts** and `.pre-commit-config.yaml` wires
black / isort / ruff / pyright / 7 hygiene hooks including `detect-private-key`.

Test posture: **144 test files, 2,364 tests, 100.00% coverage, `fail_under = 100`**, 7 skips
each individually justified, zero `TODO`/`FIXME`/`xfail`.

**The evidence-drill pattern is the strongest thing here.** Proving a *fail-closed* rail by
running the real `CycleExecutor`/`RiskService`/HTTP transport and asserting non-zero exit is a
materially better discipline than asserting a return value on a helper.

### 2.2 Gap 1 — there is no flaky-test infrastructure whatsoever

Repo-wide search of `pyproject.toml`, `.github/`, `Makefile` for
`rerun` / `flaky` / `quarantine` / `xfail` / `--lf` / `last-failed` returns **zero results**.

| Missing | Consequence |
|---|---|
| No `pytest-rerunfailures` | An intermittent failure is either ignored or causes a re-push. No data is kept. |
| No quarantine convention | A known-flaky test gets deleted, loosened, or tolerated informally. |
| No per-test timing telemetry | You cannot even *detect* flakiness, let alone diagnose it. The full run reports one aggregate `573.87s`. |
| No `--lf` / last-failed workflow | Every rerun costs 9.5 minutes. |
| No `xfail` policy | Nothing prevents `xfail` from quietly absorbing a real failure — currently there are none, but nothing stops one appearing. |

The suite takes **9 min 33 s**. Without last-failed or sharding, iterating on a single failure
costs ten minutes of wall clock, which is itself pressure toward not writing precise tests.

**Three known flake sources exist today:**

1. The 3 wall-clock asserts in `tests/performance/` (§1.2) — flaky by construction.
2. The Binance WSS test skips on HTTP 404 (`test_programme_b_operational_trust.py:801`) —
   an external dependency turning into a permanent skip.
3. `conftest.py:8-22` documents a *real* order-dependent flake that was already hit and fixed:
   process-global circuit breakers leaking across tests. The fix (`reset_all_breakers()` before
   and after each test) is correct — and it is the kind of knowledge that belongs in a written
   test strategy so the next person does not rediscover it.

### 2.3 Gap 2 — there is no written test strategy

No document describes the testing approach. Searched `docs/`, `CONTRIBUTING.md`, `.ai/` — the
phrase "test strategy" appears only incidentally.

What is therefore **undocumented and unrecorded**:

- The drill taxonomy — which of the 32 drills are credential-free (CI-enforced) versus
  credential-gated (operator-run), and why. It lives in a `KEY_GATED` tuple in
  `scripts/evidence/run_ci_drills.py:76`, readable only by opening the script.
- The intended test pyramid: 144 files, but only **3** in `tests/integration/` and **2** in
  `tests/performance/`. The shape is unit-heavy with a thin, unstated integration tier.
- The skip policy. 7 skips are individually justified in code comments, but there is no rule
  stating when a skip is permitted.
- The rule this repo most needs: **"no test may mock the seam under test."** B-1 in the
  companion audit is exactly the failure that rule prevents.

`CONTRIBUTING.md` has a "Running Tests" section (§35) and nothing on strategy, flaky handling,
or what makes a test *prove* something.

### 2.4 Gap 3 — line coverage is the wrong gate, and this repo has the receipt

`fail_under = 100` is enforced and genuinely achieved: **0 missing of 13,596 statements**. And
`pyright --strict` is clean.

**Both passed on the exact defect that breaks LIVE trading.** `Candle.timestamp` is annotated
`datetime`, so the type checker is satisfied — while `data_ingestion_service.py:86` assigns a
`str` into it at runtime through an untyped `list[dict]` boundary. Both statements execute in
tests, so coverage is satisfied. The single test named for the path
(`test_cycle_executor.py:492`) mocks ingestion, mocks risk, hand-builds a `datetime`, and runs
in `PAPER` mode — it asserts none of the four things that break.

**Conclusion: 100% line coverage is not evidence of correctness at integration boundaries, and
in this repo it is demonstrably not.** The missing gate is not more coverage — it is a
*wiring* test that constructs the production object graph from `factory.py`.

### 2.5 Test-suite hygiene

**275 `ResourceWarning: unclosed database` entries across 32 distinct tests** (plus the 2
third-party deprecations = pytest's reported 277). Leaking suites include
`tests/integration/test_api.py::TestApiPaperTrade`, `tests/test_cli.py`, `tests/test_auth.py`,
`tests/test_operator_api.py`, `tests/test_market_research.py`,
`tests/test_order_contract.py`.

These appear under `make test` (coverage on) and vanish under `--no-cov` purely because GC
timing shifts without coverage tracing — `pytest-randomly` is **not** installed, so it is not
order luck. An unbounded SQLite handle leak across a long-lived process or a CI box that runs
the suite repeatedly is a genuine failure mode, and it means those tests do not prove clean
teardown.

---

## 3 Code review via CodeRabbit

### 3.1 It is not present

| Check | Result |
|---|---|
| `.coderabbit.yaml` / `.coderabbit/` | **absent** |
| Any `coderabbit` string in `*.yml`, `*.yaml`, `*.md`, `*.toml` | **zero matches** repo-wide |
| Any CodeRabbit CI step | **absent** |

### 3.2 What substitutes for it today

Static analysis only — and it is good, but it is a *different category* of tool:

| Layer | Tool |
|---|---|
| Lint | `ruff 0.16.0` (CI + pre-commit) |
| Types | `pyright 1.1.411`, `typeCheckingMode = "strict"` |
| Format | `black 26.5.1`, `isort 8.0.1` |
| Security | `bandit -lll`, `pip-audit` |
| Hygiene | 7 pre-commit hooks incl. `detect-private-key`, `check-merge-conflict` |

**What no tool in this repo does:** semantic review. Nothing reads a diff and asks "does this
change the fail-closed behaviour of the kill switch?", "is this new default a limit or a
suggestion?", "does this test assert the real path or a mock?". Those are exactly the three
questions that would have caught B-1, B-2, and B-3 — all of which pass every existing gate.

**This is the highest-leverage single addition in the entire audit.** A semantic reviewer
configured with the domain rules would flag `win_rate: float = 0.5` (§5.3) and the `str` into a
`datetime` field on sight, because both are pattern-level mistakes, not logic-level ones.

---

## 4 Product quality and launch readiness

### 4.1 The honest shape of this codebase

| Dimension | State |
|---|---|
| Governance & process | **Mature.** Signed releases, HMAC operator acknowledgment, fail-closed live gate, red-lines policy, CI negative-test of the gate itself, 14 runbooks. |
| Test & CI discipline | **Strong.** 9 jobs, real Postgres, 32 drills, 100% coverage, strict types. |
| Documentation | **Good, with drift.** Three concrete stale claims (`GAP_READINESS.md:3`, `:27`, and the unreleased `07a7a1f`). |
| Runtime correctness on the LIVE path | **Weak.** Three fail-open defects (B-1, B-2, B-3). |
| Measured edge | **None.** No strategy demonstrates positive cost-adjusted expectancy. |
| Performance | **Unmanaged.** No baseline, no gate; two ~412 ms blocking round trips per market per cycle. |

**The pattern to name plainly: process maturity is far ahead of runtime correctness.** The
repository has spent heavily on *proving the gates work* and lightly on *proving the trading
loop is correct*. That is why 2,364 tests and a clean `pyright --strict` coexist with a data-gap
breaker that raises `TypeError` instead of blocking.

### 4.2 Launch readiness

**Not ready for real capital.** Not because of any single blocker, but because three
independent fail-opens sit on the order path and G-02's exit test has never been executed.

| Blocker | Severity | State |
|---|---|---|
| B-1 — data-gap breaker raises `TypeError` instead of blocking; its failure mode is the kill switch | **CRITICAL** | open, reproduced |
| B-3 — `can_accept_orders` is a one-way latch; periodic reconciliation result discarded | **HIGH** | open |
| B-2 — derived idempotency key replays a second flatten | **HIGH** | open (live path mitigated by caller-owned `client_order_id`; API surface exposed) |
| G-02 24–72h unattended window | **CRITICAL** | never run — operator |
| G-01 demonstrated edge | HIGH | does not exist; DATA-VALIDATION-ONLY is the correct posture |
| `07a7a1f` unreleased | MEDIUM | violates the repo's own release discipline |

**Ready for:** continued DATA-VALIDATION-ONLY paper operation, with the caveat that B-1 means
the LIVE staleness gate is not currently protective — which is precisely why paper is the
correct posture and why real capital is not.

### 4.3 What "high quality" would require here

The gap is narrow and specific. It is **not** "write more tests" (2,364 already) and **not**
"add process" (9 CI jobs already). It is:

1. Wire the rails that are declared but not called (§5.4).
2. Make the money path Decimal end-to-end (§5.5).
3. Replace hand-rolled O(n·w) indicators with O(n) or vectorized ones (§5.1).
4. Replace invented numbers with measured ones (§5.3).
5. Add a semantic review layer and a performance baseline (§3, §1).

---

## 5 Algorithms, data structures, and CS foundations

Assessed against the repo's *own* standard (`CONSTITUTION.md` Principles 1–10) rather than an
external one, so the findings are measured against doctrine the team already accepts.

### 5.1 Declared vectorization is absent; the dependency is dead weight

| Fact | Evidence |
|---|---|
| `numpy==2.5.1` and `pandas==3.0.5` are hard dependencies | `pyproject.toml:8-9` |
| They are imported in **exactly one file** repo-wide | `src/traderos/infrastructure/database/db_manager.py:4` (`import pandas as pd`) — **zero** numpy imports |
| That file is reachable **only from two legacy test files** | `tests/test_core.py:5,14` and `tests/test_sprint1.py:4,13`; no `src/` caller |

So two of the heaviest declared dependencies ship inside the production Docker image in order
to satisfy tests of legacy code that nothing in `src/` imports. (My own audit's dead-code pass
independently flagged `DatabaseManager` at `db_manager.py:10` as unreferenced.)

### 5.2 Every indicator is a naive O(n·w) loop

`src/traderos/domain/services/analysis_service.py`:

```python
# :24  compute_sma
for i in range(len(candles)):
    if i < window - 1: continue
    total = sum(float(candles[j].ohlcv.close) for j in range(i - window + 1, i + 1))  # :33
```

```python
# :45  compute_ema  — an EMA should be O(n) recursive; this recomputes a full window sum
total = sum(float(candles[j].ohlcv.close) for j in range(i - window + 1, i + 1))
```

```python
# :108 compute_atr — nested loop
for i in range(len(candles)):
    for j in range(i - window + 1, i + 1):   # :39  O(n·w) plus a list rebuild
```

`compute_bollinger_bands` and `compute_stochastics` follow the same shape. All six:
`compute_sma`, `compute_ema`, `compute_rsi`, `compute_atr`, `compute_bollinger_bands`,
`compute_stochastics`.

**Measured cost** (100 candles, from the companion audit):

| Indicator | ms/call | Should be |
|---|---:|---|
| `BreakoutDetectionService.analyze` | **15.93** | sub-ms |
| `compute_atr(14)` | 6.43 | sub-ms |
| `compute_bollinger_bands(20,2)` | 6.42 | sub-ms |
| `compute_sma(50)` | 4.04 | sub-ms |
| `compute_sma(20)` | 2.98 | sub-ms |
| `RegimeDetectionService.detect` | 0.001 | fine |

≈**36.8 ms of a ≈58 ms cycle**, recomputed every cycle on a window that has barely changed.
A prefix-sum makes SMA O(n); a recursive EMA is O(n) already; ATR/BB are O(n) with a running
sum. This is textbook optimization and it is the largest in-process win available.

### 5.3 Invented numbers in the money path

```python
# src/traderos/domain/services/risk_service.py:318-324
def assess_trade(self, price, confidence, atr, account_equity, win_rate: float = 0.5) -> RiskAssessment:
```

**Both production call sites omit `win_rate`:**

- `cycle_executor.py:325-330` — passes `price`, `confidence`, `atr`, `account_equity`. Nothing else.
- `paper_trading_service.py:329-333` — same.

So `win_rate` is **always 0.5**, and it feeds:

```python
b = win_rate / (1 - win_rate)          # :335  -> 1.0
kelly = (b * confidence - (1 - confidence)) / b
kelly = max(0.0, min(kelly, self.max_position_size))
```

`risk.kelly_fraction` then drives `PortfolioService.size_position(...)` at
`cycle_executor.py:333-334`. **Every position in both live cycling and paper trading is sized by a
Kelly fraction computed from an invented, never-measured 50% win rate.**

Two further problems with the sizing even if `win_rate` were real:

1. **Kelly is fed a signal confidence.** `confidence` is `min(|sma_gap| × 10, 1.0)` from
   `MovingAverageTrend` — a distance-from-threshold, not a probability of winning. Multiplying a
   payoff ratio by a non-probability and calling it Kelly sizing is a category error.
2. **No fractional Kelly.** The literature is unambiguous that full Kelly is high-variance and
   that ¼–⅛ Kelly is standard practice precisely because `win_rate` is estimated from limited
   data. There is no fractional factor and no note about estimation error.

This directly contradicts the repo's own fail-closed doctrine and it makes an expectancy claim
structurally unfalsifiable: **if position size is derived from a constant, no amount of
walk-forward evidence can attribute PnL to skill.**

### 5.4 Declared rails that are not wired to the real path

This is the most important CS finding, and it needs careful scoping — much of the portfolio-level
risk surface is **declared and unit-tested but has no caller in `src/`**:

| Symbol | Location | Status |
|---|---|---|
| `check_concentration` | `risk_service.py:378` | **no `src/` caller** |
| `enforce_limits` | `risk_service.py:402` | **no `src/` caller** |
| `compute_var` | `risk_service.py:~350` | reached only via `check_concentration` → also unreachable |
| `compute_max_drawdown` | `risk_service.py:367` | **no `src/` caller** |
| `max_leverage: float = 2.0` | `risk_service.py:131` | **zero uses outside its own declaration** |

Three defects live inside this unwired surface:

**(a) `check_concentration` reports the threshold as if it were the measurement.**

```python
# risk_service.py:396-399
return PortfolioRisk(
    var_95=var,
    max_drawdown=self.max_drawdown_limit,   # <-- the 20% LIMIT, not a computed drawdown
    concentration_risk=concentrations,
    num_over_limit=over,
)
```

`PortfolioRisk.max_drawdown` is hardcoded to the **limit** (default `0.20`,
`risk_service.py:132`). Any consumer would read a constant `0.20` and believe it were the
portfolio's measured drawdown. The only function that could compute it
(`compute_max_drawdown`) is the one with no caller.

*Fair scoping:* I checked the `.max_drawdown` consumers — `cli/main.py:259`,
`dashboard/app.js:386`, `api/market.py:249`, `api/server.py:428`,
`backtesting_service.py:293`, `strategy_management.py:196` — and they read **backtest**
`PerformanceMetrics`, not `PortfolioRisk`. So this is **not currently misreporting anything
user-visible.** It is a landmine: the moment someone wires `check_concentration` into the risk
path, which is plainly its intent, they get a constant dressed as a measurement. That is
precisely the "code claiming a protection it does not provide" failure mode.

**(b) `compute_max_drawdown` divides by `peak` unguarded.** Reproduced:

```
flat zero        -> ZeroDivisionError: division by zero
negative equity  -> 1.5
```

A risk function that raises on a zero-start equity curve — the state a blown account is in.
`tests/test_risk_service.py:59,271` covers an ordinary curve and the empty case; **not** the
zero case.

**(c) `enforce_limits` is dimensionally incoherent.**

```python
# risk_service.py:409
drawdown_limit = self.max_drawdown_limit * position.quantity * position.entry_price
return not (position.pnl < 0 and abs(position.pnl) > drawdown_limit)
```

A *percentage* multiplied by a *notional* is treated as a loss threshold. The consequence is
backwards: the absolute loss allowance **grows with position size**, so the largest position is
granted the largest loss budget — the inverse of a concentration rail.

**(d) `compute_var` is a one-period parametric VaR.**
`self.var_confidence * std * total_value` with `var_confidence = 1.645`. It ignores holding
period, correlation, and everything outside the normal assumption, while the field is named
`var_95`. Acceptable as a rough concentration proxy; misleading as a "95% VaR".

**What *is* genuinely enforced at the real seam** — `authorize_order`
(`risk_service.py:197-262`), called from `cycle_executor.py:351` — is a short, correct,
fail-closed list: kill switch engaged, `equity <= 0`, daily-loss limit, market allowlist, and
candle staleness. Each returns `self._block_order(...)`, which writes to both the audit trail
and metrics — satisfying `BUILD_PRINCIPLES.md` P2/P3. **The per-order rails are real. It is the
portfolio-level aggregation above them that is unwired.**

That distinction matters for the gap register, because G-03 is titled "**Portfolio**-level risk
rails" (`GAP_READINESS.md:24`) and its drill evidence covers the per-order rails and kill
flatten. The title overstates what the exit test proves.

### 5.5 Decimal discipline is real at the edge and abandoned at entry

The good part, which is genuinely well done:

- `OHLCV` is `Decimal` throughout — `domain/entities/value_objects.py:21-26`, with a real
  `validate()` rejecting `low > high` and negative prices.
- Collectors parse defensively: `Decimal(str(entry[1]))` (`binance_collector.py:41-45`) —
  going through `str` to avoid binary-float contamination.
- `alpaca_collector.py` does the same.

The abandonment, one function later:

```python
# cycle_executor.py:190-192
high   = float(last_candle.ohlcv.high)
low    = float(last_candle.ohlcv.low)
volume = float(last_candle.ohlcv.volume)
# :358, :527
abs(float(p.quantity)) * float(p.current_price)
```

And at every persistence boundary:

```sql
-- repositories/sqlite/trades.py:33-37, 122-126
quantity REAL NOT NULL,  price REAL NOT NULL,  filled_quantity REAL DEFAULT 0.0,
entry_price REAL NOT NULL, current_price REAL NOT NULL, pnl REAL NOT NULL, realized_pnl REAL DEFAULT 0.0
-- repositories/sqlite/strategies.py:106-115 — every risk metric is REAL
sharpe_ratio REAL, sortino_ratio REAL, calmar_ratio REAL, max_drawdown REAL, expectancy REAL ...
```

Domain-wide: **197 `float` annotations vs 32 `Decimal` usages.**

**Net effect: every price, quantity, PnL, and risk metric is an IEEE-754 double by the time it
is stored or compared.** The Decimal discipline at the collector boundary buys nothing, because
the value is converted to `float` on the first line of the cycle that reads it. This is a
correctness gap in a money system and it is invisible to `pyright --strict`, which sees an
annotated `float` and a correctly-typed `float()` call.

### 5.6 Data structures — assessment

| Area | Assessment |
|---|---|
| `CollectorRegistry`, repositories | Clean, appropriate abstractions; ports-and-adapters separation is genuinely well executed (`domain/ports.py` is one of the better-layered parts of the codebase). |
| Reconciliation | **Good.** Clean O(n) with dict indexing, measured 0.10 ms → 75.7 ms from 10 to 5,000 positions. **No N+1.** This is the one hot-path component that is algorithmically sound. |
| Indicator accumulation | **Poor.** O(n·w) where O(n) suffices, no prefix sums, no numpy (§5.2). |
| Persistence | **Weak.** No index on `positions`; 4 full scans/cycle; one transaction per write; hash-chain re-read 8×/cycle. |
| Caching | **Absent.** `cache.py` implements TTL + hit counters correctly but has **no caller in `src/`**. |
| Concurrency | Sync `urlopen` on the trading loop; `build_async_daemon` exists but is test-only. |
| Money representation | **Wrong for the domain** (§5.5). |

### 5.7 Analytical, problem-solving, and technical communication

Assessed from what the repository actually contains:

**Analytical / problem-solving — strong.** The evidence-drill method is a real instance of it:
identify a claim that must hold ("this rail fails closed"), construct the *real* object graph,
inject the fault, assert non-zero exit, commit the log, and gate CI on it. Sprint 45's
WS-resync drill and Sprint 50's position-flatten root-cause (712.5 AAPL, `~$234,000`, cash
`-122,422.75` → traced to the harness not closing positions) are genuine root-cause analyses
with numbers, not hand-waving. `BUILD_PRINCIPLES.md` P1 ("Evidence over aspiration") and P5
("Second order as requirements") encode the habit.

**Technical communication — strong, with one systematic flaw.** 14 runbooks, a constitution,
4 ADRs, 50 sprint documents, release notes, and evidence logs with measured values and explicit
PASS/FAIL verdicts. `GAP_READINESS.md` even includes a self-correcting note explaining *why* a
score is not a promise and that only the exit test moves it.

**The flaw: doctrine-to-practice drift is systematic and unchecked.** This audit found, in one
pass, three separate instances where `CONSTITUTION.md` states a standard the code violates:

1. Principle 10's vectorized-pipeline example — all six indicators are Python loops.
2. Principle 10's indexed-queries example — `positions` has no index.
3. `GAP_READINESS.md:24` "Portfolio-level risk rails" — the portfolio-level aggregation has no
   caller.

The documentation is accurate *about itself* and it is accurate *about the past* (the sprint
logs describe what was true when written). It is not reconciled against the present. That is a
**verification** gap, not a communication gap — and it is the single highest-value thing to fix,
because it is cheap: a doc-drift gate that re-checks the load-bearing claims.

---

## 6 Operational doctrine addendum (proposed)

The user asked that gaps in algorithms, data structures, CS practice, and analytical craft be
incorporated into operational doctrine. Written as a standalone addendum at
`docs/engineering/OPERATIONAL_DOCTRINE_ADDENDUM_2026-10-03.md`, with a promotion path into
`CONSTITUTION.md` / `BUILD_PRINCIPLES.md` requiring a normal version bump + tag.

Design rule for this addendum: **every principle carries a machine-checkable enforcement
mechanism.** That is the specific lesson of §1.3 and §5.7 — a charter, a principle, or an agent
document that nothing verifies does not move behaviour. Each item below names the gate.

| ID | Principle | Enforcement mechanism proposed |
|---|---|---|
| **OD-1** | **No measurement, no optimization** — and no optimization without a stored baseline. | `tests/performance/` becomes `pytest-benchmark` with committed baselines; a `performance` CI job runs it **non-blocking** first, then is promoted to blocking once baselines stabilize. Replaces the 3 wall-clock asserts. |
| **OD-2** | **Every hot path has a benchmark and a latency budget.** The trading cycle, order submission, reconciliation, and each collector are named, budgeted, and measured per commit. | Budget table in `docs/engineering/`; CI job fails on regression >10% against the committed baseline. Directly closes the ~412 ms RTT finding. |
| **OD-3** | **Declared dependency or delete it.** A dependency must be imported by at least one `src/` module and reachable from a production entrypoint. | A CI dependency-hygiene job asserting every `pyproject` dependency has a `src/` importer. Closes the numpy/pandas finding in §5.1. |
| **OD-4** | **Prefer the right algorithm; O(n·w) is a defect on a hot path.** Numerical kernels use prefix sums, recursion, or vectorized arrays — not nested Python loops. | The OD-1 benchmark plus a complexity review trigger when a new indicator is added. Names the §5.2 finding. |
| **OD-5** | **No invented numbers in the money path.** Position sizing may only use quantities derived from recorded observations. A default that silently substitutes an assumption for a measurement is forbidden. | Kill the `win_rate: float = 0.5` default; `assess_trade` must require an explicit, sourced `win_rate`. A lint rule flags numeric defaults on money-path signatures. Closes §5.3. |
| **OD-6** | **A rail that is not called is not a rail.** Any declared limit, validator, or check must be reachable from the real order path or be deleted. A field must never report a threshold as if it were a measurement. | A reachability check in CI (or an explicit allow-list of declared-but-unwired rails with an owner and a date). Closes §5.4, including `max_leverage` and `check_concentration`. |
| **OD-7** | **Fail closed on degenerate input.** No risk function may raise or return a sentinel on a reachable state (zero equity, empty series, negative balance). | Property-based tests over degenerate inputs (see OD-10). Closes the `compute_max_drawdown` ZeroDivisionError. |
| **OD-8** | **Money is Decimal end-to-end, or the Decimal discipline is removed.** No float may hold a price, quantity, PnL, or risk metric — in the domain, in transit, or in a column. | `REAL` → integer-minor-units or NUMERIC migration; a lint rule banning `float` in domain/ and forbidding `REAL` for money columns. Closes §5.5. |
| **OD-9** | **No test may mock the seam it exists to prove.** A test that mocks ingestion, risk, or the broker proves the mock. Wiring tests must build the object graph from the production factory. | A review checklist item plus a `tests/wiring/` tier that CI requires to exist and pass. Directly prevents a recurrence of B-1. |
| **OD-10** | **Property-based and boundary testing for the numeric core.** Kelly sizing, VaR, drawdown, indicator windows, and reconciliation get Hypothesis strategies over degenerate and adversarial inputs, not just hand-picked examples. | `hypothesis` in the `dev` extra; a CI job with a fixed seed and a shrinking budget. |
| **OD-11** | **Flakiness is a tracked metric, not a shrug.** No test may be skipped, xfailed, or loosened to make a build green. Every skip names its gate. Flaky tests are quarantined with an owner and an expiry, never deleted. | `pytest-rerunfailures` + per-test duration telemetry + a flaky-quarantine manifest reviewed like code; a CI job that fails if quarantine grows or an item expires. |
| **OD-12** | **The test suite has a written strategy.** Pyramid shape, drill taxonomy, credential-gated vs deterministic split, skip policy, and the mocking rule are documented, not implicit in a `KEY_GATED` tuple. | `docs/engineering/TEST_STRATEGY.md`, linked from `CONTRIBUTING.md`. |
| **OD-13** | **Coverage is necessary, not sufficient.** `fail_under = 100` stays and is never cited as proof of correctness at an integration boundary; no PR may justify a change by raising or removing coverage. | A language rule in PR review ("covered" ≠ "verified") plus a `tests/wiring/` tier as the compensating gate. Closes §2.4. |
| **OD-14** | **Semantic review is a gate, not a courtesy.** Every change is reviewed by a tool that reads the diff against the domain rules above — not only by linters. | **CodeRabbit** with `.coderabbit.yaml` encoding OD-5/6/8/9 as required checks, running as a CI job on every PR. Closes §3. |
| **OD-15** | **Doctrine without a gate is a wish.** Every principle in this addendum names its enforcement mechanism, and the mechanism is implemented in the same change that adds the principle. | The addendum is not ratified until each row's gate exists or has a dated owner. |
| **OD-16** | **Docs are reconciled against the present, automatically.** Every load-bearing numeric or behavioural claim in a doc is re-derived from code or CI on a schedule. | A docs-drift job that re-checks the `GAP_READINESS.md` header, its test/coverage counts, and that every registered strategy, CLI leaf, and API operation still exists. Closes the §5.7 drift findings. |

**Sequencing.** OD-14 (CodeRabbit) and OD-16 (docs-drift) are cheap, immediately valuable, and
depend on nothing. OD-5, OD-6, OD-9 are the correctness pair with the companion audit's B-1/B-2/B-3
and must land with real code changes. OD-8 is the largest migration. OD-1/OD-2 must follow the
B-1 fix, because making the loop non-blocking while the staleness breaker is broken would trade
*faster* on bad data.

---

## 7 Honest residuals of *this* foundations audit

1. **CodeRabbit's absence was established by search, not by account inspection.** No
   `.coderabbit.yaml`, no CI step, and zero string matches repo-wide. A reviewer configured
   outside the repository (org-level settings, or a GitHub App) would not be visible here.
   Worth confirming in the GitHub org settings before acting on §3.
2. **The performance baseline in §1.5 is a one-time measurement, not a regression detector.**
   Building that detector is OD-1/OD-2 and has not been done.
3. **Reachability claims in §5.4 come from a repo-wide `src/` grep.** A dynamic path — a
   plugin, a decorator, an entrypoint loaded from config — would not show up. I checked the
   obvious decorators (FastAPI, `@registry.register`, argparse) and none covers these symbols.
4. **The 275 SQLite-handle warnings were counted from one run under one Python build.** The
   `--no-cov` run reported 2 warnings; the coverage run reported 277. `pytest-randomly` is not
   installed, so the difference is coverage-tracing GC timing — but that explanation is inferred,
   not proven, and the underlying leak is real either way.
5. **`win_rate` may be intentionally conservative.** I did not find a design note justifying
   `0.5`. If there is one, the correct outcome is OD-5's *alternative*: document the assumption,
   mark it as unvalidated in the record, and make it visible in every PnL claim — not leave it
   invisible in a default.
6. **No repository code was modified by this audit.** Deliverables are
   `docs/engineering/FOUNDATIONS_AUDIT_2026-10-03.md` and
   `docs/engineering/OPERATIONAL_DOCTRINE_ADDENDUM_2026-10-03.md`. Measurements came from
   throwaway scripts in `/tmp/opencode/trader-audit/`. The 13 pre-existing modified evidence logs
   were left untouched.
