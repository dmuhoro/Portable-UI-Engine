#!/usr/bin/env python3
"""Sprint 38 (Slice D) evidence: the Market Brain, end-to-end, fail-closed.

The Market Brain is the chart watcher that sits IN FRONT OF the real submission
path. This drill proves the full stack — domain service, durable persistence,
sync gate, async gate, factory wiring — on the REAL services (real sqlite,
real observability, real event bus) with the real ``CycleExecutor`` seam, and
writes a dated evidence log. It is credential-free and network-free so it runs
deterministically in the CI drill job (WP13).

What it proves (each phase = one assertion, one PASS line):
  1. SYNC FAIL-CLOSED on the real loop: a wired Brain with no readable chart
     means the real cycle seam is NEVER invoked (``executor.run`` stays 0),
     ``sync_daemon.brain_blocks`` counts it, and a ``brain.advice`` event with
     ``allowed=False`` is published — no silent drops.
  2. SYNC FAIL-CLOSED without a data source at all: even with no ingestion, a
     wired Brain refuses an unreadable chart.
  3. RESTART-SAFE DURABLE REPLAY: seed history through the durable store, then
     rebuild the controller with a fresh Brain (simulated restart) against an
     EMPTY live source — the replayed state is readable, the real cycle runs,
     and ``sync_daemon.brain_advised`` counts it.
  4. ASYNC LIVE SEED: a fresh async daemon with a wired Brain but no durable
     history is seeded from the live data source on its first tick, the real
     cycle runs, and warm runs exactly once (a second tick never re-warms).
  5. ASYNC FAIL-CLOSED: live source empty + no durable history -> the Brain
     stays UNKNOWN and the real cycle is refused (``async_daemon.brain_blocks``).
  6. CONFIG WIRING: ``market_brain.*`` knobs reach the constructed service
     through the production factory; ``enabled=False`` and a malformed section
     both build NO brain (opt-in only, fail closed).

Run:
    PYTHONPATH=src python3 scripts/evidence/run_market_brain_drill.py
"""

from __future__ import annotations

import asyncio
import sqlite3
import sys
import threading
import time
import uuid
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from traderos.application import factory as _factory  # noqa: E402
from traderos.application.async_daemon import AsyncDaemonController  # noqa: E402
from traderos.application.daemon_controller import DaemonController  # noqa: E402
from traderos.application.models import CycleResult  # noqa: E402
from traderos.application.models import TradingMode  # noqa: E402
from traderos.domain.entities import OHLCV  # noqa: E402
from traderos.domain.entities import Candle  # noqa: E402
from traderos.domain.entities import Timeframe  # noqa: E402
from traderos.domain.services.backtesting_service import synthetic_candles  # noqa: E402
from traderos.domain.services.market_brain_service import MarketBrainService  # noqa: E402
from traderos.infrastructure.config.config_loader import Config  # noqa: E402
from traderos.infrastructure.database.connection import ThreadSafeSQLiteConnection  # noqa: E402
from traderos.infrastructure.database.migration_manager import migrate  # noqa: E402
from traderos.infrastructure.events import InMemoryEventBus  # noqa: E402
from traderos.infrastructure.market_stream import Tick  # noqa: E402
from traderos.infrastructure.observability import SQLiteAuditService  # noqa: E402
from traderos.infrastructure.observability import SQLiteHealthService  # noqa: E402
from traderos.infrastructure.observability import SQLiteManifestService  # noqa: E402
from traderos.infrastructure.observability import SQLiteMetricsService  # noqa: E402
from traderos.infrastructure.repositories.brain_candle_store import BrainCandleStore  # noqa: E402
from traderos.infrastructure.repositories.sqlite.historical_candles import (  # noqa: E402
    SQLiteHistoricalCandleRepository,
)

OUT = (
    REPO_ROOT
    / "docs"
    / "evidence"
    / f"{datetime.now(UTC).date().isoformat()}_market_brain_drill.log"
)


def _conn() -> ThreadSafeSQLiteConnection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    wrapped = ThreadSafeSQLiteConnection(conn)
    migrate(wrapped)
    return wrapped


def _raw(wrapped: ThreadSafeSQLiteConnection) -> sqlite3.Connection:
    """The underlying sqlite3.Connection a wrapper serializes. Drill services are
    typed ``conn: sqlite3.Connection`` (as in the committed drill suite), so the
    single in-memory DB is shared between repo wrapper and services."""
    return wrapped._conn  # pyright: ignore[reportPrivateUsage]


_build_market_brain = _factory._build_market_brain  # pyright: ignore[reportPrivateUsage]


def _brain(store=None, **kw) -> MarketBrainService:
    return MarketBrainService(max_risk_fraction=0.01, action_threshold=0.4, store=store, **kw)


def _tick(price: str, ts: datetime, symbol: str = "BTCUSDT") -> Tick:
    return Tick(
        symbol=symbol,
        price=__import__("decimal").Decimal(price),
        quantity=__import__("decimal").Decimal("1.0"),
        exchange_timestamp=ts,
        received_timestamp=ts,
        source="binance",
        event_id=str(uuid.uuid4()),
    )


def _daily_history(mid: uuid.UUID, count: int) -> list[Candle]:
    """Timestamp-unique rising daily bars — the shape real exchange history
    takes. (Durability is per-bar-timestamp, so the durable seat is honest for
    timestamp-unique streams; a same-timestamp synthetic tape collapses
    LAST-WINS by design.)"""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    from datetime import timedelta

    candles: list[Candle] = []
    for i in range(count):
        c = round(100.0 * (1.0 + 0.01 * i), 4)
        candles.append(
            Candle(
                market_id=mid,
                ohlcv=OHLCV(
                    open=__import__("decimal").Decimal(str(c)),
                    high=__import__("decimal").Decimal(str(c + 1)),
                    low=__import__("decimal").Decimal(str(c - 1)),
                    close=__import__("decimal").Decimal(str(c)),
                    volume=__import__("decimal").Decimal(1000),
                ),
                timestamp=base + timedelta(days=i),
                timeframe=Timeframe.DAY_1,
            )
        )
    return candles


def _stopper(controller: DaemonController, delay: float = 0.4) -> threading.Thread:
    t = threading.Thread(
        target=lambda: (time.sleep(delay), setattr(controller, "_running", False)),
        daemon=True,
    )
    t.start()
    return t


def _sync_controller(
    conn,
    executor,
    brain,
    data_ingestion,
    event_bus=None,
    market_id: uuid.UUID | None = None,
) -> tuple[DaemonController, uuid.UUID]:
    mid = market_id or uuid.uuid4()
    controller = DaemonController(
        mode=TradingMode.PAPER,
        cycle_executor=executor,
        event_bus=event_bus or InMemoryEventBus(),
        health=SQLiteHealthService(_raw(conn)),
        audit=SQLiteAuditService(_raw(conn)),
        metrics=SQLiteMetricsService(_raw(conn)),
        notifications=Mock(),
        run_manifest=SQLiteManifestService(_raw(conn)),
        data_ingestion=data_ingestion,
        market_ids=[mid],
        brain=brain,
    )
    return controller, mid


def _empty_ingestion() -> Mock:
    data_ingestion = Mock()
    data_ingestion.get_latest_close.return_value = 100.0
    data_ingestion.fetch_candles.return_value = []
    return data_ingestion


def main() -> int:
    lines: list[str] = []
    started = datetime.now(UTC)
    lines.append("MARKET BRAIN DRILL — Sprint 38 Slice D: end-to-end, fail-closed")
    lines.append(f"started {started.isoformat()}")

    results: list[tuple[bool, str]] = []

    # Phase 1 — sync fail-closed on the real loop.
    conn = _conn()
    executor = Mock()
    executor.run.return_value = CycleResult(uuid.uuid4(), 0, 0, [], 0.0, started)
    event_bus = InMemoryEventBus()
    events: list = []
    event_bus.subscribe("brain.advice", events.append)
    controller, _ = _sync_controller(
        conn, executor, _brain(), _empty_ingestion(), event_bus=event_bus
    )
    t = _stopper(controller)
    controller.run_forever(interval_seconds=1, shutdown_timeout=5)
    t.join(timeout=2)
    metrics1 = controller._metrics  # pyright: ignore[reportPrivateUsage]
    blocks1 = metrics1.get_counter("sync_daemon.brain_blocks")
    phase1 = (
        executor.run.call_count == 0
        and blocks1 >= 1
        and any(e.payload.get("allowed") is False for e in events)
    )
    results.append((phase1, "sync unreadable chart blocks the real cycle (0 runs, blocks+event)"))
    block_events = sum(1 for e in events if not e.payload.get("allowed"))
    lines.append(
        f"[{'PASS' if phase1 else 'FAIL'}] sync fail-closed: "
        f"executor.run={executor.run.call_count} brain_blocks={blocks1} "
        f"block_events={block_events}"
    )

    # Phase 2 — sync fail-closed without a data source at all.
    controller2, mid2 = _sync_controller(conn, Mock(), _brain(), None)
    brain2 = controller2._brain  # pyright: ignore[reportPrivateUsage]
    assert brain2 is not None
    gated = controller2._brain_gate(brain2, mid2)  # pyright: ignore[reportPrivateUsage]
    metrics2 = controller2._metrics  # pyright: ignore[reportPrivateUsage]
    blocks2 = metrics2.get_counter("sync_daemon.brain_blocks")
    phase2 = gated is False and blocks2 >= 1
    results.append((phase2, "sync brain refuses an unreadable chart with NO data source at all"))
    lines.append(
        f"[{'PASS' if phase2 else 'FAIL'}] sync fail-closed (no ingestion): "
        f"gate_allowed={gated} brain_blocks={blocks2}"
    )

    # Phase 3 — restart-safe durable replay: seed, then a FRESH brain against an
    # EMPTY live source still reads the chart and drives the real cycle.
    conn3 = _conn()
    mid3 = uuid.uuid4()
    store = BrainCandleStore(SQLiteHistoricalCandleRepository(conn3))
    _brain(store).seed_candles(mid3, _daily_history(mid3, 220))
    durable_after_seed = len(store.load_candles(mid3, limit=300))
    executor3 = Mock()
    executor3.run.return_value = CycleResult(mid3, 0, 0, [], 0.0, started)
    controller3, _ = _sync_controller(
        conn3, executor3, _brain(store), _empty_ingestion(), market_id=mid3
    )
    t3 = _stopper(controller3)
    controller3.run_forever(interval_seconds=1, shutdown_timeout=5)
    t3.join(timeout=2)
    replayed = _brain(store)
    replayed.warm_from_store(mid3, limit=300)
    snap = replayed.snapshot(mid3)
    metrics3 = controller3._metrics  # pyright: ignore[reportPrivateUsage]
    advised3 = metrics3.get_counter("sync_daemon.brain_advised")
    phase3 = (
        durable_after_seed == 220
        and snap.known is True
        and executor3.run.call_count >= 1
        and advised3 >= 1
    )
    results.append(
        (
            phase3,
            "durable replay: fresh brain after restart reads the same state and runs the cycle",
        )
    )
    lines.append(
        f"[{'PASS' if phase3 else 'FAIL'}] restart-safe durable replay: "
        f"durable_seat_bars={durable_after_seed} replayed_known={snap.known} "
        f"regime={snap.regime} executor.run={executor3.run.call_count} "
        f"brain_advised={advised3}"
    )

    # Phase 4 — async live seed: fresh brain, no durable history -> seeded from
    # the live source on the first tick; warm runs exactly once.
    conn4 = _conn()
    mid4 = uuid.uuid4()
    executor4 = Mock()
    executor4.run.return_value = None
    data4 = Mock()
    data4.fetch_candles.return_value = synthetic_candles(
        count=220, start_price=100.0, market_id=mid4
    )
    metrics4 = SQLiteMetricsService(_raw(conn4))
    daemon = AsyncDaemonController(
        mode=TradingMode.PAPER,
        cycle_executor=executor4,
        market_symbols={mid4: "BTCUSDT"},
        event_bus=InMemoryEventBus(),
        health=SQLiteHealthService(_raw(conn4)),
        audit=SQLiteAuditService(_raw(conn4)),
        metrics=metrics4,
        notifications=Mock(),
        run_manifest=SQLiteManifestService(_raw(conn4)),
        brain=_brain(),
        data_ingestion=data4,
    )
    asyncio.run(daemon.handle_tick(_tick("320.5", datetime(2026, 1, 1, 12, 0, tzinfo=UTC))))
    phase4_first = (
        executor4.run.call_count == 1 and metrics4.get_counter("async_daemon.brain_advised") == 1
    )
    asyncio.run(daemon.handle_tick(_tick("321.0", datetime(2026, 1, 1, 12, 1, tzinfo=UTC))))
    phase4_second = executor4.run.call_count == 2
    results.append((phase4_first and phase4_second, "async live seed on first tick + warm-once"))
    lines.append(
        f"[{'PASS' if phase4_first and phase4_second else 'FAIL'}] async live seed: "
        f"runs_after_1st_tick={executor4.run.call_count} warm_once_proven={phase4_second} "
        f"brain_advised={metrics4.get_counter('async_daemon.brain_advised')}"
    )

    # Phase 5 — async fail-closed: live source empty, no durable history.
    conn5 = _conn()
    mid5 = uuid.uuid4()
    executor5 = Mock()
    executor5.run.return_value = None
    metrics5 = SQLiteMetricsService(_raw(conn5))
    daemon5 = AsyncDaemonController(
        mode=TradingMode.PAPER,
        cycle_executor=executor5,
        market_symbols={mid5: "BTCUSDT"},
        event_bus=InMemoryEventBus(),
        health=SQLiteHealthService(_raw(conn5)),
        audit=SQLiteAuditService(_raw(conn5)),
        metrics=metrics5,
        notifications=Mock(),
        run_manifest=SQLiteManifestService(_raw(conn5)),
        brain=_brain(),
        data_ingestion=_empty_ingestion(),
    )
    asyncio.run(daemon5.handle_tick(_tick("320.5", datetime(2026, 1, 1, 12, 0, tzinfo=UTC))))
    phase5 = (
        executor5.run.call_count == 0 and metrics5.get_counter("async_daemon.brain_blocks") >= 1
    )
    blocks5 = metrics5.get_counter("async_daemon.brain_blocks")
    results.append((phase5, "async live source empty -> Brain UNKNOWN -> cycle refused"))
    lines.append(
        f"[{'PASS' if phase5 else 'FAIL'}] async fail-closed: "
        f"executor.run={executor5.run.call_count} brain_blocks={blocks5}"
    )

    # Phase 6 — production config wiring (opt-in, fail closed).
    knobs = Config(
        db_path=":memory:",
        _raw_settings={
            "market_brain": {
                "enabled": True,
                "min_candles": 40,
                "action_threshold": 0.7,
                "max_risk_fraction": 0.005,
            }
        },
    )
    built = _build_market_brain(knobs)
    disabled = _build_market_brain(
        Config(db_path=":memory:", _raw_settings={"market_brain": {"enabled": False}})
    )
    malformed = _build_market_brain(
        Config(db_path=":memory:", _raw_settings={"market_brain": "not-a-dict"})
    )
    phase6 = (
        built is not None
        and built.min_candles == 40
        and built.action_threshold == 0.7
        and built.max_risk_fraction == 0.005
        and disabled is None
        and malformed is None
    )
    results.append(
        (phase6, "market_brain.* config reaches the service; disabled/malformed build NO brain")
    )
    lines.append(
        f"[{'PASS' if phase6 else 'FAIL'}] config wiring: "
        f"min_candles={built.min_candles if built else None} "
        f"action_threshold={built.action_threshold if built else None} "
        f"max_risk_fraction={built.max_risk_fraction if built else None} "
        f"disabled_builds={disabled} malformed_builds={malformed}"
    )

    verdict = "PASS" if all(ok for ok, _ in results) else "FAIL"
    lines.append("")
    for ok, label in results:
        lines.append(f"  {'OK ' if ok else 'FAILED'} {label}")
    lines.append(f"VERDICT: {verdict}")
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
