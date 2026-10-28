# ADR-009: Money Representation — Decimal at the Boundary, Scaled Integers in SQLite

**Status:** Accepted
**Date:** 2026-10-03
**Driver:** Phase 3A of the 2026-10-03 directive; `Constitution.md` §"money is never
binary float"; and the `win_rate=0.5` defect (`119576a`), which was a fabricated
*number*, and whose natural successor is a fabricated *balance*.

## Context

`OHLCV` prices are already `Decimal`. Almost nothing else that represents money is.

| Surface | Current type |
|---|---|
| `Position.quantity`, `entry_price`, `current_price`, `pnl`, `realized_pnl` | `float` |
| `Trade.quantity`, `price`, `filled_quantity`, `filled_price` | `float` |
| `RiskService.assess_trade(price, equity, existing_gross_exposure, …)` | `float` |
| SQLite `trades`/`positions` money columns | `REAL` |
| SQLite `indicators.price_level` | `REAL` |
| `Metrics.total_return`, `max_drawdown`, `expectancy`, … | `float` |

The risk rails are the part that matters. `notional = quantity * price` and
`cap = equity * eff_max_pos` are the exact comparisons that decide whether real
money moves, and both are IEEE-754 double arithmetic. `0.1 + 0.2 != 0.3` is a
curiosity in a spreadsheet and a reconciliation defect in a position ledger: the
`broker_only_position` / `local_only_position` divergence class in G-02 exists
because the local book and the broker book are computed differently and compared
exactly.

Two failure modes follow from the current state, and both are silent:

- **Accumulated drift.** `realized_pnl` is summed across fills. Double addition
  does not associate, so a replay of the same fills can differ in the last bits
  from the original run. The causal-replay drill (G-05) reconstructs PnL by
  re-deriving it; it is comparing a float sum against a float sum and cannot
  distinguish "replayed correctly" from "replayed within rounding".
- **Boundary asymmetry.** `Decimal` market prices from `OHLCV` are converted to
  `float` at the edge of `Position` and `Trade`, so the value that is compared
  against a broker's decimal quantity is not the value that was ingested.

### The trap: `NUMERIC` in SQLite is not decimal

The obvious migration — declare the columns `NUMERIC` and bind `Decimal` — is a
false fix and must be rejected explicitly.

SQLite's NUMERIC affinity stores a value as INTEGER if it is losslessly
representable as one, and as REAL otherwise. `Decimal("1.10")` becomes the
double `1.100000000000000088817841970012523233890533447265625`. The type
affinity change is silent, there is no error, and the value is wrong in the same
way it was before the migration. A migration that swaps `REAL` for `NUMERIC` and
reports success would be exactly the kind of false protection the Constitution
forbids — it would pass every test written against it.

`TEXT` affinity is exact but is not a fix either: SQLite compares TEXT
lexicographically, so `'9.00' > '10.00'` is true. Any `ORDER BY`, `SUM`, or
`WHERE price < ?` over TEXT money is silently wrong. Text storage is correct only
with a fixed-width, zero-padded, scale-normalized encoding, which is to say a
scaled integer stored as text — strictly worse than storing the integer.

## Decision

1. **Domain and service layer: `Decimal`, always.** Every money value crossing a
   service boundary is `decimal.Decimal`. Quantity, price, notional, PnL, equity,
   cash, fees and commission are all `Decimal`. No `float` arithmetic is permitted
   to produce a value that is persisted or compared to a monetary threshold.
2. **Storage layer: scaled integers in minor units, stored as SQLite `INTEGER`.**
   Exact, orderable, summable in SQL. Each money column carries a declared scale
   in the schema comment and in the repository's field map:
   - price and money amounts: 8 decimal places (`PRICE_SCALE = 8`)
   - quantity: 8 decimal places (`QTY_SCALE = 8`), chosen because a BTC or SOL
     quantity needs more precision than an equity quantity, and one scale for all
     instruments is preferable to a per-instrument scale table that nothing else
     validates.
   Conversion is a single audited pair of helpers, `to_minor_units` /
   `from_minor_units`, with `ROUND_HALF_EVEN` stated explicitly and never left to
   the context default.
3. **Ratios and statistics stay `float`, deliberately.** `sharpe_ratio`,
   `sortino_ratio`, `win_rate`, `max_drawdown` as a fraction, `latency_bps`,
   `confidence` and every indicator coefficient are dimensionless and are *not*
   money. They stay `float`, and this is recorded here so it is a decision rather
   than an omission. `Metrics.total_return` and `Metrics.expectancy` are derived
   from money and are therefore migrated to `Decimal`; the ratios they feed remain
   `float`.
4. **Comparison thresholds are `Decimal`.** `max_position_size`,
   `max_gross_exposure`, `daily_loss_pct` and `equity` are converted to `Decimal`
   once at config resolution. A config float multiplied by a `Decimal` equity must
   raise rather than silently upcast — that is the tripwire for B-2-class defects
   recurring in the rails.
5. **Broker boundary.** Alpaca and Binance both accept decimal strings. The
   outbound adapter formats `Decimal` to the venue's documented precision and
   never routes a money value through `float`. A `TypeError` on `float * Decimal`
   is the intended failure mode, not a nuisance to be silenced with `cast`.
6. **Migration of existing rows.** Trade and position tables are migrated in
   place by a single audited script that reads each `REAL` value, converts via
   `Decimal(str(value))` — *not* `Decimal(value)`, which would bake the double's
   error in permanently — and writes the scaled integer. The script prints the
   row count and the maximum absolute change it observed, and refuses to complete
   if any row's change exceeds one minor unit. Existing `REAL` values are
   therefore preserved to the precision they actually had, and are not claimed to
   become more accurate.

## Rejected alternatives

- **`NUMERIC` columns (SQLite).** Rejected: silently stores REAL. Documented above.
- **`float` everywhere with tolerance comparisons.** Rejected: tolerance-based
  money comparison is how a reconciliation gap becomes permanent. The whole point
  is to make equality exact so a divergence means a divergence.
- **`TEXT` money columns.** Rejected: lexicographic comparison is wrong for
  non-fixed-width values.
- **Migrate the broker's `str` quantities at the edge only.** Rejected: leaves the
  local book in float, which is the side that diverged in G-02.
- **Big-integer micro-units at 18dp for everything.** Rejected as premature:
  quantity precision requirements are not yet established across the full venue
  list, and 8dp already covers the pilot instruments. Revisit only with evidence
  that 8dp truncates a real venue order.

## Consequences

- **Positive:** `realized_pnl` sums are exactly reproducible, so G-05 causal
  replay compares like with like. Reconciliation comparisons become exact. The
  `Decimal` × `float` tripwire turns a future float-money regression into a
  `TypeError` at the boundary instead of a silent rounding defect.
- **Negative:** This is a wide change. It touches the two entities, the risk
  service, both SQL backends, the paper-trading service, the broker adapters and
  their tests. It is expected to be the largest single item in this directive.
- **Negative:** `RiskService.assess_trade` and its callers change signature. The
  win-rate provider seam added in `119576a` must accept `Decimal` equity.
- **Negative:** Scaled integers make raw SQL reports unreadable (`1843257000000`
  for `$18,432.57`) and require the scale to be applied in every ad-hoc query an
  operator writes by hand. Documented in the schema and in the repository.
- **Accepted risk:** 8dp quantity cannot represent a venue that requires more.
  Mitigated by the conversion helper raising on excess precision rather than
  rounding silently.

## Implementation

- `Money` helpers in the domain layer: `to_minor_units`, `from_minor_units`, and
  the `PRICE_SCALE` / `QTY_SCALE` constants, with round-trip tests including the
  values that historically exposed the bug (`0.1`, `1.005`, `1.10`, `2.675`).
- `Position` and `Trade` money fields become `Decimal`; `Metrics.total_return`
  and `Metrics.expectancy` follow.
- `RiskService.assess_trade` takes `Decimal` price, equity and exposure.
- SQLite schema: `quantity`, `price`, `filled_quantity`, `filled_price`,
  `entry_price`, `current_price`, `pnl`, `realized_pnl`, `price_level` become
  `INTEGER` with the scale documented beside each.
- PostgreSQL backend receives matching `NUMERIC(20,8)` columns and must be
  reviewed separately, since unlike SQLite it stores decimal exactly.
- Proof obligation: a test that stores `0.1 + 0.2` and `0.3` as separate fills
  and asserts the summed `realized_pnl` equals `Decimal("0.3")` exactly. This test
  **fails on the pre-migration code**, which is the required proof that the gate
  is real and not decorative.
