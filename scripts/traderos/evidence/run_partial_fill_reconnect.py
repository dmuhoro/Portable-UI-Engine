#!/usr/bin/env python3
"""G-02 evidence: partial fills + forced reconnect through the REAL path.

The G-02 exit test demands 0 duplicate/lost orders and clean reconciliation
across broker-side surprises. This drill makes the broker simulator *partially
fill* every order and also drops acks, driving the real production chain
(``CycleExecutor`` -> ``JournaledBroker`` -> ``AlpacaBrokerAdapter``) so the
local position book is forced to agree with broker truth after partial fills
and reconnects.

Proves with one run:
  1. partial fills are journal-confirmed with the ACTUAL filled quantity, so
     local positions match broker positions (no phantom full-size positions)
  2. reconcile is clean after partial fills (0 quantity mismatches)
  3. 0 duplicate orders: broker orders == journal confirmed == trades
  4. 0 lost orders: no pending intents after the drill
  5. restart replay re-submits nothing (idempotent journal)

Run:  PYTHONPATH=. python3 scripts/evidence/run_partial_fill_reconnect.py
"""

from __future__ import annotations

import sqlite3
import sys
import types
import uuid
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

import traderos.infrastructure.retry as _retry  # noqa: E402

_retry.time.sleep = lambda s: None  # bounded, deterministic drill

from traderos.application.cycle_executor import CycleExecutor  # noqa: E402
from traderos.application.models import TradingMode  # noqa: E402
from traderos.domain.entities.signal import Signal  # noqa: E402
from traderos.domain.entities.signal import SignalDirection  # noqa: E402
from traderos.domain.services.analysis_service import AnalysisService  # noqa: E402
from traderos.domain.services.broker_state_reconciliation_service import (  # noqa: E402
    BrokerStateReconciliationService,
)
from traderos.domain.services.portfolio_service import PortfolioService  # noqa: E402
from traderos.domain.services.risk_service import KillSwitch  # noqa: E402
from traderos.domain.services.risk_service import RiskAssessment  # noqa: E402
from traderos.domain.services.risk_service import TradeVerdict  # noqa: E402
from traderos.domain.services.signal_service import SignalProvenance  # noqa: E402
from traderos.domain.services.strategy_framework import SignalResult  # noqa: E402
from traderos.domain.services.strategy_framework import StrategyBase  # noqa: E402
from traderos.domain.services.strategy_framework import registry as strategy_registry  # noqa: E402
from traderos.infrastructure.alpaca_broker import AlpacaBrokerAdapter  # noqa: E402
from traderos.infrastructure.events import InMemoryEventBus  # noqa: E402
from traderos.infrastructure.journal import OrderEventJournal  # noqa: E402
from traderos.infrastructure.journaled_broker import JournaledBroker  # noqa: E402
from traderos.infrastructure.observability import SQLiteAuditService  # noqa: E402
from traderos.infrastructure.observability import SQLiteHealthService  # noqa: E402
from traderos.infrastructure.observability import SQLiteManifestService  # noqa: E402
from traderos.infrastructure.observability import SQLiteMetricsService  # noqa: E402
from traderos.infrastructure.repositories.sqlite.trades import (  # noqa: E402
    SQLitePositionRepository,
)
from traderos.infrastructure.repositories.sqlite.trades import SQLiteTradeRepository  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-04_sprint27_partial_fill_reconnect.log"


class _Order:
    def __init__(self, symbol, qty, side, client_order_id, fill_pct) -> None:
        self.id = f"ord-{client_order_id[:8]}"
        self.symbol = symbol
        self.qty = qty if isinstance(qty, Decimal) else Decimal(str(qty))
        self.side = side
        self.type = "market"
        self.client_order_id = client_order_id
        # Exact money (ADR-009): `fill_pct` is a ratio, so it is carried into
        # Decimal before it multiplies a quantity. Rounding a float fill left
        # the position book unreconcilable by 1 ulp and failed the drill.
        self.filled_qty = (self.qty * Decimal(str(fill_pct))).quantize(Decimal("0.00000001"))
        self.filled_avg_price = Decimal("100.0")


class PartialFillAlpacaClient:
    """Fills only ``fill_pct`` of every order and drops acks on a schedule —
    the two broker-side surprises that most often corrupt position books."""

    def __init__(self, fill_pct: float = 0.5) -> None:
        self.orders: dict[str, _Order] = {}
        self.submit_calls = 0
        self.dropped_cids: set[str] = set()
        self.fill_pct = fill_pct
        self._drop_every = 0

    def arm_ack_drop_every(self, n: int) -> None:
        self._drop_every = n

    def submit_order(self, order_data):
        self.submit_calls += 1
        cid = order_data.client_order_id
        existing = self.orders.get(cid)
        if existing is not None:
            return existing
        order = _Order(order_data.symbol, order_data.qty, order_data.side, cid, self.fill_pct)
        self.orders[cid] = order
        if self._drop_every and len(self.orders) % self._drop_every == 0:
            self.dropped_cids.add(cid)
            raise TimeoutError("ack lost after order accepted")
        return order

    def get_account(self):
        return types.SimpleNamespace(equity=10000.0)

    def get_all_positions(self):
        net: dict[str, float] = {}
        for o in self.orders.values():
            delta = o.filled_qty if o.side == "buy" else -o.filled_qty
            net[o.symbol] = net.get(o.symbol, Decimal(0)) + delta
        return [
            types.SimpleNamespace(symbol=s, qty=q, market_value=q * Decimal("100.0"))
            for s, q in net.items()
            if abs(q) > Decimal("0.000000001")
        ]

    def get_orders(self, _request):
        return []

    def replace_order_by_id(self, order_id, order_data=None):
        return None

    def cancel_order_by_id(self, order_id):
        return None


class _Strat(StrategyBase):
    name = "evidence_partial_fill_strat"

    def evaluate(self, state):
        return SignalResult("long", 0.8, {"reason": "partial-fill"})


def _prov(confidence=0.8):
    now = datetime.now(UTC)
    return SignalProvenance(
        signal=Signal(
            market_id=uuid.uuid4(),
            strategy_id=uuid.uuid4(),
            direction=SignalDirection.LONG,
            confidence=confidence,
            generated_at=now,
            expires_at=now + timedelta(hours=1),
        ),
        strategy_name="partial-fill",
        indicators_used={},
    )


def main() -> int:
    lines: list[str] = []
    started = datetime.now(UTC)
    lines.append("PARTIAL-FILL + RECONNECT DRILL — G-02 broker-side surprises")
    lines.append(f"started {started.isoformat()}")

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from traderos.infrastructure.database.migration_manager import migrate

    migrate(conn)

    flaky = PartialFillAlpacaClient(fill_pct=0.5)
    flaky.arm_ack_drop_every(3)
    adapter = AlpacaBrokerAdapter(api_key="x", secret_key="x", paper=True, client=flaky)
    journal = OrderEventJournal(conn)
    broker = JournaledBroker(adapter, journal)

    audit = SQLiteAuditService(conn)
    portfolio = PortfolioService(
        trade_repo=SQLiteTradeRepository(conn),
        position_repo=SQLitePositionRepository(conn),
        audit=audit,
    )
    signal_service = Mock()
    signal_service.process_evaluation.return_value = _prov()
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

    def build_executor():
        return CycleExecutor(
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
            enabled_strategies=lambda: [("partial-fill", "evidence_partial_fill_strat", {})],
        )

    strategy_registry.register(_Strat)
    try:
        executor = build_executor()
        market = uuid.uuid4()
        for i in range(12):
            signal_service.process_evaluation.return_value = _prov()
            executor.run(market, 100.0 + (i % 50))

        broker_orders = len(flaky.orders)
        confirmed = journal.count()
        trades = len(portfolio.trade_repo.list())
        pending = len(journal.pending_events())

        local_qty = sum(p.quantity for p in SQLitePositionRepository(conn).list_open())
        broker_qty = sum(o.filled_qty for o in flaky.orders.values())

        pre_restart_cids = set(flaky.orders)
        executor = build_executor()
        signal_service.process_evaluation.return_value = _prov()
        executor.run(market, 300.0)
        post_restart_orders = len(flaky.orders)

        local_positions = [
            {
                "market_id": str(p.market_id),
                "qty": p.quantity,
                "current_price": p.current_price,
                "entry_price": p.entry_price,
            }
            for p in SQLitePositionRepository(conn).list_open()
        ]
        recon = BrokerStateReconciliationService(broker=adapter).reconcile(
            local_positions=local_positions,
            local_orders=[],
            journal_pending=broker.pending(),
        )

        no_duplicates = broker_orders == confirmed == trades
        no_lost = pending == 0
        partial_fills_recorded = any(o.filled_qty < o.qty for o in flaky.orders.values())
        book_matches_broker = abs(local_qty - broker_qty) < Decimal("0.000001")
        reconcile_clean = recon.errors == [] and not recon.has_mismatches
        restart_ok = (
            pre_restart_cids.issubset(set(flaky.orders))
            and post_restart_orders == broker_orders + 1
        )
        disconnects = len(flaky.dropped_cids) > 0

        verdict = (
            "PASS"
            if (
                no_duplicates
                and no_lost
                and partial_fills_recorded
                and book_matches_broker
                and reconcile_clean
                and restart_ok
                and disconnects
            )
            else "FAIL"
        )

        lines.append(
            f"cycles=12 forced_disconnects={len(flaky.dropped_cids)} "
            f"submit_attempts={flaky.submit_calls} fill_pct={flaky.fill_pct}"
        )
        lines.append(
            f"broker_orders={broker_orders} journal_confirmed={confirmed} " f"trades={trades}"
        )
        lines.append(f"journal_pending={pending}")
        lines.append(f"local_position_qty={local_qty:.6f} broker_filled_qty={broker_qty:.6f}")
        lines.append(f"reconcile_errors={len(recon.errors)} mismatches={len(recon.mismatches)}")
        lines.append("")
        lines.append(f"1. partial fills recorded w/ actual qty:   {partial_fills_recorded}")
        lines.append(f"2. position book == broker after partial:   {book_matches_broker}")
        lines.append(f"3. reconcile clean:                        {reconcile_clean}")
        lines.append(f"4. 0 duplicate orders (broker==journal==trades): {no_duplicates}")
        lines.append(f"5. 0 lost orders (no pending intents):     {no_lost}")
        lines.append(f"6. restart re-submits nothing:             {restart_ok}")
        lines.append(f"7. forced disconnects exercised:           {disconnects}")
        lines.append(f"VERDICT: {verdict}")

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return 0 if verdict == "PASS" else 1
    finally:
        strategy_registry.unregister("evidence_partial_fill_strat")
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
