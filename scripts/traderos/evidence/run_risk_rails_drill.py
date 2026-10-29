#!/usr/bin/env python3
"""G-03 evidence: portfolio risk rails provably stop the live loop.

Drills each fail-closed rail against the REAL submission path — a real
``CycleExecutor`` driven with a real ``RiskService`` and a real
``BrokerAdapter``: the broker is never invoked when a rail refuses, and a
kill-switch flatten issues exactly the close orders through that same broker.

Proves, with one drill run:
  1. portfolio gross-exposure cap blocks submission (broker untouched)
  2. allowlist blocks an unlisted symbol; allowlisted symbols reach the broker
  3. kill-switch engage -> flatten closes positions exactly-once + blocks new buys
  4. data-gap (stale feed) blocks trading in LIVE mode
  5. control: an in-limit order reaches the broker

Run:  PYTHONPATH=. python3 scripts/evidence/run_risk_rails_drill.py
"""

from __future__ import annotations

import sqlite3
import sys
import uuid
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from traderos.application.cycle_executor import CycleExecutor  # noqa: E402
from traderos.application.models import TradingMode  # noqa: E402
from traderos.domain.adapters.broker_adapter import BrokerAdapter  # noqa: E402
from traderos.domain.adapters.broker_adapter import FillResult  # noqa: E402
from traderos.domain.entities import Position  # noqa: E402
from traderos.domain.entities import Signal  # noqa: E402
from traderos.domain.entities import SignalDirection  # noqa: E402
from traderos.domain.services.analysis_service import AnalysisService  # noqa: E402
from traderos.domain.services.backtesting_service import synthetic_candles  # noqa: E402
from traderos.domain.services.flatten_service import FlattenService  # noqa: E402
from traderos.domain.services.portfolio_service import PortfolioService  # noqa: E402
from traderos.domain.services.risk_service import KillSwitch  # noqa: E402
from traderos.domain.services.risk_service import RiskService  # noqa: E402
from traderos.domain.services.signal_service import SignalProvenance  # noqa: E402
from traderos.domain.services.strategy_framework import SignalResult  # noqa: E402
from traderos.domain.services.strategy_framework import StrategyBase  # noqa: E402
from traderos.domain.services.strategy_framework import registry as strategy_registry  # noqa: E402
from traderos.infrastructure.events import InMemoryEventBus  # noqa: E402
from traderos.infrastructure.observability import SQLiteAuditService  # noqa: E402
from traderos.infrastructure.observability import SQLiteHealthService  # noqa: E402
from traderos.infrastructure.observability import SQLiteManifestService  # noqa: E402
from traderos.infrastructure.observability import SQLiteMetricsService  # noqa: E402
from traderos.infrastructure.repositories.sqlite import SQLitePositionRepository  # noqa: E402
from traderos.infrastructure.repositories.sqlite import SQLiteTradeRepository  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-04_sprint27_risk_rails_drill.log"


class _SpyBroker(BrokerAdapter):
    def __init__(self) -> None:
        self.orders: list[tuple] = []

    def place_market_order(self, market_id, side, quantity, close_price=None, client_order_id=None):
        self.orders.append((str(market_id), side, quantity, close_price))
        return FillResult(
            True,
            quantity,
            close_price or Decimal("100.0"),
            Decimal("0.0"),
            "filled",
            f"ord-{len(self.orders)}",
        )

    def place_limit_order(self, market_id, side, quantity, price, close_price=None):
        return FillResult(False, Decimal("0.0"), Decimal("0.0"), quantity, "pending", "")

    def cancel_order(self, order_id):
        return FillResult(
            True, Decimal("0.0"), Decimal("0.0"), Decimal("0.0"), "cancelled", order_id
        )

    def place_stop_order(self, market_id, side, quantity, stop_price, market_price=None):
        return FillResult(False, Decimal("0.0"), Decimal("0.0"), quantity, "pending", "")

    def place_trailing_stop_order(
        self, market_id, side, quantity, trail_percent, market_price=None
    ):
        return FillResult(False, Decimal("0.0"), Decimal("0.0"), quantity, "pending", "")

    def modify_order(
        self, order_id, qty=None, limit_price=None, stop_price=None, trail_percent=None
    ):
        return FillResult(
            True, Decimal("0.0"), Decimal("0.0"), Decimal("0.0"), "modified", order_id
        )

    def get_account_balance(self):
        return 10000.0

    def get_positions(self):
        return []

    def get_open_orders(self):
        return []


class _AlwaysSignal(StrategyBase):
    name = "risk_rails_drill_signal"

    def evaluate(self, state):
        return SignalResult("long", 0.8, {"drill": True})


def _make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from traderos.infrastructure.database.migration_manager import migrate

    migrate(conn)
    return conn


def _signal_service(mid: uuid.UUID):
    now = datetime.now(UTC)
    signal = Signal(
        market_id=mid,
        strategy_id=uuid.uuid4(),
        direction=SignalDirection.LONG,
        confidence=0.8,
        generated_at=now,
        expires_at=now + timedelta(hours=1),
    )
    provenance = SignalProvenance(signal=signal, strategy_name="x", indicators_used={})
    service = Mock()
    service.process_evaluation.return_value = provenance
    return service


def _executor(
    conn,
    broker,
    risk_service,
    portfolio_service,
    mid,
    mode=TradingMode.PAPER,
    data_ingestion=None,
    flatten_service=None,
):
    return CycleExecutor(
        mode=mode,
        signal_service=_signal_service(mid),
        risk_service=risk_service,
        portfolio_service=portfolio_service,
        execution=Mock(),
        analysis=AnalysisService(),
        broker=broker,
        event_bus=InMemoryEventBus(),
        health=SQLiteHealthService(conn),
        audit=SQLiteAuditService(conn),
        metrics=SQLiteMetricsService(conn),
        notifications=Mock(),
        run_manifest=SQLiteManifestService(conn),
        data_ingestion=data_ingestion,
        enabled_strategies=lambda: [("risk_rails_drill_signal", "risk_rails_drill_signal", {})],
        flatten_service=flatten_service,
        # This drill proves the portfolio risk rails, so sizing must be given
        # a sourced win rate to reach them. Without one, sizing refuses first
        # and every rail would report "broker untouched" for the wrong reason.
        win_rate_provider=lambda: 0.55,
    )


def main() -> int:
    lines: list[str] = []
    lines.append("RISK-RAILS DRILL — G-03 portfolio-level fail-closed proof")
    lines.append(f"started {datetime.now(UTC).isoformat()}")

    strategy_registry.register(_AlwaysSignal)
    results: list[tuple[str, bool, str]] = []

    def run_case(name: str, fn) -> None:
        ok, detail = fn()
        results.append((name, ok, detail))
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    try:
        # 1. Gross exposure cap
        def case_gross():
            conn = _make_conn()
            try:
                trade_repo = SQLiteTradeRepository(conn)
                pos_repo = SQLitePositionRepository(conn)
                pf = PortfolioService(trade_repo=trade_repo, position_repo=pos_repo)
                mid = uuid.uuid4()
                pos_repo.add(
                    Position(
                        market_id=mid,
                        quantity=Decimal("100.0"),
                        entry_price=Decimal("100.0"),
                        current_price=Decimal("100.0"),
                        pnl=Decimal("0.0"),
                    )
                )
                risk = RiskService(max_gross_exposure=0.504)
                broker = _SpyBroker()
                r = _executor(conn, broker, risk, pf, mid).run(mid, close_price=Decimal("100.0"))
                blocked = (
                    broker.orders == []
                    and r.trades == 0
                    and any("gross exposure" in e for e in r.errors)
                )
                return (
                    blocked,
                    (
                        "cap 0.504x equity blocks 16 qty @ 100 with existing "
                        "10000 exposure (broker untouched)"
                    ),
                )
            finally:
                conn.close()

        # 2a. Allowlist blocks unlisted
        def case_allowlist_block():
            conn = _make_conn()
            try:
                trade_repo = SQLiteTradeRepository(conn)
                pos_repo = SQLitePositionRepository(conn)
                pf = PortfolioService(trade_repo=trade_repo, position_repo=pos_repo)
                listed = uuid.uuid4()
                risk = RiskService(allowed_markets=frozenset({listed}))
                broker = _SpyBroker()
                r = _executor(conn, broker, risk, pf, uuid.uuid4()).run(
                    uuid.uuid4(), close_price=Decimal("100.0")
                )
                blocked = (
                    broker.orders == []
                    and r.trades == 0
                    and any("allowlist" in e for e in r.errors)
                )
                return blocked, "unlisted symbol refused; broker untouched"
            finally:
                conn.close()

        # 2b. Allowlisted reaches broker
        def case_allowlist_pass():
            conn = _make_conn()
            try:
                trade_repo = SQLiteTradeRepository(conn)
                pos_repo = SQLitePositionRepository(conn)
                pf = PortfolioService(trade_repo=trade_repo, position_repo=pos_repo)
                mid = uuid.uuid4()
                risk = RiskService(allowed_markets=frozenset({mid}))
                broker = _SpyBroker()
                r = _executor(conn, broker, risk, pf, mid).run(mid, close_price=Decimal("100.0"))
                return bool(broker.orders) and r.trades == 1, "allowlisted symbol reaches broker"
            finally:
                conn.close()

        # 3. Kill-switch flatten
        def case_kill_flatten():
            conn = _make_conn()
            try:
                trade_repo = SQLiteTradeRepository(conn)
                pos_repo = SQLitePositionRepository(conn)
                pf = PortfolioService(trade_repo=trade_repo, position_repo=pos_repo)
                mid = uuid.uuid4()
                pos_repo.add(
                    Position(
                        market_id=mid,
                        quantity=Decimal("5.0"),
                        entry_price=Decimal("100.0"),
                        current_price=Decimal("100.0"),
                        pnl=Decimal("0.0"),
                    )
                )
                risk = RiskService(kill_switch=KillSwitch())
                risk.kill_switch.engage()
                broker = _SpyBroker()
                flatten = FlattenService(
                    broker=broker,
                    portfolio_service=pf,
                    notifications=Mock(),
                    audit=SQLiteAuditService(conn),
                    metrics=SQLiteMetricsService(conn),
                )
                ex = _executor(conn, broker, risk, pf, mid, flatten_service=flatten)
                ex.run(mid, close_price=Decimal("100.0"))
                ex.run(mid, close_price=Decimal("100.0"))  # second cycle must not re-flatten
                sells = [o for o in broker.orders if o[1] == "sell"]
                buys = [o for o in broker.orders if o[1] == "buy"]
                exactly_once = len(sells) == 1 and sells[0][2] == Decimal("5.0") and buys == []
                return (
                    exactly_once,
                    "kill switch -> 1 sell close (5 qty), 0 buys, exactly-once across cycles",
                )
            finally:
                conn.close()

        # 4. Data-gap LIVE
        def case_data_gap():
            conn = _make_conn()
            try:
                trade_repo = SQLiteTradeRepository(conn)
                pos_repo = SQLitePositionRepository(conn)
                pf = PortfolioService(trade_repo=trade_repo, position_repo=pos_repo)
                risk = RiskService(max_data_staleness_seconds=60.0)

                class _StaleFeed:
                    def __init__(self):
                        self._candles = synthetic_candles(count=10)  # timestamps 2024-01-01

                    def fetch_candles(self, market_id, limit=100):
                        return self._candles

                broker = _SpyBroker()
                r = _executor(
                    conn,
                    broker,
                    risk,
                    pf,
                    uuid.uuid4(),
                    mode=TradingMode.LIVE,
                    data_ingestion=_StaleFeed(),
                ).run(uuid.uuid4(), close_price=Decimal("100.0"))
                blocked = (
                    broker.orders == []
                    and r.trades == 0
                    and any("trading blocked" in e or "stale" in e for e in r.errors)
                )
                return blocked, "stale feed (2024 candles) blocks live trading; broker untouched"
            finally:
                conn.close()

        # 5. Control
        def case_control():
            conn = _make_conn()
            try:
                trade_repo = SQLiteTradeRepository(conn)
                pos_repo = SQLitePositionRepository(conn)
                pf = PortfolioService(trade_repo=trade_repo, position_repo=pos_repo)
                risk = RiskService()
                broker = _SpyBroker()
                r = _executor(conn, broker, risk, pf, uuid.uuid4()).run(
                    uuid.uuid4(), close_price=Decimal("100.0")
                )
                return bool(broker.orders) and r.trades == 1, "in-limit order reaches broker"
            finally:
                conn.close()

        for name, fn in [
            ("gross_exposure_cap_blocks", case_gross),
            ("allowlist_blocks_unlisted", case_allowlist_block),
            ("allowlist_reaches_broker", case_allowlist_pass),
            ("kill_switch_flatten_exactly_once", case_kill_flatten),
            ("data_gap_blocks_live", case_data_gap),
            ("control_reaches_broker", case_control),
        ]:
            run_case(name, fn)
    finally:
        strategy_registry.unregister("risk_rails_drill_signal")

    passed = sum(1 for _, ok, _ in results if ok)
    verdict = "PASS" if passed == len(results) else "FAIL"
    lines.append("")
    lines.append(f"VERDICT: {verdict} — {passed}/{len(results)} rails proven fail-closed")
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
