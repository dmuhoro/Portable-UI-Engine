#!/usr/bin/env python3
"""G-06 evidence: engine conformance against the frozen reference oracle.

Locks the backtest engine to the committed reference PnL on both the full
frozen dataset and a withheld (out-of-sample) window. If the engine's
fill/cost/indicator semantics drift, this drill fails — the same guarantee
``tests/test_backtest_oracle.py`` gives in the suite, recorded as standing
evidence for the G-06 exit test.

Run:  PYTHONPATH=src:tests python3 scripts/evidence/run_oracle_conformance.py
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

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-04_sprint27_oracle_conformance.log"

# Committed reference (2026-10-04, cost-adjusted engine: 5bps slippage, 10bps
# fee, ADR-010 sizing). Must match tests/test_backtest_oracle.py.
#
# Re-baselined from the 2026-08-04 reference (-0.094886 / -0.028102). The old
# engine sized a position as `signal.confidence * 10` SHARE COUNT, ignoring cash
# and price entirely, so it was not capital-aware (invariant I5). Trade counts
# are identical before and after (55 / 18), which is the evidence that only
# sizing moved and no entry/exit decision changed.
REFERENCE_FULL_RETURN = -0.102948983850274
REFERENCE_FULL_TRADES = 55
REFERENCE_WITHHELD_RETURN = -0.0267217407694787
REFERENCE_WITHHELD_TRADES = 18
TOLERANCE = 1e-4


def _cost_adjusted() -> BacktestingService:
    return BacktestingService(execution=ExecutionService(slippage_bps=5, fee_bps=10, min_fee=0.0))


def main() -> int:
    lines: list[str] = []
    lines.append("ORACLE CONFORMANCE — G-06 frozen reference PnL lock")
    lines.append(f"started {datetime.now(UTC).isoformat()}")

    strat_cls = strategy_registry.get("moving_average_trend")
    if strat_cls is None:
        lines.append("FAIL: moving_average_trend strategy not registered")
        OUT.write_text("\n".join(lines) + "\n")
        return 1

    candles = oracle_candles()
    results: list[tuple[str, bool]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        results.append((name, ok))
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    result, _ = _cost_adjusted().run(strat_cls(), candles, MARKET_ID)
    trades_ok = result.metrics.total_trades == REFERENCE_FULL_TRADES
    return_ok = abs(result.metrics.total_return - REFERENCE_FULL_RETURN) < TOLERANCE
    check(
        "full_frozen_dataset",
        trades_ok and return_ok,
        f"trades={result.metrics.total_trades} (want {REFERENCE_FULL_TRADES}), "
        f"return={result.metrics.total_return:.6f} (want {REFERENCE_FULL_RETURN})",
    )

    withheld = oracle_candles()[-70:]
    wresult, _ = _cost_adjusted().run(strat_cls(), withheld, MARKET_ID)
    wtrades_ok = wresult.metrics.total_trades == REFERENCE_WITHHELD_TRADES
    wreturn_ok = abs(wresult.metrics.total_return - REFERENCE_WITHHELD_RETURN) < TOLERANCE
    check(
        "withheld_window",
        wtrades_ok and wreturn_ok,
        f"trades={wresult.metrics.total_trades} (want {REFERENCE_WITHHELD_TRADES}), "
        f"return={wresult.metrics.total_return:.6f} (want {REFERENCE_WITHHELD_RETURN})",
    )

    passed = sum(1 for _, ok in results if ok)
    verdict = "PASS" if passed == len(results) else "FAIL"
    lines.append("")
    lines.append(
        f"VERDICT: {verdict} — engine reproduces committed reference PnL on "
        f"{passed}/{len(results)} conformance cases (tolerance {TOLERANCE})"
    )
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
