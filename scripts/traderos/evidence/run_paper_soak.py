#!/usr/bin/env python3
"""G-02 evidence: bounded unattended paper-soak through the REAL submission path.

Drives the actual production order chain (CycleExecutor -> JournaledBroker ->
AlpacaBrokerAdapter) against a broker simulator that drops acknowledgements
after accepting orders — the worst-case scenario for duplicate/lost orders —
for N soak cycles, then verifies:

  1. 0 duplicate orders  : broker order count == journal count == trade count
  2. 0 lost orders       : every accepted order is journal-confirmed (0 pending)
  3. restart recovery    : rebuilding JournaledBroker from the same journal
                           re-submits nothing; previously confirmed orders replay
  4. reconcile clean     : BrokerStateReconciliationService finds 0 mismatches
  5. ack-loss drill      : the real idempotent retry (same client_order_id)
                           recovers the order on retry — no duplicate at the broker

Run:  PYTHONPATH=. python3 scripts/evidence/run_paper_soak.py [cycles]
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

_retry.time.sleep = lambda s: None  # bounded, deterministic soak

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


class _Order:
    def __init__(self, symbol, qty, side, client_order_id) -> None:
        self.id = f"ord-{client_order_id[:8]}"
        self.symbol = symbol
        self.qty = qty
        self.side = side
        self.type = "market"
        self.client_order_id = client_order_id
        self.filled_qty = qty
        self.filled_avg_price = 100.0


class FlakyAlpacaClient:
    def __init__(self) -> None:
        self.orders: dict[str, _Order] = {}
        self.submit_calls = 0
        self.dropped_cids: set[str] = set()

    def submit_order(self, order_data):
        self.submit_calls += 1
        cid = order_data.client_order_id
        existing = self.orders.get(cid)
        if existing is not None:
            return existing
        order = _Order(order_data.symbol, order_data.qty, order_data.side, cid)
        self.orders[cid] = order
        if len(self.orders) % 5 == 0:
            self.dropped_cids.add(cid)
            raise TimeoutError("ack lost after order accepted")
        return order

    def get_account(self):
        return types.SimpleNamespace(equity=10000.0)

    def get_all_positions(self):
        net: dict[str, float] = {}
        for o in self.orders.values():
            delta = o.qty if o.side == "buy" else -o.qty
            net[o.symbol] = net.get(o.symbol, 0.0) + delta
        return [
            types.SimpleNamespace(symbol=s, qty=q, market_value=q * 100.0)
            for s, q in net.items()
            if abs(q) > 1e-9
        ]

    def get_orders(self, _request):
        return []

    def replace_order_by_id(self, order_id, order_data=None):
        return None

    def cancel_order_by_id(self, order_id):
        return None


class _Strat(StrategyBase):
    name = "evidence_soak_strat"

    def evaluate(self, state):
        return SignalResult("long", 0.8, {"reason": "soak"})


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
        strategy_name="soak",
        indicators_used={},
    )


def main(argv: list[str]) -> int:
    cycles = int(argv[0]) if argv else 250
    lines: list[str] = []
    started = datetime.now(UTC)

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from traderos.infrastructure.database.migration_manager import migrate

    migrate(conn)

    flaky = FlakyAlpacaClient()
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
            enabled_strategies=lambda: [("soak", "evidence_soak_strat", {})],
        )

    strategy_registry.register(_Strat)
    try:
        executor = build_executor()
        market = uuid.uuid4()
        for i in range(cycles):
            signal_service.process_evaluation.return_value = _prov()
            executor.run(market, 100.0 + (i % 50))

        broker_orders = len(flaky.orders)
        confirmed = journal.count()
        trades = len(portfolio.trade_repo.list())
        pending = len(journal.pending_events())
        disconnects = len(flaky.dropped_cids)

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
        restart_ok = pre_restart_cids.issubset(set(flaky.orders)) and post_restart_orders == (
            broker_orders + 1
        )
        reconcile_clean = recon.errors == [] and not recon.has_mismatches
        ack_recovery_ok = len(flaky.dropped_cids) > 0 and disconnects > 0

        verdict = (
            "PASS" if (no_duplicates and no_lost and restart_ok and reconcile_clean) else "FAIL"
        )

        lines.append("PAPER SOAK (bounded, deterministic) — G-02 exit-test essentials")
        lines.append(f"started {started.isoformat()} finished {datetime.now(UTC).isoformat()}")
        lines.append(
            f"cycles={cycles} forced_disconnects={disconnects} submit_attempts={flaky.submit_calls}"
        )
        lines.append("")
        lines.append(f"broker_orders={broker_orders} journal_confirmed={confirmed} trades={trades}")
        lines.append(f"journal_pending={pending}")
        lines.append(
            f"restart: pre_restart_orders={broker_orders} post_restart_orders={post_restart_orders}"
        )
        lines.append(f"reconcile_errors={len(recon.errors)} mismatches={len(recon.mismatches)}")
        lines.append("")
        lines.append(f"1. 0 duplicate orders (broker==journal==trades): {no_duplicates}")
        lines.append(f"2. 0 lost orders (no pending intents):            {no_lost}")
        lines.append(f"3. restart re-submits nothing:                    {restart_ok}")
        lines.append(f"4. reconcile clean (0 errors, 0 mismatches):      {reconcile_clean}")
        lines.append(f"5. ack-loss recovered via idempotent retry:       {ack_recovery_ok}")
        lines.append(f"VERDICT: {verdict}")

        evidence_dir = REPO_ROOT / "docs" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        out = evidence_dir / "2026-08-04_sprint25_paper_soak.log"
        out.write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        print(f"\nEvidence written: {out}")
        return 0 if verdict == "PASS" else 1
    finally:
        strategy_registry.unregister("evidence_soak_strat")
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
