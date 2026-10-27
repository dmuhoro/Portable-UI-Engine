# Operational Doctrine Addendum — Measurement, Testing, and Foundations

**Version:** 1.0.0-draft · **Date:** 2026-10-03 · **Status:** DRAFT — not yet ratified
**Authority:** none until ratified. Extends, does not amend,
`docs/engineering/CONSTITUTION.md` and `docs/engineering/BUILD_PRINCIPLES.md`.
**Evidence base:** `docs/engineering/FOUNDATIONS_AUDIT_2026-10-03.md`,
`docs/engineering/SPRINT_AUDIT_2026-10-03.md`.

---

## 0 Purpose and scope

`CONSTITUTION.md` already holds Principles 1–10, several of which state the correct standard in
unusually precise language. The foundations audit found that **two of Principle 10's three
positive examples are contradicted by the code**, and that `.ai/agents/performance-agent.md`
promised baseline benchmarks which do not exist and whose charter (find N+1 queries and missing
indexes) matched defects that were present and undetected.

The gap is therefore **not comprehension and not intent**. It is that doctrine here is prose
without machinery. This addendum exists to close exactly that gap, and it is deliberately
written against one rule:

### OD-15 — No principle without a gate *(governing rule for this document)*

**Rule.** Every principle below names the machine-checkable gate that makes it binding. A
principle without a gate is not merged into this document, and none may be promoted into
`CONSTITUTION.md` until its gate exists in CI or has a named owner and a dated commitment
(§7.2).

**Evidence.** This document exists because a prose charter is not an enforcement mechanism.
`.ai/agents/performance-agent.md` promised baseline benchmarks and N+1 detection; the benchmarks do
not exist, and the N+1 (`get_summary()` 4× per cycle) and the missing `positions` index were both
present and undetected. `CONSTITUTION.md` Principle 10 states two standards — vectorized
pipelines, indexed queries — that the code violates. Written intent, in both cases, produced no
behaviour change.

**Enforcement.** This addendum is not ratified until every row of §7.2 reads `yes`, or carries an
owner and a date.

**Status.** PROPOSED — and it is the first row that must close.

---

Each entry below carries: the rule, the evidence that motivated it, the enforcement mechanism, and
a status. `Status: PROPOSED` means the rule is agreed but the gate does not exist yet.

---

## 1 Performance and measurement

### OD-1 — No optimization without a stored baseline
**Rule.** An optimization is not accepted unless it is measured against a committed baseline
*before* and *after*, and the baseline is stored in the repository.

**Evidence.** `tests/performance/test_benchmarks.py` holds 3 raw `time.perf_counter()`
assertions against hardcoded ceilings, no baseline history, no statistics, and none on the
trading hot path. `CONSTITUTION.md:257` already requires "Every optimization must be justified
by a benchmark" — unenforced.

**Enforcement.** Replace `tests/performance/` with `pytest-benchmark`; commit `*.benchmark.json`
baselines. A dedicated `performance` CI job runs **non-blocking** for two weeks, then is promoted
to blocking once baseline variance is characterised.

**Status.** PROPOSED. **Gate owner:** unassigned.

### OD-2 — Every hot path has a named budget
**Rule.** These four paths are budgeted and measured per commit: the trading cycle
(`CycleExecutor.run`), order submission (`JournaledBroker.place_market_order`), broker-state
reconciliation, and each market-data collector.

**Evidence.** *Measured:* two blocking Binance round trips per market per cycle at **~412 ms
each**, RTT-dominated — payload size irrelevant (`SPRINT_AUDIT` §2.1.2). `CycleExecutor.run`
**≈58 ms median / 68 ms p95** in-process. These numbers exist only in an audit document; nothing
re-checks them.

**Enforcement.** A budget table in `docs/engineering/PERFORMANCE_BUDGETS.md`; CI fails when a
budget regresses >10% against the committed baseline.

**Status.** PROPOSED. **Gate owner:** unassigned.

### OD-4 — The right algorithm, or it is a defect on a hot path
**Rule.** Numerical kernels on a hot path use O(n) techniques — prefix sums, recursion, or
vectorized arrays. O(n·w) nested Python loops are a review-blocking defect, not a style note.

**Evidence.** All six indicators in `domain/services/analysis_service.py` are O(n·w):
`compute_sma:24-40`, `compute_ema:45-62`, `compute_atr:108-139`, plus `compute_bollinger_bands:136`
and `compute_stochastics:182`. *Measured* ≈**36.8 ms of a ≈58 ms cycle**, recomputed every cycle
on an essentially unchanged window. `CONSTITUTION.md:265` lists "Using Python lists instead of
numpy arrays for numerical computation" as a **violation example** — it describes this codebase.

**Enforcement.** OD-1's benchmark plus a mandatory complexity note in the PR description for any
new or changed indicator.

**Status.** PROPOSED.

---

## 2 Dependencies and data representation

### OD-3 — A declared dependency must earn its place
**Rule.** Every dependency in `pyproject.toml` must be imported by at least one module under
`src/` that is reachable from a production entrypoint. Otherwise it is removed or the dead
consumer is removed.

**Evidence.** `numpy==2.5.1` and `pandas==3.0.5` are hard dependencies (`pyproject.toml:8-9`).
Repo-wide, `pandas` is imported in exactly **one** file — `infrastructure/database/db_manager.py:4`
— and `numpy` in **none**. That file's only consumers are two legacy test files
(`tests/test_core.py:5,14`, `tests/test_sprint1.py:4,13`); it has no `src/` caller. Two of the
heaviest dependencies ship in the production image to satisfy tests of legacy code.

**Enforcement.** A CI dependency-hygiene job asserting each declared dependency has a `src/`
importer; run weekly and on dependency changes.

**Status.** PROPOSED.

### OD-8 — Money is Decimal end-to-end, or not at all
**Rule.** No `float` may hold a price, quantity, PnL, or risk metric — in the domain, in transit,
or in a database column. Either the Decimal discipline reaches the store, or the pretence of it
is removed from the collectors.

**Evidence.** The discipline is real at the edge and abandoned one function later. `OHLCV` is
correctly `Decimal` (`domain/entities/value_objects.py:21-26`, with a real `validate()`), and
collectors parse defensively via `Decimal(str(...))` (`binance_collector.py:41-45`). Then
`cycle_executor.py:190-192` calls `float()` on the first line that reads a candle, `:358` and
`:527` do `float(p.quantity) * float(p.current_price)`, and every money column is SQLite
`REAL` (`repositories/sqlite/trades.py:33-37,122-126`) as is every risk metric
(`repositories/sqlite/strategies.py:106-115`). Domain-wide: **197 `float` annotations vs 32
`Decimal` usages**. `pyright --strict` cannot see this, because the declared type is correctly
`float`.

**Enforcement.** A lint rule banning `float` annotations under `domain/`; a schema check
forbidding `REAL` on money columns; a migration to integer minor units or NUMERIC.

**Status.** PROPOSED — largest item in this addendum. **Sequencing:** after OD-5 and OD-6.

---

## 3 Risk correctness — the money path

### OD-5 — No invented numbers in the money path
**Rule.** Position sizing may only use quantities derived from recorded observations. A default
that silently substitutes an assumption for a measurement is **forbidden** — the function must
require the value, or refuse.

**Evidence.** `risk_service.py:324` declares `win_rate: float = 0.5`. **Both production call
sites omit it** — `cycle_executor.py:325-330` and `paper_trading_service.py:329-333`. It feeds
`kelly = (b·confidence − (1−confidence))/b` at `:336`, whose result drives
`PortfolioService.size_position` at `cycle_executor.py:333-334`. **Every position in live cycling and
paper trading is sized from an invented, never-measured 50% win rate.** Two further defects:
signal `confidence` (a distance-from-threshold, `strategy_framework.py:73`) is fed to Kelly as
though it were a probability; and there is no fractional-Kelly factor despite `win_rate` being
estimated from limited data.

**Enforcement.** Remove the default so `assess_trade` requires an explicit, sourced `win_rate`;
add a lint rule rejecting numeric defaults on money-path signatures.

**Status.** PROPOSED. **Sequencing:** with OD-6.

### OD-6 — A rail that is not called is not a rail
**Rule.** Any declared limit, validator, or check must be reachable from the real order path, or
be deleted. A field must never report a threshold as though it were a measurement.

**Evidence.** `check_concentration` (`risk_service.py:378`), `enforce_limits` (`:402`),
`compute_var`, and `compute_max_drawdown` (`:367`) have **no `src/` caller**.
`max_leverage: float = 2.0` (`:131`) has **zero uses outside its own declaration**. Inside that
unwired surface:
- `:397` returns `max_drawdown=self.max_drawdown_limit` — the **20% limit** — as `max_drawdown`.
  A consumer would read the constant `0.20` as a measurement.
- `:409` computes `max_drawdown_limit * quantity * entry_price`: a percentage × a notional used
  as a loss threshold, which makes the loss budget **grow with position size**.
- `:365` is a one-period parametric VaR reported as `var_95`.

*Fair scoping:* what **is** enforced at the real seam — `authorize_order`
(`risk_service.py:197-262`, called from `cycle_executor.py:351`) — is correct and fail-closed:
kill switch, `equity <= 0`, daily-loss limit, allowlist, staleness, each via `_block_order` to
both audit and metrics. **The per-order rails are real; the portfolio-level aggregation above
them is not wired.** G-03 is titled "*Portfolio*-level risk rails"
(`GAP_READINESS.md:24`) and its drill covers the per-order rails — the title overstates the exit
test.

**Enforcement.** A CI reachability check over declared rails, or an explicit allow-list where each
unwired rail has a named owner and a dated commitment.

**Status.** PROPOSED.

### OD-7 — Fail closed on degenerate input
**Rule.** No risk or sizing function may raise or return a sentinel on a reachable state — zero
equity, empty series, negative balance, zero denominator.

**Evidence.** `compute_max_drawdown` divides by `peak` unguarded (`risk_service.py:375`).
Reproduced: `flat zero → ZeroDivisionError`. `tests/test_risk_service.py:59,271` covers an ordinary
curve and the empty case — not the zero case. A risk function that raises on a zero-start equity
curve is raising in exactly the state where the number is needed most.

**Enforcement.** Property-based tests over degenerate inputs — see OD-10.

**Status.** PROPOSED.

---

## 4 Testing doctrine

### OD-9 — No test may mock the seam it exists to prove
**Rule.** A test that mocks ingestion, risk, or the broker proves the mock. Any claim about
system behaviour must be backed by a test that builds the object graph from the production
factory.

**Evidence.** `tests/test_cycle_executor.py:492`
`test_candles_processed_with_data_ingestion` uses a mocked `data_ingestion` (`:497`), a
hand-built `datetime` (`:520`), a mocked `risk_service` (`:537`), and `mode=PAPER` (`:556`) — so
it exercises **none** of the four things that break. `data_ingestion_service.py:50,86` puts a
`str` into a `datetime`-annotated `Candle`, and **both** consumers (`cycle_executor.py:160-161`,
`risk_service.py:260-261`) raise `TypeError`. `scripts/evidence/run_real_paper_soak.py` builds
`CycleExecutor` with **no** `data_ingestion` (verified), so the soak that reported PASS never
reached it. This defect passed **2,364 tests, 100% line coverage, and `pyright --strict`.**

**Enforcement.** A `tests/wiring/` tier that CI requires to exist and pass, constructing the graph
from `factory.py` and running one LIVE-shaped cycle per collector type. Plus a review checklist
item.

**Status.** PROPOSED. **Highest priority in this section.**

### OD-10 — Property-based testing for the numeric core
**Rule.** Kelly sizing, VaR, drawdown, indicator windows, reconciliation, and fold-splitting get
Hypothesis strategies over degenerate and adversarial inputs — not only hand-picked examples.

**Evidence.** The 100%-coverage, strict-types suite still shipped two arithmetic defects in the
risk path (OD-5, OD-7). Hand-picked examples do not find the input nobody imagined; a
zero-denominator is exactly that input.

**Enforcement.** `hypothesis` in the `dev` extra; a CI job with a fixed seed, a shrinking
example database, and a per-run deadline.

**Status.** PROPOSED.

### OD-11 — Flakiness is a tracked metric, not a shrug
**Rule.** No test may be skipped, xfailed, loosened, or retried into green to make a build pass.
Every skip names the gate that authorises it. A flaky test is **quarantined with an owner and an
expiry** — never deleted, never silently retried.

**Evidence.** Repo-wide search for `rerun` / `flaky` / `quarantine` / `xfail` / `--lf` /
`last-failed` across `pyproject.toml`, `.github/`, `Makefile` returns **zero results**. The suite
takes **9 m 33 s** with no per-test timing telemetry, so flakiness cannot even be detected, let
alone diagnosed. Three known sources today: the 3 wall-clock asserts in `tests/performance/`
(flaky by construction); the Binance WSS test permanently skipped on HTTP 404
(`test_programme_b_operational_trust.py:801`); and the process-global circuit-breaker leak
already hit and fixed in `conftest.py:8-22` — knowledge that belongs in OD-12 so it is not
rediscovered.

**Enforcement.** `pytest-rerunfailures` + per-test duration telemetry + a
`tests/QUARANTINE.md` manifest reviewed like code + a CI job that fails if quarantine grows or an
item passes its expiry.

**Status.** PROPOSED.

### OD-12 — The test suite has a written strategy
**Rule.** Pyramid shape, drill taxonomy, the credential-gated vs deterministic split, the skip
policy, and the mocking rule (OD-9) are documented — not implicit in a `KEY_GATED` tuple.

**Evidence.** `CONTRIBUTING.md` has "Running Tests" and nothing on strategy. The deterministic
drill set is discoverable only by reading `scripts/evidence/run_ci_drills.py:76`. Of 144 test
files, only **3** are in `tests/integration/` and **2** in `tests/performance/` — the shape is
unit-heavy with an unstated, thin integration tier.

**Enforcement.** `docs/engineering/TEST_STRATEGY.md`, linked from `CONTRIBUTING.md`, reviewed when
the suite shape changes materially.

**Status.** PROPOSED.

### OD-13 — Coverage is necessary and not sufficient
**Rule.** `fail_under = 100` stays. It is **never** cited as evidence of correctness at an
integration boundary, and a PR may not justify a change by raising or removing coverage.

**Evidence.** Achieved: **0 missing of 13,596 statements**, with `pyright --strict` clean — and
both gates passed on the LIVE-breaking defect in OD-9. Line coverage proves lines ran; it does
not prove the object graph was real.

**Enforcement.** Language rule in PR review: "covered" ≠ "verified". `tests/wiring/` (OD-9) is
the compensating gate.

**Status.** PROPOSED.

---

## 5 Review

### OD-14 — Semantic review is a gate, not a courtesy
**Rule.** Every change is reviewed by a tool that reads the diff against the domain rules in this
document — not only by linters and type checkers.

**Evidence.** **CodeRabbit is entirely absent**: no `.coderabbit.yaml`, no CI step, and zero
string matches for `coderabbit` across every `*.yml`, `*.yaml`, `*.md`, and `*.toml` in the
repo. What exists is static analysis only — `ruff`, `pyright --strict`, `black`, `isort`,
`bandit`, `pip-audit`, plus 7 pre-commit hooks. Every one of those passed on all three LIVE
fail-open defects, because each is a **pattern-level** mistake (a `str` in a `datetime` field; a
`0.5` default on a money-path parameter; a discarded reconciliation result), not a logic error.

**Enforcement.** `.coderabbit.yaml` encoding OD-5, OD-6, OD-8, and OD-9 as required checks,
running as a CI job on every pull request, with `path_instructions` pointing at
`docs/engineering/CONSTITUTION.md`, `BUILD_PRINCIPLES.md`, and this addendum.

**Status.** PROPOSED. **Highest leverage per line of effort in this addendum.**

---

## 6 Documentation integrity

### OD-16 — Docs are reconciled against the present, automatically
**Rule.** Every load-bearing numeric or behavioural claim in a document is re-derived from code
or CI on a schedule. A doc that is stale is a defect, not a backlog item.

**Evidence.** Three concrete drifts found in one pass:
`GAP_READINESS.md:3` still reads "Generated: 2026-08-13 · HEAD: `48f28b0` (Sprint 36)" while its
own body describes Sprint 50 and `v1.3.3`; `GAP_READINESS.md:27` claims "2139 tests, 0 missing
of 12,139 statements" against an actual **2364 / 13,596**; and `07a7a1f` (dashboard deploy config)
is unreleased — after the `v1.3.3` tag — violating the repo's own release discipline.

**Enforcement.** A docs-drift CI job re-checking: the `GAP_READINESS.md` header against `git`,
its test and coverage counts against a real run, and that every registered strategy, CLI leaf,
and API operation still exists.

**Status.** PROPOSED.

---

## 7 Ratification and promotion

### 7.1 Promotion path

This addendum is **draft** and carries no authority until ratified. It does not amend
`CONSTITUTION.md`; it extends it. To promote:

1. Land **OD-14** (CodeRabbit) and **OD-16** (docs-drift) first — both are cheap, depend on
   nothing, and immediately catch the class of drift that produced most of this document.
2. Land the correctness pair — **OD-5 and OD-6** — together with the companion audit's B-1, B-2,
   and B-3, each with its proof shown failing before the fix.
3. Land **OD-9** before any further performance work. **OD-1/OD-2 must follow the B-1 fix**,
   because making the trading loop non-blocking while the staleness breaker is broken would trade
   *faster* on bad data.
4. Schedule **OD-8** (Decimal end-to-end) as its own migration with its own ADR.
5. Only then fold Principles into `CONSTITUTION.md` §2 via a normal version bump, CHANGELOG entry,
   signed tag, and push — the same discipline the repo already applies to releases.

### 7.2 Gate status

| ID | Gate exists? | Owner | Date |
|---|---|---|---|
| OD-1 · OD-2 | no | *unassigned* | — |
| OD-3 | no | *unassigned* | — |
| OD-4 | no | *unassigned* | — |
| OD-5 · OD-6 · OD-7 | no | *unassigned* | — |
| OD-8 | no | *unassigned* | — |
| OD-9 · OD-10 | no | *unassigned* | — |
| OD-11 · OD-12 · OD-13 | no | *unassigned* | — |
| OD-14 · OD-16 | no | *unassigned* | — |

**Every row is currently "no."** That is the honest state, and stating it is the point: this
repository has strong doctrine and no enforcement. Closing these rows is the work.

### 7.3 Review cadence

This addendum is reviewed whenever `CONSTITUTION.md` changes, whenever a gap-register score
changes, and at least annually. An entry that has been unenforced for more than two consecutive
sprints is either implemented or deleted — an unenforced principle decays into decoration.

---

## 8 Source evidence

| Claim in this addendum | Source |
|---|---|
| Principle 10's positive examples vs reality | `docs/engineering/FOUNDATIONS_AUDIT_2026-10-03.md` §1.4 |
| No CodeRabbit anywhere | `FOUNDATIONS_AUDIT` §3.1 |
| No flaky-test infrastructure | `FOUNDATIONS_AUDIT` §2.2 |
| numpy/pandas used by legacy-test-only code | `FOUNDATIONS_AUDIT` §5.1 |
| O(n·w) indicators, measured cost | `FOUNDATIONS_AUDIT` §5.2; `SPRINT_AUDIT` §2.1.1 |
| `win_rate=0.5` on both production paths | `FOUNDATIONS_AUDIT` §5.3 |
| Unwired portfolio rails | `FOUNDATIONS_AUDIT` §5.4 |
| `compute_max_drawdown` ZeroDivisionError | `FOUNDATIONS_AUDIT` §5.4(b) |
| Decimal abandoned at cycle entry | `FOUNDATIONS_AUDIT` §5.5 |
| Mocked seam in `test_cycle_executor.py:492` | `FOUNDATIONS_AUDIT` §2.4; `SPRINT_AUDIT` §2.4.1 |
| Three documentation drifts | `FOUNDATIONS_AUDIT` §6; `SPRINT_AUDIT` §2.5.2 |
| CI job inventory | `.github/workflows/ci.yml` |
| Doctrine drift is systematic | `FOUNDATIONS_AUDIT` §5.7 |
