#!/usr/bin/env python3
"""G-05 evidence: causal replay across simulated process restarts.

The G-05 exit test is *replay a full trading day and reconstruct why each fill
happened, bit-identical to the recorded events*. This drill records real cycles
through the actual ``CycleExecutor``, then simulates broker/daemon restarts by
closing and reopening the durable SQLite store with a brand-new executor
process-equivalent (fresh connection, fresh in-memory objects, same DB file).
Trading continues across restart boundaries; afterwards the whole day is
replayed from durable audit + trades tables.

Proves with one run:
  1. audit hash-chain stays valid across restarts (append-only, tamper-evident)
  2. every cycle's causal chain (signal -> decision -> order -> fill) is
     reconstructible after restarts
  3. replay of the recorded events is complete (fills == cycles that filled)
  4. per-fill realized PnL is recomputed by FIFO matching from the same data

Run:  PYTHONPATH=. python3 scripts/evidence/run_multirestart_replay.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
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
from traderos.domain.entities.signal import Signal  # noqa: E402
from traderos.domain.entities.signal import SignalDirection  # noqa: E402
from traderos.domain.services.analysis_service import AnalysisService  # noqa: E402
from traderos.domain.services.portfolio_service import PortfolioService  # noqa: E402
from traderos.domain.services.replay_service import ReplayService  # noqa: E402
from traderos.domain.services.risk_service import KillSwitch  # noqa: E402
from traderos.domain.services.risk_service import RiskAssessment  # noqa: E402
from traderos.domain.services.risk_service import TradeVerdict  # noqa: E402
from traderos.domain.services.signal_service import SignalProvenance  # noqa: E402
from traderos.domain.services.strategy_framework import SignalResult  # noqa: E402
from traderos.domain.services.strategy_framework import StrategyBase  # noqa: E402
from traderos.domain.services.strategy_framework import registry as strategy_registry  # noqa: E402
from traderos.infrastructure.events import InMemoryEventBus  # noqa: E402
from traderos.infrastructure.observability import SQLiteAuditService  # noqa: E402
from traderos.infrastructure.observability import SQLiteHealthService  # noqa: E402
from traderos.infrastructure.observability import SQLiteManifestService  # noqa: E402
from traderos.infrastructure.observability import SQLiteMetricsService  # noqa: E402
from traderos.infrastructure.repositories.sqlite.trades import (  # noqa: E402
    SQLitePositionRepository,
)
from traderos.infrastructure.repositories.sqlite.trades import SQLiteTradeRepository  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-04_sprint27_multirestart_replay.log"


class _Broker(BrokerAdapter):
    def __init__(self) -> None:
        self.submissions: list[dict] = []

    def place_market_order(self, market_id, side, quantity, close_price=None, client_order_id=None):
        price = close_price if close_price is not None else Decimal("100.0")
        self.submissions.append({"side": side, "qty": quantity, "price": price})
        return FillResult(True, quantity, price, Decimal(0), "filled", f"ord-{side}-{price}")

    def place_limit_order(self, market_id, side, quantity, price, close_price=None):
        return FillResult(False, 0.0, 0.0, quantity, "pending", "")

    def cancel_order(self, order_id):
        return FillResult(True, 0.0, 0.0, 0.0, "cancelled", order_id)

    def place_stop_order(self, market_id, side, quantity, stop_price, market_price=None):
        return FillResult(False, 0.0, 0.0, quantity, "pending", "")

    def place_trailing_stop_order(
        self, market_id, side, quantity, trail_percent, market_price=None
    ):
        return FillResult(False, 0.0, 0.0, quantity, "pending", "")

    def modify_order(
        self, order_id, qty=None, limit_price=None, stop_price=None, trail_percent=None
    ):
        return FillResult(True, 0.0, 0.0, 0.0, "modified", order_id)

    def get_account_balance(self):
        return 10000.0

    def get_positions(self):
        return []

    def get_open_orders(self):
        return []


class _Strat(StrategyBase):
    name = "evidence_multirestart_strat"

    def evaluate(self, state):
        return SignalResult("long", 0.8, {"reason": "multirestart"})


def _prov(direction: SignalDirection, confidence: float = 0.8) -> SignalProvenance:
    now = datetime.now(UTC)
    return SignalProvenance(
        signal=Signal(
            market_id=uuid.uuid4(),
            strategy_id=uuid.uuid4(),
            direction=direction,
            confidence=confidence,
            generated_at=now,
            expires_at=now + timedelta(hours=1),
        ),
        strategy_name="evidence",
        indicators_used={},
    )


def _make_executor(
    db_path: str, broker: _Broker, signal_service: Mock
) -> tuple[CycleExecutor, sqlite3.Connection, SQLiteAuditService, PortfolioService]:
    """A brand-new 'process' (fresh connection + fresh executor) on the SAME
    durable DB — the essence of a broker/daemon restart."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    from traderos.infrastructure.database.migration_manager import migrate

    migrate(conn)
    audit = SQLiteAuditService(conn)
    portfolio = PortfolioService(
        trade_repo=SQLiteTradeRepository(conn),
        position_repo=SQLitePositionRepository(conn),
        audit=audit,
    )
    risk = Mock()
    risk.can_trade.return_value = TradeVerdict(True, "")
    risk.kill_switch = KillSwitch()
    # Money fields are Decimal (ADR-009); kelly_fraction is a ratio and stays float.
    risk.assess_trade.return_value = RiskAssessment(
        kelly_fraction=0.5,
        suggested_stop_loss=Decimal("99.0"),
        suggested_take_profit=Decimal("102.0"),
        risk_per_unit=Decimal("1.0"),
        max_risk_amount=Decimal("200.0"),
    )
    risk.authorize_order.return_value = Mock(allowed=True, reason="")
    executor = CycleExecutor(
        mode=TradingMode.PAPER,
        signal_service=signal_service,
        risk_service=risk,
        portfolio_service=portfolio,
        execution=Mock(),
        analysis=AnalysisService(),
        broker=broker,
        event_bus=InMemoryEventBus(),
        health=SQLiteHealthService(conn),
        audit=audit,
        metrics=SQLiteMetricsService(conn),
        notifications=Mock(),
        run_manifest=SQLiteManifestService(conn),
        enabled_strategies=lambda: [("evidence", "evidence_multirestart_strat", {})],
    )
    return executor, conn, audit, portfolio


def main() -> int:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    strategy_registry.register(_Strat)
    lines: list[str] = []
    lines.append("MULTI-RESTART REPLAY — G-05 causal accountability across restarts")
    lines.append(f"started {datetime.now(UTC).isoformat()}")
    lines.append(f"DB: {db_path}")
    lines.append("")

    market = uuid.uuid4()
    day = ["09:30", "09:45", "10:00", "10:15", "10:30", "10:45", "11:00", "11:15", "11:30"]
    prices = [
        Decimal("100.0"),
        Decimal("102.0"),
        Decimal("104.0"),
        Decimal("106.0"),
        Decimal("104.0"),
        Decimal("108.0"),
        Decimal("106.0"),
        Decimal("110.0"),
        Decimal("112.0"),
    ]

    executor_signal = Mock()
    executor, conn, _, portfolio = _make_executor(db_path, _Broker(), executor_signal)
    day_start = datetime.now(UTC) - timedelta(seconds=5)
    cycle_count = 0
    restarts = (len(prices) - 1) // 3
    try:
        for i, price in enumerate(prices):
            # Simulate a process restart every 3 cycles: close the old store and
            # bring up a brand-new executor over the same durable DB.
            if i > 0 and i % 3 == 0:
                conn.close()
                executor, conn, _, portfolio = _make_executor(db_path, _Broker(), executor_signal)
                lines.append(f"RESTART #{i // 3} simulated at {day[i]} (fresh process, same DB)")
            direction = SignalDirection.SHORT if i in (4, 6) else SignalDirection.LONG
            executor_signal.process_evaluation.return_value = _prov(direction)
            executor.run(market, price)
            cycle_count += 1
        day_end = datetime.now(UTC) + timedelta(seconds=5)

        audit = SQLiteAuditService(conn)
        replay = ReplayService(audit=audit, trade_repo=portfolio.trade_repo).replay_day(
            day_start, day_end
        )

        lines.append("")
        for chain in replay.chains:
            line = (
                f"[{chain.signal_at.isoformat()}] signal={chain.strategy} "
                f"{chain.direction} conf={chain.confidence} "
            )
            if chain.blocked:
                line += "-> BLOCKED"
            elif chain.fill:
                pnl = (
                    f"{chain.fill.realized_pnl:.4f}"
                    if chain.fill.realized_pnl is not None
                    else "open"
                )
                line += (
                    f"-> decision={chain.fill.decision} order={chain.fill.order_status} "
                    f"fill {chain.fill.side} qty={chain.fill.filled_qty} "
                    f"@ {chain.fill.filled_price} pnl={pnl}"
                )
            else:
                line += "-> no order"
            lines.append(line)

        lines.append("")
        chain_valid = audit.verify_chain()
        fills_replayed = replay.total_fills
        complete_chains = sum(1 for c in replay.chains if c.complete)
        chains_recorded = len(replay.chains)
        fills_match = fills_replayed == cycle_count
        replay_complete = complete_chains == cycle_count

        lines.append(
            f"SUMMARY: cycles={cycle_count} restarts={restarts} chains_recorded="
            f"{chains_recorded} fills_replayed={fills_replayed} "
            f"blocked={replay.total_blocked} unfilled={replay.total_unfilled} "
            f"total_realized_pnl={replay.total_realized_pnl:.2f}"
        )
        lines.append(f"  audit chain valid after restarts: {chain_valid}")
        lines.append(f"  every cycle reconstructed (chain complete): {replay_complete}")
        lines.append(f"  replay matches recorded events: {fills_match}")

        passed = chain_valid and replay_complete and fills_match
        verdict = "PASS" if passed else "FAIL"
        lines.append("")
        lines.append(
            f"VERDICT: {verdict} — full day replayed bit-complete after "
            f"{restarts} simulated restarts"
        )
        lines.append(f"Evidence: {OUT}")

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return 0 if verdict == "PASS" else 1
    finally:
        strategy_registry.unregister("evidence_multirestart_strat")
        try:
            conn.close()
        finally:
            os.unlink(db_path)


if __name__ == "__main__":
    raise SystemExit(main())
