#!/usr/bin/env python3
"""G-01 evidence: cost-adjusted walk-forward with a withheld out-of-sample
window, over the frozen G-06 oracle dataset.

This is the keyless, reproducible companion to
``run_cost_adjusted_backtest.py`` (which needs live Alpaca keys). It exercises
the exact same cost model — side-aware slippage, fee floor, and **latency** —
against a frozen, committed candle set so the run is bit-identical on any
machine. A withheld window (the last ~third of the series) is the
out-of-sample region: an edge that only exists in-sample is not an edge.

The G-01 exit test is *positive expectancy after full costs on out-of-sample
data*. If no strategy clears that bar, the honest verdict is PILOT =
DATA-VALIDATION ONLY (no PnL claim), exactly as ``LIVE_RUN_POLICY.md`` requires.

Run:  PYTHONPATH=src:src/tests python3 scripts/evidence/run_walk_forward_evidence.py
"""

from __future__ import annotations

import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from backtest_oracle_dataset import MARKET_ID  # noqa: E402
from backtest_oracle_dataset import oracle_candles  # noqa: E402

from traderos.domain.services.backtesting_service import BacktestingService  # noqa: E402
from traderos.domain.services.execution_service import ExecutionService  # noqa: E402
from traderos.domain.services.strategy_framework import registry as strategy_registry  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-04_sprint27_walk_forward_evidence.log"


def _cost_adjusted() -> BacktestingService:
    return BacktestingService(
        execution=ExecutionService(slippage_bps=5, fee_bps=10, min_fee=0.0, latency_bps=10)
    )


def main() -> int:
    lines: list[str] = []
    lines.append("WALK-FORWARD EVIDENCE — G-01 cost-adjusted, out-of-sample")
    lines.append(f"started {datetime.now(UTC).isoformat()}")
    lines.append("engine: next-bar fills, side-aware slippage 5bps, fee 10bps, latency 10bps")
    lines.append("dataset: frozen G-06 oracle candles (reproducible on any machine)")

    candles = oracle_candles()
    withheld = int(len(candles) * 0.35)
    out_of_sample = candles[-withheld:]
    lines.append(f"  full series: {len(candles)} candles")
    lines.append(
        f"  withheld out-of-sample window: {len(out_of_sample)} candles "
        f"({out_of_sample[0].timestamp.date()} -> {out_of_sample[-1].timestamp.date()})"
    )
    lines.append("")

    results: list[tuple[str, float, float]] = []
    for strat_name in strategy_registry.list():
        strat_cls = strategy_registry.get(strat_name)
        if strat_cls is None:
            continue
        wf = _cost_adjusted().walk_forward(strat_cls(), out_of_sample, MARKET_ID, n_splits=5)
        mean = wf["mean_fold_return"]
        positive = int(wf["positive_folds"])
        edge = len(wf["fold_returns"]) == 5 and positive == 5 and mean > 0
        results.append((strat_name, mean, positive))
        lines.append(f"=== strategy: {strat_name} ===")
        lines.append(
            f"  walk-forward on withheld OOS (5 folds, full costs incl. latency): "
            f"mean_fold_return={mean:.4f} positive_folds={positive}/5 "
            f"mean_sharpe={wf['mean_sharpe']:.4f} mean_max_dd={wf['mean_max_drawdown']:.4f} "
            f"folds={[round(x, 4) for x in wf['fold_returns']]}"
        )
        lines.append(f"  EDGE PROVEN (all folds positive after costs): {'YES' if edge else 'NO'}")
        lines.append("")

    proven = [name for name, mean, pos in results if pos == 5 and mean > 0]
    lines.append("G-01 EXIT TEST (positive expectancy after full costs on OOS data):")
    if proven:
        lines.append(f"  EDGE PROVEN for: {', '.join(proven)}")
    else:
        lines.append(
            "  No strategy shows positive expectancy after full costs on the "
            "out-of-sample window. Honest outcome: PILOT = DATA-VALIDATION ONLY, "
            "no PnL claim (per LIVE_RUN_POLICY.md)."
        )
    verdict = "PASS"  # evidence recorded either way; the edge claim is the callout above
    lines.append(f"VERDICT: {verdict} — cost-adjusted walk-forward evidence recorded")
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
