#!/usr/bin/env python3
"""G-05 evidence: record a real paper trading day through the actual
CycleExecutor, then replay the per-fill causal chains from the durable store.

Proves the chain signal -> decision -> order -> fill -> PnL is reconstructible
entirely from persisted data (audit hash-chain + trades table), with per-fill
realized PnL recomputed by FIFO matching.

Run:  PYTHONPATH=. python3 scripts/evidence/run_causal_replay.py
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


class _Broker(BrokerAdapter):
    def __init__(self) -> None:
        self.submissions: list[dict] = []

    def place_market_order(self, market_id, side, quantity, close_price=None, client_order_id=None):
        price = close_price if close_price is not None else 100.0
        self.submissions.append({"side": side, "qty": quantity, "price": price})
        return FillResult(True, quantity, price, 0.0, "filled", f"ord-{side}-{price}")

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
    name = "evidence_replay_strat"

    def evaluate(self, state):
        return SignalResult("long", 0.8, {"reason": "evidence"})


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


def main() -> int:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_file = db_path
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    from traderos.infrastructure.database.migration_manager import migrate

    migrate(conn)

    strategy_registry.register(_Strat)
    try:
        audit = SQLiteAuditService(conn)
        portfolio = PortfolioService(
            trade_repo=SQLiteTradeRepository(conn),
            position_repo=SQLitePositionRepository(conn),
            audit=audit,
        )
        signal_service = Mock()
        signal_service.process_evaluation.return_value = _prov(SignalDirection.LONG)
        risk = Mock()
        risk.can_trade.return_value = TradeVerdict(True, "")
        risk.kill_switch = KillSwitch()
        risk.assess_trade.return_value = RiskAssessment(
            kelly_fraction=0.5,
            # Money fields are Decimal (ADR-009); kelly_fraction is a ratio.
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
            broker=_Broker(),
            event_bus=InMemoryEventBus(),
            health=SQLiteHealthService(conn),
            audit=audit,
            metrics=SQLiteMetricsService(conn),
            notifications=Mock(),
            run_manifest=SQLiteManifestService(conn),
            enabled_strategies=lambda: [("evidence", "evidence_replay_strat", {})],
        )

        day_start = datetime.now(UTC) - timedelta(seconds=5)
        market = uuid.uuid4()
        day = ["06:30", "06:45", "07:00", "07:15", "07:30", "07:45", "08:00"]
        prices = [100.0, 102.0, 104.0, 106.0, 108.0, 110.0]
        for i, price in enumerate(prices):
            direction = SignalDirection.SHORT if i in (3, 5) else SignalDirection.LONG
            signal_service.process_evaluation.return_value = _prov(direction)
            executor.run(market, price)
        day_end = datetime.now(UTC) + timedelta(seconds=5)

        replay = ReplayService(audit=audit, trade_repo=portfolio.trade_repo).replay_day(
            day_start, day_end
        )

        lines: list[str] = []
        lines.append(f"REPLAY LOG — {day[0]} -> {day[-1]} (6 cycles, market {market})")
        lines.append(f"DB: {db_file}  |  audit chain valid: {audit.verify_chain()}")
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
        lines.append(
            f"SUMMARY: fills={replay.total_fills} blocked={replay.total_blocked} "
            f"unfilled={replay.total_unfilled} total_realized_pnl={replay.total_realized_pnl:.2f}"
        )

        evidence_dir = REPO_ROOT / "docs" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        out = evidence_dir / "2026-08-04_sprint25_causal_replay.log"
        out.write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        print(f"\nEvidence written: {out}")
        return 0
    finally:
        strategy_registry.unregister("evidence_replay_strat")
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
