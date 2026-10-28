#!/usr/bin/env python3
"""Sprint 45 evidence: LIVE WS-resync reconciliation drill against real Binance.

Closes the G-02 residual "WS resync vs live API untested" on the real wire:

  1. Connect the real aggTrade WebSocket (BTCUSDT) through the production
     ``StreamingMarketDataService`` + ``StreamingMarketDataCollector`` chain
     and let at least one full minute-candle close.
  2. Force a real transport outage by closing the underlying websocket while
     the run loop is consuming — exactly the failure mode resync exists for.
     This is repeated a few times to exercise multiple reconnects.
  3. After the final reconnect, reconcile fires automatically; then the drill
     independently verifies CONVERGENCE: every fully-closed candle in the
     live cache matches the official REST kline for the same minute within
     tolerance, with no missing minutes in between (gapless series).

PASS requires: >=1 proven resync, zero reconcile failures, and a gapless,
kline-matching closed-candle series. The drill never fabricates market data;
if Binance is unreachable it exits NO-GO.

Run:
    PYTHONPATH=. python3 scripts/evidence/run_ws_resync_drill.py
"""

from __future__ import annotations

import argparse
import time
from datetime import UTC
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from traderos.domain.collectors.base import CollectorOHLCV
from traderos.infrastructure.collectors.binance_collector import BinanceCollector
from traderos.infrastructure.collectors.streaming_collector import StreamingMarketDataCollector
from traderos.infrastructure.market_stream import BinanceStreamTransport
from traderos.infrastructure.market_stream import StreamingMarketDataService

REPO_ROOT = Path(__file__).resolve().parents[2]

SYMBOL = "BTCUSDT"
INTERVAL_S = 60


def _closed_klines(limit: int) -> dict[int, CollectorOHLCV]:
    """Official REST klines keyed by bucket-start epoch second."""
    rows = BinanceCollector().fetch_historical(SYMBOL, "1m", limit=limit)
    now = datetime.now(tz=UTC)
    out: dict[int, CollectorOHLCV] = {}
    for row in rows:
        if (now - row.timestamp).total_seconds() < INTERVAL_S:
            continue  # still forming at the exchange — not truth yet
        out[int(row.timestamp.timestamp())] = row
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--phase-a-seconds", type=float, default=130.0)
    parser.add_argument("--settle-seconds", type=float, default=95.0)
    parser.add_argument("--outages", type=int, default=3)
    args = parser.parse_args()

    started = datetime.now(UTC).isoformat()
    lines = [
        "WS-RESYNC RECONCILIATION DRILL (real Binance WS + REST klines)",
        f"started {started} symbol={SYMBOL} interval={INTERVAL_S}s",
        (
            f"plan: {args.phase_a_seconds:.0f}s live capture, {args.outages} forced "
            f"outages, {args.settle_seconds:.0f}s settle, then convergence check"
        ),
    ]
    print("\n".join(lines))

    transport = BinanceStreamTransport()
    service = StreamingMarketDataService(transport, reconnect_limit=10)
    collector = StreamingMarketDataCollector(
        stream=service,
        backfill=BinanceCollector(),
        interval_seconds=INTERVAL_S,
    )
    collector.subscribe([SYMBOL])

    import threading

    runner_thread = threading.Thread(
        target=service.run, kwargs={"max_messages": None}, name="drill-stream", daemon=True
    )
    runner_thread.start()

    deadline = time.monotonic() + args.phase_a_seconds
    # Inspect the LIVE snapshot only — fetch_historical would silently serve
    # REST-backfill rows and mask the stream's own progress.
    while time.monotonic() < deadline:
        if len(collector._snapshot.get(SYMBOL, [])) >= 1:  # pyright: ignore[reportPrivateUsage]
            break
        time.sleep(2.0)
    pre_candles = len(collector._snapshot.get(SYMBOL, []))  # pyright: ignore[reportPrivateUsage]
    lines.append(f"phase A: {pre_candles} closed candle(s) before first outage")
    if pre_candles == 0:
        lines += ["NO-GO: no candle closed during phase A — feed unreachable?", "VERDICT: NO-GO"]
        out = (
            REPO_ROOT
            / "docs"
            / "evidence"
            / (f"{datetime.now(UTC).date().isoformat()}_ws_resync_drill.log")
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return 2

    for i in range(args.outages):
        time.sleep(7.0)
        lines.append(f"forced outage {i + 1}/{args.outages}: closing underlying websocket")
        transport.close()  # recv() dies -> run loop treats as outage -> backoff -> reconnect
    deadline = time.monotonic() + args.settle_seconds
    while time.monotonic() < deadline and service.resync_count < 1:
        time.sleep(2.0)

    served = list(collector._snapshot.get(SYMBOL, []))  # pyright: ignore[reportPrivateUsage]
    truth = _closed_klines(limit=max(60, len(served) * 2))

    def evaluate() -> tuple[bool, list[str]]:
        """Convergence evaluation: gapless closed series + kline matches."""
        rows = list(collector._snapshot.get(SYMBOL, []))  # pyright: ignore[reportPrivateUsage]
        stamps = sorted(int(c.timestamp.timestamp()) for c in rows)
        report: list[str] = []
        missing: list[str] = []
        if stamps:
            end = int(datetime.now(tz=UTC).timestamp()) // INTERVAL_S * INTERVAL_S - INTERVAL_S
            expected = set(range(stamps[0], end + 1, INTERVAL_S))
            missing = [str(t) for t in sorted(expected - set(stamps))]
        mismatches: list[str] = []
        tol = collector._reconcile_tolerance_bps  # pyright: ignore[reportPrivateUsage]
        for ts_key in stamps:
            cached = next(c for c in rows if int(c.timestamp.timestamp()) == ts_key)
            kline = truth.get(ts_key)
            if kline is None:
                mismatches.append(f"{ts_key}: kline absent from REST window")
                continue
            for field in ("open", "high", "low", "close", "volume"):
                a, b = getattr(cached, field), getattr(kline, field)
                bps = float("inf") if b == 0 else float(abs((a - b) / b) * Decimal(10000))
                if bps > tol:
                    mismatches.append(f"{ts_key}.{field}: {a} vs {b} ({bps:.2f} bps)")
        ok_resync = service.resync_count >= 1
        ok_failures = collector.reconcile_failures == 0
        ok_gapless = bool(stamps) and not missing
        ok_match = bool(stamps) and not mismatches
        verdict_ = all([ok_resync, ok_failures, ok_gapless, ok_match])
        report += [
            (
                f"convergence: cached_closed_candles={len(stamps)} "
                f"rest_klines_in_window={len(truth)}"
            ),
            f"missing_minutes={len(missing)}" + (f" e.g. {missing[:3]}" if missing else ""),
            f"field_mismatches={len(mismatches)}"
            + (f" e.g. {mismatches[:5]}" if mismatches else ""),
            (
                f"checks: resync_fired={ok_resync} reconcile_clean={ok_failures} "
                f"gapless={ok_gapless} matches_klines={ok_match}"
            ),
        ]
        return verdict_, report

    # Poll for convergence: the mop-up pass can only fire once the damaged
    # candle's official kline has matured at the exchange, so allow up to
    # settle_seconds for that to happen instead of checking once blindly.
    verdict = False
    report: list[str] = []
    while time.monotonic() < deadline:
        verdict, report = evaluate()
        if verdict:
            break
        time.sleep(5.0)

    meters = {
        "resyncs": service.resync_count,
        "gaps_filled": collector.reconcile_gaps_filled,
        "divergences": collector.reconcile_divergences,
        "failures": collector.reconcile_failures,
    }
    lines.append("meters: " + ", ".join(f"{k}={v}" for k, v in meters.items()))
    lines += report
    lines += [
        f"finished {datetime.now(UTC).isoformat()}",
        f"VERDICT: {'PASS' if verdict else 'FAIL'}",
    ]

    out = (
        REPO_ROOT
        / "docs"
        / "evidence"
        / (f"{datetime.now(UTC).date().isoformat()}_ws_resync_drill.log")
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
