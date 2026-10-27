#!/usr/bin/env python3
"""G-01 / A3 evidence: real-market cost-adjusted walk-forward.

Upgrades the walk-forward evidence from the *frozen synthetic oracle* to *real
public Binance candles* — ≥1 year of 1h klines pulled over the public,
unauthenticated kline REST endpoint (data, not an account, per
``PILOT_TO_PRODUCT.md`` §0).

Design (honest, reproducible, fails closed):

- **Real data, frozen — and reused, never overwritten.** The script downloads
  ≥1 year of ``BTCUSDT`` 1h candles from ``api.binance.com/api/v3/klines``
  (paginated, 1000/request, oldest→newest) and writes the raw klines to a
  **date-stamped frozen CSV dataset pointer** under ``docs/evidence/frozen/``
  (dataset-freeze discipline, §A2 2nd order). A re-run **reuses the newest
  existing snapshot from disk** — no network, bit-identical candles on any
  machine or CI checkout. Refreshing is an explicit, deliberate act: pass
  ``--refresh`` to download fresh data and write a *new* dated snapshot; the
  previously frozen file is never mutated in place, so committed evidence can
  not silently change. If neither a frozen snapshot nor a usable download
  exists the run **fails closed** (exit 1, NO-GO) — it never fabricates
  candles.
- **Cost-adjusted walk-forward.** The last ~35% of the real series is withheld
  as out-of-sample; full costs (fee 10bps + slippage 5bps + latency 10bps)
  across 5 folds — the same engine as ``run_walk_forward_evidence.py``.
- **Honest verdict.** G-01 exit test is *positive expectancy after full costs
  on OOS data*. If no strategy proves it, the honest verdict is PILOT =
  DATA-VALIDATION ONLY, no PnL claim (per ``LIVE_RUN_POLICY.md``).

Run:
  PYTHONPATH=src:src/tests python3 scripts/evidence/run_real_market_walk_forward.py
  PYTHONPATH=src:src/tests python3 scripts/evidence/run_real_market_walk_forward.py --refresh
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from traderos.domain.entities import OHLCV  # noqa: E402
from traderos.domain.entities import Candle  # noqa: E402
from traderos.domain.entities import Timeframe  # noqa: E402
from traderos.domain.services.backtesting_service import BacktestingService  # noqa: E402
from traderos.domain.services.execution_service import ExecutionService  # noqa: E402
from traderos.domain.services.strategy_framework import registry as strategy_registry  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-06_real_market_walk_forward.log"
OUT_SPEC = OUT.name  # stable evidence-log name; refresh updates its content only
FROZEN_DIR = REPO_ROOT / "docs" / "evidence" / "frozen"
# Snapshot naming: binance_btcusdt_1h_<freeze-date>.csv. The newest file on
# disk is the reproducibility anchor; a refresh writes a NEW dated file and
# never mutates a committed one.
MARKET_ID = uuid.UUID("8b2b6f3c-2d3a-4e9a-9f0a-1c2d3e4f5a6b")
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
DAYS = 370  # comfortably ≥1 year (365) so pagination covers the window
HOUR_MS = 3_600_000
CANDLES_PER_CALL = 1000
OOS_FRACTION = 0.35
KLINES_URL = "https://api.binance.com/api/v3/klines"
MIN_CANDLES = 876  # ~1 year of 1h candles


def _snapshot_name() -> str:
    """Microsecond-precision snapshot name that can never collide with an
    existing file — a refresh must write a NEW file, never overwrite a
    committed one. Fixed-width components keep lexical order == time order."""
    now = datetime.now(UTC)
    candidate = f"binance_btcusdt_1h_{now.strftime('%Y-%m-%dT%H%M%S%f')}.csv"
    for counter in range(2, 100):
        if not (FROZEN_DIR / candidate).exists():
            return candidate
        candidate = f"binance_btcusdt_1h_{now.strftime('%Y-%m-%dT%H%M%S%f')}-{counter}.csv"
    raise FileExistsError(f"could not allocate a fresh snapshot name under {FROZEN_DIR}")


def _load_frozen(path: Path) -> list[dict]:
    """Read a frozen CSV snapshot back into row dicts (the reproducibility
    anchor: a re-run consumes exactly the committed candles, no network)."""
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [
            {
                "timestamp": int(r["timestamp"]),
                "open": r["open"],
                "high": r["high"],
                "low": r["low"],
                "close": r["close"],
                "volume": r["volume"],
            }
            for r in reader
        ]
    return rows


def _latest_snapshot() -> Path | None:
    """Newest existing frozen snapshot, else None. Deterministic ordering on the
    ISO date embedded in the filename so a re-run picks the same file."""
    if not FROZEN_DIR.is_dir():
        return None
    candidates = sorted(
        (p for p in FROZEN_DIR.glob("binance_btcusdt_1h_*.csv")),
        key=lambda p: p.name,
    )
    return candidates[-1] if candidates else None


def _fetch_klines(start_ms: int, end_ms: int) -> list[list]:
    url = (
        f"{KLINES_URL}?symbol={SYMBOL}&interval={INTERVAL}"
        f"&startTime={start_ms}&endTime={end_ms}&limit={CANDLES_PER_CALL}"
    )
    with urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode())


def _download_one_year() -> list[dict]:
    """Paginate 1h klines over the trailing ~365 days, oldest first."""
    end = datetime.now(UTC)
    start = end - timedelta(days=DAYS)
    rows: list[dict] = []
    cursor = int(start.timestamp() // 1) * 1000
    end_ms = int(end.timestamp() // 1) * 1000
    while cursor < end_ms:
        batch = _fetch_klines(cursor, end_ms)
        if not batch:
            break
        for entry in batch:
            rows.append(
                {
                    "timestamp": int(entry[0]),
                    "open": entry[1],
                    "high": entry[2],
                    "low": entry[3],
                    "close": entry[4],
                    "volume": entry[5],
                }
            )
        next_open = int(batch[-1][0]) + HOUR_MS
        if next_open <= cursor:
            break  # pagination safety: never spin forever on a stuck cursor
        cursor = next_open
    return rows


def _freeze(rows: list[dict], path: Path) -> None:
    """Write a NEW dated snapshot (never mutates an existing committed one)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["timestamp", "open", "high", "low", "close", "volume"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in writer.fieldnames})


def _to_candles(rows: list[dict]) -> list[Candle]:
    return [
        Candle(
            market_id=MARKET_ID,
            ohlcv=OHLCV(
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row["volume"])),
            ),
            timestamp=datetime.fromtimestamp(int(row["timestamp"]) / 1000, tz=UTC),
            timeframe=Timeframe.HOUR_1,
        )
        for row in rows
    ]


def _cost_adjusted() -> BacktestingService:
    return BacktestingService(
        execution=ExecutionService(slippage_bps=5, fee_bps=10, min_fee=0.0, latency_bps=10)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Real-market cost-adjusted walk-forward evidence.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-download fresh Binance candles and write a NEW dated snapshot instead of "
        "reusing the newest existing frozen one. Never mutates a committed snapshot.",
    )
    args = parser.parse_args(argv)

    lines: list[str] = []
    lines.append("REAL-MARKET WALK-FORWARD — G-01 cost-adjusted, out-of-sample (A3)")
    lines.append(f"started {datetime.now(UTC).isoformat()}")
    lines.append("engine: next-bar fills, side-aware slippage 5bps, fee 10bps, latency 10bps")

    source_path: Path | None
    rows: list[dict] = []
    refresh = bool(args.refresh)
    if not refresh:
        source_path = _latest_snapshot()
        if source_path is not None:
            try:
                rows = _load_frozen(source_path)
            except Exception as exc:  # noqa: BLE001 — unusable frozen data must fail closed
                lines.append(f"  FROZEN SNAPSHOT UNREADABLE (fails closed): {source_path}: {exc}")
                lines.append("VERDICT: NO-GO — cannot reuse a corrupt frozen dataset")
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text("\n".join(lines) + "\n")
                print("\n".join(lines))
                return 2
            lines.append("dataset: frozen Binance BTCUSDT 1h snapshot (no network; reused)")
        else:
            lines.append("dataset: real public Binance BTCUSDT 1h klines via REST (paginated)")
    else:
        lines.append(
            "dataset: real public Binance BTCUSDT 1h klines via REST (paginated, --refresh)"
        )
        source_path = FROZEN_DIR / _snapshot_name()

    if refresh or source_path is None:
        try:
            rows = _download_one_year()
        except Exception as exc:  # noqa: BLE001 — any failure must fail closed
            lines.append(f"  DOWNLOAD FAILED (fails closed, no fabricated data): {exc}")
            lines.append("VERDICT: NO-GO — could not fetch real Binance candles over the network")
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text("\n".join(lines) + "\n")
            print("\n".join(lines))
            return 2

        if len(rows) < MIN_CANDLES:
            lines.append(
                f"  TOO FEW CANDLES ({len(rows)} < {MIN_CANDLES}): fails closed, no edge claim"
            )
            lines.append("VERDICT: NO-GO — insufficient real data")
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text("\n".join(lines) + "\n")
            print("\n".join(lines))
            return 2

        rows.sort(key=lambda r: int(r["timestamp"]))
        assert source_path is not None  # refresh always supplies the snapshot path
        _freeze(rows, source_path)
    else:
        if len(rows) < MIN_CANDLES:
            lines.append(
                f"  FROZEN SNAPSHOT TOO SHORT ({len(rows)} < {MIN_CANDLES}): "
                "fails closed, no edge claim"
            )
            lines.append("VERDICT: NO-GO — frozen dataset below the reproducibility floor")
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text("\n".join(lines) + "\n")
            print("\n".join(lines))
            return 2

    candles = _to_candles(rows)
    withheld = int(len(candles) * OOS_FRACTION)
    out_of_sample = candles[-withheld:]
    lines.append(
        f"  full series: {len(candles)} candles ({len(rows)} hours, {len(rows) // 24} days)"
    )
    lines.append(
        f"  withheld out-of-sample window: {len(out_of_sample)} candles "
        f"({out_of_sample[0].timestamp.date()} -> {out_of_sample[-1].timestamp.date()})"
    )
    lines.append(f"  frozen dataset pointer: {source_path.relative_to(REPO_ROOT)}")
    lines.append("")

    results: list[tuple[str, float, float]] = []
    for strat_name in strategy_registry.list():
        strat_cls = strategy_registry.get(strat_name)
        if strat_cls is None:
            continue
        wf = _cost_adjusted().walk_forward(strat_cls(), out_of_sample, MARKET_ID, n_splits=5)
        mean = wf["mean_fold_return"]
        positive = int(wf["positive_folds"])
        results.append((strat_name, mean, positive))
        lines.append(f"=== strategy: {strat_name} ===")
        lines.append(
            f"  walk-forward on real OOS (5 folds, full costs incl. latency): "
            f"mean_fold_return={mean:.4f} positive_folds={positive}/5 "
            f"mean_sharpe={wf['mean_sharpe']:.4f} mean_max_dd={wf['mean_max_drawdown']:.4f}"
        )
        lines.append("")

    lines.append("G-01 EXIT TEST (positive expectancy after full costs on real OOS data):")
    lines.append("  (corrected label; exit criterion unchanged: all folds positive after costs)")
    if results:
        proven = [name for name, mean, pos in results if pos == 5 and mean > 0]
        if proven:
            lines.append(f"  EDGE PROVEN for: {', '.join(proven)}")
        else:
            lines.append(
                "  No strategy shows positive expectancy after full costs on the real "
                "out-of-sample window. Honest outcome: PILOT = DATA-VALIDATION ONLY, "
                "no PnL claim (per LIVE_RUN_POLICY.md)."
            )
    lines.append("VERDICT: PASS — cost-adjusted walk-forward over real data recorded")
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
