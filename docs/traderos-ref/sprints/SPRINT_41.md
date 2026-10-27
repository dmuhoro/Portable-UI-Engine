# Sprint 41 — Product completeness: deep audit, honest backtest, durable research store, pagination, real-feed wiring

**Period:** 2026-08-20
**Objective:** Close the software-closeable slices identified by a deep
codebase audit on the road to GO for real capital, and record the product's
true state. Four concrete gaps closed without touching the execution/order
path: (1) `POST /v1/backtest` fabricated synthetic candles and never touched
real data — now it runs the engine against the real ingested candle series and
fails closed on unknown/empty symbols; (2) the research store
(observations/hypotheses/experiments/results/lessons) was **in-memory only** —
lost on every restart — now wired to durable SQLite and Postgres repos; (3)
list endpoints were unbounded — now paginated with `limit`/`offset`; (4) the
real Binance feed could only be enabled by editing committed YAML — now
switchable on a deployed instance via env vars. The audit also corrected two
stale claims in the readiness docs (operator login and market/research
endpoints were already shipped in prior sprints). The README was rewritten as
a living product-state document.

---

## 1. Deep audit & codebase index

A full inventory of `src/traderos` (190 modules), the 55+ route `/v1` API, the
data layer, migrations (v001–v008), and the test suite (143 files) was
produced and verified against the live deployment. Key findings:

- **`POST /v1/backtest` was pure synthetic data** (`server.py:353-368`): it
  built a deterministic price ramp (`open=100+i`, volume 1000, all candles on
  `2024-01-01`) and never touched the data feed. Any UI showing this result
  displayed fabricated-in-place numbers.
- **Research store was in-memory only** (`factory.py:418-424`): `ResearchService`
  was wired to `InMemory*Repository`, so observations/hypotheses/experiments/
  lessons were **lost on restart**. Full SQLite implementations existed but were
  never wired; no Postgres implementation existed.
- **No pagination**: audit/trades/positions/orders/strategies/manifest/paper-
  trade sessions returned unbounded lists (only a bare `limit` on some routes).
- **Real feed off in shipped config**: `settings.yaml` sets
  `binance.enabled: false`; the deployed instance served mock data, and there
  was no env-var override.
- **Corrections to stale docs**: the earlier frontend audit claimed operator
  login used a `localStorage` API key and that Market/Research had no backend.
  Verified against code: WP8 session login (`POST /v1/auth/login`,
  `sessionStorage`) and WP9 market/research endpoints were **already shipped**
  and are covered by passing tests. These claims were corrected, not re-built.

## 2. Honest backtest (server.py)

`POST /v1/backtest` now:
- Accepts a `symbol` (default `BTCUSDT`) and runs the engine against the
  **real ingested candle series** from `DataIngestionService` — the same data
  the live loop consumes.
- **Fails closed**: unknown strategy → 404, unknown/empty symbol → 404, missing
  data service → 503, empty candle series → 404. A UI can never display a
  fabricated-in-place result.
- Returns `symbol` and `candles` count so consumers know what was actually
  tested.

The existing `POST /v1/research/backtest` already used real candles; the plain
`/v1/backtest` endpoint is now consistent with it.

## 3. Durable research store

- Wired the existing SQLite research repos (`SQLiteObservationRepository`,
  `SQLiteHypothesisRepository`, `SQLiteExperimentRepository`,
  `SQLiteExperimentResultRepository`, `SQLiteLessonRepository`) into
  `build_orchestrator` for the SQLite backend.
- **Added Postgres implementations** (`postgres/research.py`) for the
  production store, using positional row access to match the psycopg2 tuple
  convention used by the other Postgres repos.
- Research data now survives restart/crash on both SQLite and Postgres
  backends; the in-memory repos remain the no-DB (test) fallback.

## 4. Pagination

Added consistent `limit`/`offset` to the unbounded list endpoints:
- `/v1/audit` (offset added; limit bounded 1..100)
- `/v1/manifest` (limit/offset; limit bounded 1..1000)
- `/v1/trades` (limit/offset; limit bounded 1..1000)
- `/v1/positions` (optional limit + offset)
- `/v1/orders` (optional limit + offset)
- `/v1/strategies` (optional limit + offset)
- `/v1/papertrade/sessions` (optional limit + offset)

`RunManifest.get_runs` gained `offset` on both the in-memory and durable
implementations.

## 5. Real-feed wiring via env vars

Added `_env_flag` helper and `BINANCE_ENABLED` / `BINANCE_STREAMING` env-var
overrides so an operator can switch the real Binance feed on for a deployed
instance (Railway Variables) **without editing committed YAML**. The committed
default stays off so CI/tests remain network-free (Constitution §2 Principle 6).
Precedence: env var wins over config; unset falls back to config. `.env.example`
was refreshed with the full current variable set.

## 6. README as living product-state doc

Rewrote `README.md` from a stale static feature list into a living
product-state document: current status table (tests, CI, release, live
deploy, governance), what the product does today (core loop, risk rails, data,
API, dashboard, research, security, CLI), an honest gap register with the
software-closeable vs operator-run vs account-gated split, and the full
architecture + env reference.

## 7. Verification

| Check | Result |
|---|---|
| `pytest` (full suite) | **2259 passed, 7 skipped, 100.00%** coverage (gate 100) |
| `ruff check .` | All checks passed |
| `black --check .` | 368 files left unchanged |
| `pyright` (strict, `src/traderos`) | 0 errors, 0 warnings |
| `pre-commit --all-files` | All hooks Passed |
| Postgres research repo tests | 6 new tests, pass against local PG 16 |
| Backtest honesty tests | 3 tests (incl. fail-closed unknown symbol), pass |
| Env-override tests | 2 tests, pass |
| Pagination tests | positions/orders/strategies/trades/paper-sessions + manifest offset tests, pass |

## 8. Governance / honesty notes

- The execution/order path was **not touched** — per the directive, real order
  execution is tested last.
- Real market data on the deployed instance still requires an operator to set
  `BINANCE_ENABLED=true` and a ≥24h run with the data-gap breaker armed; this
  sprint provides the mechanism, not the run.
- The 24–72h unattended Alpaca paper soak, managed-Vault rotation cadence, and
  live on-call delivery remain operator-run gates (harness ready).
- No real order has ever been submitted; real Alpaca connectivity is proven
  read-only once. GO for real capital remains **NO-GO** until the exit tests in
  `GAP_READINESS.md` are met.
