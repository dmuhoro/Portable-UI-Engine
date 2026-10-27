#!/usr/bin/env python3
"""A2 evidence: the live Binance WebSocket feed is real, ordered, and produces
candles that feed the daemon's data-gap breaker.

This drill talks to the PUBLIC Binance stream (public market data only — no
account, no order, nothing money-adjacent). It proves four things:

  1. the REAL combined-stream endpoint accepts the transport (no 404 regression)
  2. ticks arrive with strictly increasing (or equal) exchange timestamps — the
     ordering guarantee the aggregator relies on
  3. those ticks aggregate into closed candles served by
     StreamingMarketDataCollector.fetch_historical
  4. the factory gating: streaming stays OFF unless explicitly enabled, and is
     OFF for forex even when enabled (crypto-only seam)

Run:  PYTHONPATH=. python3 scripts/evidence/run_real_binance_stream_drill.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from traderos.application.factory import build_orchestrator  # noqa: E402
from traderos.domain.collectors.base import CollectorType  # noqa: E402
from traderos.infrastructure.collectors.streaming_collector import StreamingFeedRunner  # noqa: E402
from traderos.infrastructure.collectors.streaming_collector import (  # noqa: E402
    StreamingMarketDataCollector,
)
from traderos.infrastructure.config.config_loader import Config  # noqa: E402
from traderos.infrastructure.market_stream import BinanceStreamTransport  # noqa: E402
from traderos.infrastructure.market_stream import StreamingMarketDataService  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-06_real_binance_stream_drill.log"

SYMBOL = "BTCUSDT"
WARMUP_SECONDS = 16
AGGREGATE_INTERVAL_SECONDS = 5


def _sources(orch) -> dict[str, str]:
    """Collector-type per symbol from the orchestrator's ingestion registry."""
    if orch.data_ingestion is None:
        return {}
    return {s.symbol: s.collector_type.value for s in orch.data_ingestion.sources}


def main() -> int:
    lines: list[str] = []
    lines.append("REAL BINANCE STREAM DRILL — A2 live market-data seam")
    results: list[tuple[str, bool]] = []

    stream = StreamingMarketDataService(BinanceStreamTransport())

    # 1. tap the REAL ticks as the collector drains them, recording exchange
    #    times so ordering can be proven independently of candle aggregation
    ordered_ticks: list[datetime] = []
    collector = StreamingMarketDataCollector(
        stream=stream, interval_seconds=AGGREGATE_INTERVAL_SECONDS
    )
    collector.subscribe([SYMBOL])
    collector.attach_observer(lambda tick: ordered_ticks.append(tick.exchange_timestamp))
    runner = StreamingFeedRunner(stream, [SYMBOL])
    runner.start()

    time.sleep(WARMUP_SECONDS)

    # 1. real ticks arrived over the wire, in exchange time order
    ticks = list(ordered_ticks)
    ordered = all(ticks[i] <= ticks[i + 1] for i in range(len(ticks) - 1))
    results.append(("real_ticks_received", len(ticks) > 0))
    results.append(("ticks_exchange_time_ordered", ordered))
    # 2. the collector drained those same ticks and aggregated closed candles
    candles = collector.fetch_historical(SYMBOL, "1m", limit=5)
    results.append(("closed_candles_aggregated", len(candles) > 0))
    if candles:
        latest = candles[-1]
        lines.append(
            f"  latest candle {latest.timestamp.isoformat()} O={latest.open} "
            f"C={latest.close} V={latest.volume}"
        )

    # 3. staleness is finite and small while the feed is live (gap-breaker input)
    results.append(
        (
            "stale_seconds_finite_and_fresh",
            collector.stale_seconds < 5.0 * AGGREGATE_INTERVAL_SECONDS,
        )
    )

    runner.stop()
    lines.append(
        f"  ticks seen by probe: {len(ticks)}, drained by collector: {collector.ticks_seen}"
    )

    # 4. factory gating — the streaming seam never engages unless explicitly
    #    configured, and forex never routes through it even when enabled
    orch = build_orchestrator(
        config=Config(
            db_path=":memory:",
            _raw_settings={
                "data_collection": {
                    "forex_symbols": ["EURUSD"],
                    "crypto_symbols": ["BTCUSDT"],
                    "binance": {"enabled": True, "streaming": False},
                }
            },
        )
    )
    sources = _sources(orch)
    results.append(
        (
            "streaming_off_unless_explicitly_enabled",
            sources["BTCUSDT"] == CollectorType.BINANCE.value,
        )
    )
    results.append(("streaming_feed_absent_when_off", orch.streaming_feed is None))

    orch = build_orchestrator(
        config=Config(
            db_path=":memory:",
            _raw_settings={
                "data_collection": {
                    "forex_symbols": ["EURUSD"],
                    "crypto_symbols": ["BTCUSDT"],
                    "binance": {"enabled": True, "streaming": True},
                }
            },
        )
    )
    sources = _sources(orch)
    results.append(
        (
            "streaming_on_when_explicitly_enabled",
            sources["BTCUSDT"] == CollectorType.STREAMING.value,
        )
    )
    results.append(("forex_never_streams", sources["EURUSD"] == CollectorType.MOCK.value))
    if orch.streaming_feed is not None:
        orch.streaming_feed.stop()

    lines.append("")
    for name, ok in results:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}")
    lines.append("")
    ok_count = sum(1 for _, ok in results if ok)
    verdict = "PASS" if ok_count == len(results) else "FAIL"
    lines.append(f"VERDICT: {verdict} — live feed + gating {ok_count}/{len(results)}")
    lines.append(f"Evidence: {OUT}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
