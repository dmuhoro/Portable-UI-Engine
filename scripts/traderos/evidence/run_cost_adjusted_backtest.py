"""G-01 evidence: cost-adjusted backtest + walk-forward on REAL Alpaca data.

Reproducible drill for the Sprint 25 gap-closure. Requires live Alpaca read
keys in the environment (ALPACA_API_KEY / ALPACA_SECRET_KEY) — never committed;
this script only prints and writes an evidence log.

Run:
    ALPACA_API_KEY=... ALPACA_SECRET_KEY=... python3 scripts/evidence/run_cost_adjusted_backtest.py
"""

from __future__ import annotations

import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from traderos.domain.collectors.base import DataCollector
from traderos.domain.services.backtesting_service import BacktestingService
from traderos.domain.services.execution_service import ExecutionService
from traderos.domain.services.historical_data import HistoricalDataService
from traderos.domain.services.strategy_framework import registry as strategy_registry
from traderos.infrastructure.collectors.alpaca_collector import AlpacaCollector

EVIDENCE = Path("docs/evidence/2026-08-04_sprint25_cost_adjusted_backtest.log")


def _log(lines: list[str]) -> None:
    text = "\n".join(lines) + "\n"
    print(text, end="")
    EVIDENCE.write_text(text)


def main() -> int:
    lines: list[str] = []
    lines.append("=== Sprint 25 G-01 cost-adjusted backtest drill host=2026-08-04 ===")
    lines.append("")

    collectors: dict[str, DataCollector] = {"alpaca": AlpacaCollector()}
    service = HistoricalDataService(collectors=collectors)
    try:
        candles = service.get_candles(
            "alpaca",
            "1h",
            "BTC/USD",
            limit=500,
            start=datetime.now(UTC) - timedelta(days=120),
            use_cache=False,
        )
    except Exception as e:  # noqa: BLE001
        lines.append(f"FATAL: could not fetch real data: {e}")
        lines.append("NO-GO: real-data evidence unavailable; no edge claim possible.")
        _log(lines)
        return 1

    lines.append(f"Real data: Alpaca BTC/USD 1h, {len(candles)} candles")
    lines.append(f"  period {candles[0].timestamp.date()} -> {candles[-1].timestamp.date()}")
    lines.append("")

    for strat_name in strategy_registry.list():
        strat_cls = strategy_registry.get(strat_name)
        if strat_cls is None:
            continue
        no_cost = BacktestingService(execution=ExecutionService(slippage_bps=0, fee_bps=0))
        costed = BacktestingService(
            execution=ExecutionService(slippage_bps=5, fee_bps=10, min_fee=0.0, latency_bps=10)
        )
        r0, _ = no_cost.run(strat_cls(), candles, candles[0].market_id)
        r1, _ = costed.run(strat_cls(), candles, candles[0].market_id)
        wf = costed.walk_forward(strat_cls(), candles, candles[0].market_id, n_splits=5)
        folds = wf["fold_returns"]
        edge = len(folds) == 5 and all(x > 0 for x in folds)
        lines.append(f"=== strategy: {strat_name} ===")
        lines.append(
            f"  no-cost : total_return={r0.metrics.total_return:.4f} "
            f"trades={r0.metrics.total_trades}"
        )
        lines.append(
            f"  costed  : total_return={r1.metrics.total_return:.4f} "
            f"trades={r1.metrics.total_trades} "
            f"max_dd={r1.metrics.max_drawdown:.4f} sharpe={r1.metrics.sharpe_ratio:.4f}"
        )
        lines.append(
            f"  walk-forward (5 folds, costed): mean_fold_return="
            f"{wf['mean_fold_return']:.4f} positive_folds={int(wf['positive_folds'])}/5 "
            f"mean_sharpe={wf['mean_sharpe']:.4f} folds={[round(x,4) for x in folds]}"
        )
        lines.append(f"  EDGE PROVEN: {'YES' if edge else 'NO'}")
        lines.append("")

    lines.append("EDGE VERDICT (G-01 exit test is cost-adjusted walk-forward):")
    lines.append("  A positive mean fold return across ALL 5 out-of-sample folds after")
    lines.append("  full costs is the only acceptable proof of an edge for a real-capital")
    lines.append("  pilot. No strategy above passes that bar, so the honest outcome is")
    lines.append("  PILOT = DATA-VALIDATION ONLY, no PnL claim.")
    _log(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
