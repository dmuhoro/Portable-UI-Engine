# ADR-010: Position Sizing Policy — Risk From Measured Win Rate, Not From Signal Confidence

**Status:** Accepted
**Date:** 2026-10-04
**Driver:** `Constitution.md` §"fail closed" and §"money is never binary float"; the
unsourced `confidence * 10` sizing multiplier discovered during the ADR-009 Decimal
migration; and the standing requirement that no business number ship without
provenance.

## Context

`PortfolioService.size_position` sized a position as:

```python
allocation = min(risk_per_trade * confidence * 10, 0.25)
```

Three separate defects live in that one line.

**1. The `* 10` is a magic constant with no source.** It appears in
`StrategyBase._param("confidence_multiplier", 10.0)` and again as a literal in the
sizing formula. Nothing derives it. It is not a Kelly fraction, not a leverage
limit, not a volatility adjustment. It is a number someone typed.

**2. `confidence` is not a probability, so it cannot scale risk.** Reading the
strategies that produce it (`src/traderos/domain/services/strategy_framework.py`):

```python
ratio = (fast - slow) / slow                       # threshold distance
multiplier = self._param("confidence_multiplier", 10.0)
confidence = min(ratio * multiplier, 1.0)          # score, clamped
```

`confidence` is *how far past its own entry threshold a signal travelled*, rescaled
by a per-strategy constant (`10.0` for `moving_average_trend`, `5.0` for
`volatility_breakout` and `mean_reversion`). It carries no information about the
probability that the trade wins. Feeding it into a risk budget treats a UI-facing
score as if it were an expectancy estimate — the same category of error as the
`win_rate=0.5` coin-flip defect fixed in `119576a`, one layer downstream.

**3. The strategies make `confidence == 0.0` unreachable, so the guard was
untestable theatre.** Every strategy returns `None` unless its threshold is already
breached, and a breached threshold implies `ratio > threshold > 0`, which implies
`min(ratio * multiplier, 1.0) > 0`. A `confidence`-based zero check therefore never
fires in production. It existed only to satisfy a unit test.

Meanwhile the sizing that *should* carry risk — the Bayesian win-rate estimate — is
still unimplemented, so `assess_trade` refuses every unsourced position. The net
effect of the old line was: risk budget silently scaled by a UI score, while the
one defensible risk input was absent.

## Decision

**1. Signal confidence never scales the risk budget.** It is removed from the
sizing contract entirely. It remains a legitimate *ranking* input — `SignalService`
resolves conflicting signals by `highest_confidence` — and it stays on `Signal`,
`Trade` and the audit trail for observability. It is not a risk input.

**2. `size_position` drops the `confidence` parameter from its signature.** A
parameter that is accepted and then ignored is worse than no parameter: it invites
the next author to assume it still matters. If it does not size, it is not there.

**3. Allocation is exactly `min(risk_per_trade, max_allocation)`.**

| Term | Value | Provenance |
|---|---|---|
| `risk_per_trade` | `0.02` | ADR-010. Conventional 2% fractional risk per trade. Operator-tunable via `RiskProfile`. |
| `max_allocation` | assessed Kelly fraction | `RiskService.assess_trade`. Quarter-Kelly of a measured, sourced win rate. **Absent a sourced win rate there is no position** — `assess_trade` refuses, so `max_allocation` is never fabricated. |
| quantity | `(cash * allocation / price).quantize(1e-8)` | 8dp mirrors the SQLite storage scale (ADR-009). |

Because `max_allocation` requires a sourced win rate, the two regimes are:

- **No measured win rate** → refuse the position. This is the default and it is the
  correct behaviour for a system that has not yet demonstrated edge.
- **Measured win rate present** → `min(0.02, quarter_kelly(p, b))` quantizes to
  8dp.

**4. `confidence == 0.0` is not a sizing refusal condition.** It is unreachable
upstream by construction, and a guard that cannot fire is not a guard. Signals are
rejected for *not existing* at the strategy gate; a strategy that returns a signal
has already passed its own threshold.

**5. `confidence_multiplier` is documented as score scaling, not risk.** The
per-strategy constants stay (they are needed to spread scores across `[0, 1]` for
ranking) but are named and commented as presentation, and are explicitly barred
from the money path.

**6. Stop and target remain ATR-derived and unchanged:** `stop = price - 2*ATR`,
`target = price + 3*ATR`, giving a payoff ratio `b = 1.5`. These stay available on a
refusal — refusing a size is not the same as pretending market data is missing.

## Consequences

**Good.** The money path stops consuming a number that means "how far past a
threshold" as though it meant "how likely to win". `confidence` keeps working where
it is genuinely useful (signal ranking, operator UI). The `* 10` magic constant is
gone from the risk calculation. Sizing now has one input that can defend itself —
a measured win rate — and when that is missing the system refuses instead of
guessing.

**Bad, and accepted.** Position size no longer varies with signal strength. Two
signals of very different quality receive the same allocation when both pass their
strategy gate. This is a real loss of nuance, accepted deliberately: the honest
version of that nuance requires a probability estimate, which is ADR-011's job. We
would rather size uniformly from measured expectancy than vary size from an
uncalibrated score.

**Neutral.** `assess_trade(..., confidence=...)` still accepts `confidence` because
it uses it as a minimum-strength gate (`confidence < min_confidence` refuses) and
records it on the assessment for audit. That is a *gate*, not a multiplier, and is
unchanged.

**Follow-on.** ADR-011 owns the win-rate estimator that makes `max_allocation`
real. Until ADR-011 ships and a strategy has a measured, cost-aware, sufficiently
sampled win rate, sizing refuses and the platform cannot open a position. That is
the intended state, not a defect.

## Rejected alternatives

- **Keep `confidence` in the signature, ignore it.** Rejected: a lying API invites
  the next author to re-introduce the multiplier.
- **Clamp `confidence` to a conservative range, e.g. `[0.5, 1.0]`.** Rejected: still
  treats a score as a probability, just more cautiously. Same category of error.
- **Replace `* 10` with a sourced constant.** Rejected: the problem is not the value,
  it is that a UI score is being multiplied into a risk budget at all.
- **Make `confidence` a proper probability now.** Rejected as out of scope and
  premature: it needs calibration data and a sample count, which is ADR-011, and
  inventing a probability from `ratio * multiplier` is precisely the fabrication
  `119576a` removed.
