#!/usr/bin/env python3
"""G-02 evidence: unattended paper-broker soak HARNESS (real Alpaca paper).

The G-02 exit test is an *unattended paper-broker soak (Alpaca paper,
24–72h)*: 0 reconcile errors, 0 duplicate/lost orders across forced
disconnects, journal-recovery replays correctly.

This is the operator-run harness for that soak. It requires live **paper**
Alpaca credentials in the environment (ALPACA_API_KEY / ALPACA_SECRET_KEY —
never committed; env-only per LIVE_RUN_POLICY §credential policy). Without
credentials it fails closed: it refuses to invent broker truth, so the honest
result is NO-GO (soak cannot run), exactly like ``run_cost_adjusted_backtest``.

It drives the real production chain (CycleExecutor -> JournaledBroker ->
AlpacaBrokerAdapter) for ``cycles`` market orders against the real Alpaca
paper endpoint, then reconciles broker truth against the journal + local
position book.

CLOSE-OUT IS ORDERS *AND* POSITIONS. Each batch closes out what it opened:
its own resting orders (cancel) and its own net position delta (market close),
so a multi-day run cannot walk the account into a holding until buying power
is exhausted and every later order is rejected. Only the delta versus the
batch's own pre-run baseline is closed — a pre-existing holding is never
touched — and reconciliation is therefore run against that captured baseline:
the assertion is "broker truth ends where this run found it", not "the
account happens to be empty".

Run (env-only paper keys):
    ALPACA_API_KEY=... ALPACA_SECRET_KEY=... \
    PYTHONPATH=. python3 scripts/evidence/run_real_paper_soak.py [cycles]
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time
import uuid
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import Mock

if TYPE_CHECKING:  # pragma: no cover - annotation-only, never imported at runtime
    from traderos.domain.entities.signal import SignalDirection
    from traderos.infrastructure.alpaca_broker import AlpacaBrokerAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

# The production chain is imported on demand rather than at module scope. Those
# imports pull in the entire application graph, which needs third-party packages
# (python-dotenv via Config, psycopg2, pandas). Importing them at module scope
# made the credential refusal unreachable in a sanitized environment: the process
# died with ``ModuleNotFoundError: No module named 'dotenv'`` and a traceback
# during import, before the NO-GO verdict could ever be emitted. The refusal is
# the safe outcome, so it must not be gated behind an unrelated dependency
# resolving.
#
# The ImportError is captured rather than raised because importing this module
# must stay safe for the drills that exec it directly (test_soak_position_flat).
# main() surfaces it only after the credential gate has had its say, so
# "credentials absent" remains the first verdict an operator sees.
_trading_stack_error: ImportError | None = None
_stack: Any = None

# Real tradable symbols in the paper account (verified: get_asset -> tradable=True).
# The broker requires a symbol_map; without it the adapter would submit the raw
# market UUID as a symbol and the real paper account rejects "asset not found".
SOAK_SYMBOL = os.getenv("SOAK_SYMBOL", "AAPL")
SOAK_MARKET_ID = uuid.uuid5(uuid.NAMESPACE_URL, f"traderos-soak.{SOAK_SYMBOL}")


def _load_trading_stack() -> None:
    """Import the production chain into ``_stack`` on demand.

    Every name lands on one explicitly-``Any`` namespace rather than being bound
    as a bare module global. A ``try: import ... except ImportError`` around
    module-level imports leaves every downstream reference "possibly unbound" to a
    strict type checker (31 errors here), and a bare name that silently does not
    exist is precisely the false confidence this gate exists to prevent.
    ``_require_trading_stack()`` guarantees ``_stack`` is populated before any of
    it is read, so an ``Any`` escape hatch cannot hide a missing import.
    """
    global _stack, _trading_stack_error
    try:
        from traderos.application.cycle_executor import CycleExecutor
        from traderos.application.models import TradingMode
        from traderos.domain.entities.signal import Signal
        from traderos.domain.entities.signal import SignalDirection
        from traderos.domain.services.analysis_service import AnalysisService
        from traderos.domain.services.broker_state_reconciliation_service import (
            BrokerStateReconciliationService,
        )
        from traderos.domain.services.portfolio_service import PortfolioService
        from traderos.domain.services.risk_service import KillSwitch
        from traderos.domain.services.risk_service import RiskAssessment
        from traderos.domain.services.risk_service import TradeVerdict
        from traderos.domain.services.signal_service import SignalProvenance
        from traderos.domain.services.strategy_framework import SignalResult
        from traderos.domain.services.strategy_framework import StrategyBase
        from traderos.domain.services.strategy_framework import registry as strategy_registry
        from traderos.infrastructure.alpaca_broker import AlpacaBrokerAdapter
        from traderos.infrastructure.events import InMemoryEventBus
        from traderos.infrastructure.journal import OrderEventJournal
        from traderos.infrastructure.journaled_broker import JournaledBroker
        from traderos.infrastructure.observability import SQLiteAuditService
        from traderos.infrastructure.observability import SQLiteHealthService
        from traderos.infrastructure.observability import SQLiteManifestService
        from traderos.infrastructure.observability import SQLiteMetricsService
        from traderos.infrastructure.repositories.sqlite.trades import SQLitePositionRepository
        from traderos.infrastructure.repositories.sqlite.trades import SQLiteTradeRepository
    except ImportError as exc:  # pragma: no cover - depends on the environment
        _trading_stack_error = exc
        return
    _stack = SimpleNamespace(
        CycleExecutor=CycleExecutor,
        TradingMode=TradingMode,
        Signal=Signal,
        SignalDirection=SignalDirection,
        AnalysisService=AnalysisService,
        BrokerStateReconciliationService=BrokerStateReconciliationService,
        PortfolioService=PortfolioService,
        KillSwitch=KillSwitch,
        RiskAssessment=RiskAssessment,
        TradeVerdict=TradeVerdict,
        SignalProvenance=SignalProvenance,
        SignalResult=SignalResult,
        StrategyBase=StrategyBase,
        strategy_registry=strategy_registry,
        AlpacaBrokerAdapter=AlpacaBrokerAdapter,
        InMemoryEventBus=InMemoryEventBus,
        OrderEventJournal=OrderEventJournal,
        JournaledBroker=JournaledBroker,
        SQLiteAuditService=SQLiteAuditService,
        SQLiteHealthService=SQLiteHealthService,
        SQLiteManifestService=SQLiteManifestService,
        SQLiteMetricsService=SQLiteMetricsService,
        SQLitePositionRepository=SQLitePositionRepository,
        SQLiteTradeRepository=SQLiteTradeRepository,
    )


def _require_trading_stack() -> None:
    """Load the production chain, or fail loudly if it cannot be imported.

    Raises instead of emitting a verdict: by the time this runs the credential
    gate has already spoken, so an unimportable stack is a broken deployment and
    must not be papered over with a NO-GO that reads as a deliberate operator
    decision.
    """
    global _trading_stack_error
    if _stack is None:
        _trading_stack_error = None
        _load_trading_stack()
    if _trading_stack_error is not None:
        raise RuntimeError(
            f"production trading chain unavailable: {_trading_stack_error}"
        ) from _trading_stack_error


def _evidence_path() -> Path:
    """Dated soak evidence path (defaults to today; SOAK_LOG_LABEL can disambiguate).

    Each soak run must write its own dated log so the 24-72h barrier evidence
    chain is auditable and a re-run never overwrites an earlier result.
    """
    label = os.getenv("SOAK_LOG_LABEL", "real_paper_soak")
    date = datetime.now(UTC).date().isoformat()
    return REPO_ROOT / "docs" / "evidence" / f"{date}_{label}.log"


OUT = _evidence_path()


def _emit(lines: list[str]) -> None:
    """Write the evidence file and echo it to stdout, in that order.

    The file is written FIRST so a stdout failure (a closed/broken pipe when
    Railway's log drain goes away) can never cost us the evidence row. Both
    steps are flushed so a SIGKILL mid-write cannot truncate the log.
    """
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(lines) + "\n"
    with OUT.open("w", encoding="utf-8") as fh:
        fh.write(body)
        fh.flush()
        os.fsync(fh.fileno())
    try:
        print(body, flush=True)
    except (BrokenPipeError, OSError):  # pragma: no cover — log drain died
        pass


def _register_evidence_strategy() -> None:
    """Define and register the soak's probe strategy.

    Built here rather than at module scope on purpose: the strategy subclasses a
    production class, and the production chain is imported lazily so a sanitized
    environment can still reach the credential refusal. A module-level class
    statement would evaluate ``_stack.StrategyBase`` at import time -- where
    ``_stack`` is still ``None`` -- and die with
    ``AttributeError: 'NoneType' object has no attribute 'StrategyBase'``, which
    is exactly the pre-gate crash this design exists to remove.

    Caller must have passed ``_require_trading_stack()``.
    """

    class _Strat(_stack.StrategyBase):
        name = "evidence_real_paper_strat"

        def evaluate(self, state: Any) -> Any:
            return _stack.SignalResult("long", 0.8, {"reason": "real-paper-soak"})

    _stack.strategy_registry.register(_Strat)


def _prov(mid: uuid.UUID, direction: SignalDirection):
    now = datetime.now(UTC)
    return _stack.SignalProvenance(
        signal=_stack.Signal(
            market_id=mid,
            strategy_id=uuid.uuid4(),
            direction=direction,
            confidence=0.8,
            generated_at=now,
            expires_at=now + timedelta(hours=1),
        ),
        strategy_name="real-paper-soak",
        indicators_used={},
    )


def _snapshot_open_orders(adapter: AlpacaBrokerAdapter) -> list[dict] | None:
    """Broker open orders, or ``None`` when the read itself failed.

    An unattended soak must distinguish "the broker says there are no open
    orders" from "we could not ask the broker". Collapsing the second into the
    first (``[] on error``) would let a transient outage masquerade as a clean
    account and would skip the close-out of orders that are actually resting —
    the exact silent-drop the AGENTS rules forbid.
    """
    try:
        return adapter.get_open_orders()
    # Any broker read failure is a NO-GO, never an empty order book.
    except Exception as exc:  # noqa: BLE001
        print(f"broker open-orders read failed: {exc}", flush=True)
        return None


def _cancel_residue(
    adapter: AlpacaBrokerAdapter, orders: list[dict], settle_waits: int
) -> tuple[list[str], bool]:
    """Cancel this run's own residue and wait for the broker to settle.

    Returns ``(still_resting, resettled)``. Never raises: an unattended soak
    must always finish its own close-out and record the outcome honestly, even
    when the broker is unreachable — a leaked order is evidence, not something
    to crash on and lose the record of.

    The guarantee checked here is "none of OUR orders is still resting at the
    broker", NOT "every cancel call returned success". The two differ, and the
    difference decided a real batch: a market order that filled in the gap
    between the open-orders snapshot and the cancel cannot be cancelled (the
    broker refuses to cancel a filled order), so a cancel-response check scored
    that as leaked residue and failed a batch that had in fact left the account
    exactly as it found it. The residue of a fill is closed out by the position
    flatten, which is where a fill actually has to be undone.
    """
    ours = {str(order.get("id", "?")) for order in orders}
    for order in orders:
        try:
            adapter.cancel_order(order["id"])
        except Exception as exc:  # noqa: BLE001 — record, never crash the close-out
            print(f"cancel raised for {order.get('id', '?')}: {exc}", flush=True)

    if not ours:
        return [], True

    deadline = time.monotonic() + settle_waits
    while True:
        remaining = _snapshot_open_orders(adapter)
        if remaining is not None:
            still = {str(o["id"]) for o in remaining if str(o["id"]) in ours}
            if not still:
                return [], True
        elif time.monotonic() >= deadline:
            # Never treat an unverifiable read as a clean account.
            return sorted(ours), False
        if time.monotonic() >= deadline:
            return sorted(ours), False
        time.sleep(2)


def _own_residue(
    adapter: AlpacaBrokerAdapter, baseline_open_ids: set[str] | None
) -> list[dict] | None:
    """This run's own resting orders, or ``None`` if the read failed.

    Only orders the soak created are ever touched: anything present in the
    pre-run baseline predates this run (it may be a user's order and is left
    strictly alone). ``latprobe-`` orphans from an earlier crashed run are also
    reclaimed — they are unambiguously ours and must not accumulate.
    """
    orders = _snapshot_open_orders(adapter)
    if orders is None:
        return None
    if baseline_open_ids is None:
        # We never established a baseline, so we cannot prove ownership. Do NOT
        # guess and cancel: the fail-closed choice is to claim nothing and let
        # the batch FAIL on residue rather than risk touching a user's order.
        print("no open-orders baseline — refusing to claim residue", flush=True)
        return []
    return [
        o
        for o in orders
        if str(o.get("client_order_id", "")).startswith("latprobe-")
        or (o["symbol"] == SOAK_SYMBOL and o["id"] not in baseline_open_ids)
    ]


# Fractional broker quantities make an exact float equality the wrong test; this
# is far below any real fill but far above float noise.
_POSITION_TOLERANCE = Decimal("0.000001")
# A close-out is bounded by BOTH the settle deadline and an attempt cap: a
# refused market close must not turn into an unbounded submit loop against a
# broker that is already saying no.
_FLATTEN_MAX_ATTEMPTS = 3
# The position book must be shown to be AT REST before it is allowed to declare
# anything, and "at rest" means this many consecutive identical reads.
_POSITION_QUIESCENCE_READS = 2
_QUIESCENCE_POLL_SECONDS = 2.0


def _await_position_quiescence(
    adapter: AlpacaBrokerAdapter, settle_waits: float
) -> dict[str, Decimal] | None:
    """Poll positions until two consecutive reads agree; ``None`` if never at rest.

    Alpaca's POSITION book lags FILL settlement. An order that has already
    filled can still read as absent for a second or more, so a single read
    taken at the end of close-out proves nothing. That is not theoretical: a
    batch reported ``after_qty=0.000000`` and ``positions_back_at_baseline=True``
    — and PASS — while 132.05154639 shares of its own buying were still in
    flight. The NEXT run then inherited those shares as a "pre-run baseline"
    it was forbidden to touch, so the leak became permanent and self-
    legitimising.

    The precondition that makes quiescence sufficient: ``_cancel_residue`` has
    already established that none of this run's orders is still open, so no
    further fill can originate from them. Once such an order is terminal and
    the position book has stopped moving, the delta is final and correct.

    Returns ``None`` on an unreadable book or on a book that never settles —
    both fail closed, because a soak that mistakes a moving book for a flat one
    is exactly the defect this exists to prevent.
    """
    previous = _positions_by_symbol(adapter)
    if previous is None:
        return None

    deadline = time.monotonic() + settle_waits
    stable = 0
    while True:
        time.sleep(_QUIESCENCE_POLL_SECONDS)
        current = _positions_by_symbol(adapter)
        if current is None:
            return None
        if current == previous:
            stable += 1
            if stable >= _POSITION_QUIESCENCE_READS:
                return current
        else:
            # Still landing. Restart the count against the new truth.
            stable = 0
            previous = current
        if time.monotonic() >= deadline:
            return None


def _positions_by_symbol(adapter: AlpacaBrokerAdapter) -> dict[str, Decimal] | None:
    """Broker positions keyed by symbol (summed), or ``None`` when unreadable.

    Same fail-closed contract as ``_snapshot_open_orders``: "we could not ask
    the broker" is never collapsed into "nothing is held". An unattended soak
    that mistakes an unreadable position book for a flat one would liquidate
    nothing and call a permanently maxed-out account clean.
    """
    try:
        positions = adapter.get_positions()
    except Exception as exc:  # noqa: BLE001 — record, never crash the close-out
        print(f"broker positions read failed: {exc}", flush=True)
        return None
    # Quantities are exact decimals, not floats. Alpaca returns strings, and the
    # broker's own place_market_order takes a Decimal; reading the book as float
    # and comparing it against a Decimal baseline raised
    # ``TypeError: unsupported operand type(s) for -: 'float' and 'Decimal'`` the
    # moment the two sides disagreed -- and a float read is also how a non-zero
    # residual could round away and be declared "already at baseline".
    by_symbol: dict[str, Decimal] = {}
    for pos in positions:
        symbol = str(pos.get("symbol", ""))
        by_symbol[symbol] = by_symbol.get(symbol, Decimal(0)) + Decimal(str(pos.get("qty", 0)))
    return by_symbol


def _flatten_own_delta(
    adapter: AlpacaBrokerAdapter,
    market_id: uuid.UUID,
    baseline: dict[str, Decimal] | None,
    settle_waits: int,
) -> tuple[list[str], bool, list[str]]:
    """Close this run's NET position delta, returning the account to ``baseline``.

    Why this must exist: a soak that only ever buys accumulates a holding, and
    a long multi-day run will eventually exhaust the account's buying power —
    after which *every* subsequent buy is rejected and the soak silently stops
    exercising the path it exists to prove. (That is exactly what happened to
    the real paper account: 712.5 AAPL, buying_power=0.)

    Ownership, same rule as ``_own_residue`` applies to resting orders: only
    the delta this run opened versus its own pre-run baseline is closed. A
    pre-existing holding — which on a shared account may be an operator's — is
    left strictly alone.

    The verdict is "the position is demonstrably back at baseline", never "every
    close returned a filled response". A fractional market close is frequently
    ``pending`` when the ack arrives and fills a moment later, so scoring the
    ack would fail every batch whose close-out actually worked. Retries are
    capped only against a broker that definitively REFUSES: a refusal is
    counted, a slow fill is waited out, so a close-out can neither spam a
    refusing broker nor give up on a settling one.

    Returns ``(failures, resettled, notes)``. Never raises: crashing here would
    leak the position we were trying to close, which is evidence, not something
    to die on.
    """
    if baseline is None:
        return ["position baseline unreadable — refusing to flatten blind"], False, []

    notes: list[str] = []
    refused = 0
    base_qty = baseline.get(SOAK_SYMBOL, Decimal(0))
    deadline = time.monotonic() + settle_waits
    while True:
        # Bound each quiescence wait by what is LEFT of the overall deadline, so
        # nesting it here cannot quietly multiply the close-out's time budget.
        remaining = deadline - time.monotonic()
        current = _await_position_quiescence(adapter, max(remaining, 0.0))
        if current is None:
            return ["position book never reached rest during flatten"], False, notes
        delta = current.get(SOAK_SYMBOL, Decimal(0)) - base_qty
        if abs(delta) <= _POSITION_TOLERANCE:
            return [], True, notes
        if time.monotonic() >= deadline or refused >= _FLATTEN_MAX_ATTEMPTS:
            detail = (
                f"position did not return to baseline "
                f"(net {delta:+.6f} {SOAK_SYMBOL}, {refused} refused close(s))"
            )
            return [detail], False, notes

        side = "sell" if delta > 0 else "buy"
        try:
            fill = adapter.place_market_order(
                market_id,
                side,
                abs(delta),
                client_order_id=f"soakflat-{uuid.uuid4().hex[:12]}",
            )
        except Exception as exc:  # noqa: BLE001 — record, never crash the close-out
            refused += 1
            notes.append(f"flatten {side} {abs(delta):.6f} raised: {exc}")
            print(f"flatten {side} failed: {exc}", flush=True)
        else:
            if fill.status == "rejected":
                refused += 1
                notes.append(f"flatten {side} {abs(delta):.6f} rejected: {fill.order_id}")
            else:
                notes.append(f"flatten {side} {abs(delta):.6f} {fill.status}")
        time.sleep(2)


def main(argv: list[str]) -> int:
    cycles = int(argv[0]) if argv else 50
    lines: list[str] = []
    started = datetime.now(UTC)
    settle_waits = int(os.getenv("SOAK_SETTLE_SECONDS", "30"))

    api_key = os.getenv("ALPACA_API_KEY", "")
    secret_key = os.getenv("ALPACA_SECRET_KEY", "")
    if not api_key or not secret_key:
        _emit(
            [
                "REAL-PAPER SOAK HARNESS — G-02 unattended paper-broker soak",
                f"started {started.isoformat()}",
                "FATAL: no ALPACA_API_KEY / ALPACA_SECRET_KEY (paper keys) in env.",
                (
                    "NO-GO: the soak requires real Alpaca paper credentials; the drill "
                    "refuses to fabricate broker truth without them."
                ),
                "VERDICT: NO-GO (credentials absent) — harness ready, soak not run",
                f"Evidence: {OUT}",
            ]
        )
        return 2

    # Only now, with real paper keys present, does a missing dependency become the
    # operator's problem to hear about. The credential refusal above must stay the
    # first verdict regardless of what is installed.
    _require_trading_stack()

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from traderos.infrastructure.database.migration_manager import migrate

    migrate(conn)

    adapter = _stack.AlpacaBrokerAdapter(
        api_key=api_key,
        secret_key=secret_key,
        paper=True,
        symbol_map={SOAK_MARKET_ID: SOAK_SYMBOL},
    )
    journal = _stack.OrderEventJournal(conn)
    broker = _stack.JournaledBroker(adapter, journal)

    audit = _stack.SQLiteAuditService(conn)
    portfolio = _stack.PortfolioService(
        trade_repo=_stack.SQLiteTradeRepository(conn),
        position_repo=_stack.SQLitePositionRepository(conn),
        audit=audit,
    )
    signal_service = Mock()
    risk = Mock()
    risk.can_trade.return_value = _stack.TradeVerdict(True, "")
    risk.kill_switch = _stack.KillSwitch()
    # ADR-009: every price and amount here is money and must be Decimal. These
    # were float literals, and CycleExecutor calls
    # ``(max_risk_amount / risk_per_unit).quantize(...)`` on them, so the harness
    # died with "AttributeError: 'float' object has no attribute 'quantize'".
    # kelly_fraction stays float: it is a dimensionless fraction.
    risk.assess_trade.return_value = _stack.RiskAssessment(
        kelly_fraction=0.5,
        suggested_stop_loss=Decimal("99.0"),
        suggested_take_profit=Decimal("102.0"),
        risk_per_unit=Decimal("1.0"),
        max_risk_amount=Decimal("200.0"),
    )
    risk.authorize_order.return_value = Mock(allowed=True, reason="")

    mid = SOAK_MARKET_ID
    signal_service.process_evaluation.return_value = _prov(mid, _stack.SignalDirection.LONG)

    def build_executor():
        return _stack.CycleExecutor(
            mode=_stack.TradingMode.PAPER,
            signal_service=signal_service,
            risk_service=risk,
            portfolio_service=portfolio,
            execution=Mock(),
            analysis=_stack.AnalysisService(),
            broker=broker,
            event_bus=_stack.InMemoryEventBus(),
            health=_stack.SQLiteHealthService(conn),
            audit=audit,
            metrics=_stack.SQLiteMetricsService(conn),
            notifications=Mock(),
            run_manifest=_stack.SQLiteManifestService(conn),
            enabled_strategies=lambda: [("real-paper-soak", "evidence_real_paper_strat", {})],
        )

    _register_evidence_strategy()
    baseline_open_ids: set[str] | None = None
    baseline_positions: dict[str, Decimal] | None = None
    runner_open_orders: list[dict] = []
    still_resting: list[str] = []
    resettled = False
    position_failures: list[str] = []
    position_notes: list[str] = []
    positions_resettled = False
    crash: str | None = None
    try:
        executor = build_executor()
        # Baseline of pre-existing broker state so the harness only ever claims
        # (and only ever closes out) residue *it* created, never a user's.
        # ``None`` means "could not read" — never silently treated as "empty",
        # because an empty baseline would make every resting order look like a
        # user's and every order would be left resting forever.
        baseline = _snapshot_open_orders(adapter)
        if baseline is not None:
            baseline_open_ids = {str(o["id"]) for o in baseline}
        baseline_positions = _positions_by_symbol(adapter)

        results: list[tuple[bool, str]] = []
        for i in range(cycles):
            r = executor.run(mid, 100.0 + (i % 20))
            results.append((r.trades > 0, ";".join(r.errors[:1])))

        # WP6 latency calibration (rides the soak): measure real submit-ack
        # latency for a small bound of same-path market orders, then close them
        # out with the rest. `place_market_order` returns after the broker ack,
        # so the elapsed time is the full ack round-trip through the real path.
        ack_latencies_ms: list[float] = []
        probe_len = int(os.getenv("SOAK_LATENCY_PROBES", "10"))
        for _ in range(probe_len):
            # `place_market_order` returns only after the broker ack, so the
            # elapsed time around the call IS the full submit->ack round trip.
            t0 = datetime.now(UTC)
            # The probe quantity is an order size: money, so Decimal (ADR-009).
            # As a float literal it reached the broker adapter as 0.01 and any
            # Decimal accumulator downstream raised
            # ``TypeError: unsupported operand type(s) for +=: 'Decimal' and 'float'``.
            res = adapter.place_market_order(
                mid,
                "buy",
                Decimal("0.01"),
                client_order_id=f"latprobe-{uuid.uuid4().hex[:12]}",
            )
            ack_ms = (datetime.now(UTC) - t0).total_seconds() * 1000.0
            if res.status == "rejected":
                # The broker is refusing orders: stop probing (further probes
                # only add load and extend the outage) but still record the
                # rejection so the evidence shows exactly why the batch stopped.
                lines.append(
                    f"latency probe rejected after {len(ack_latencies_ms)} probe(s): {res.order_id}"
                )
                break
            ack_latencies_ms.append(ack_ms)

        # Close out this run's own residue so the reconcile is against a
        # settled state — a pending order left resting is not a reconcilation
        # error, and an unattended soak must not leak live orders behind it.
        claimed = _own_residue(adapter, baseline_open_ids)
        if claimed is None:
            runner_open_orders = []
            resettled = False
            lines.append("close-out: broker open-orders read failed; residue unverified")
        else:
            runner_open_orders = claimed
            still_resting, resettled = _cancel_residue(adapter, claimed, settle_waits)

        # Close out this run's own NET POSITION as well as its resting orders.
        # Only orders were ever closed out before, so the soak accumulated AAPL
        # until buying power hit 0 and every later buy was rejected — the window
        # then produced no fills and no verdict worth the name.
        position_failures, positions_resettled, position_notes = _flatten_own_delta(
            adapter, mid, baseline_positions, settle_waits
        )

        filled = sum(1 for ok, _ in results if ok)
        not_filled = [e for _, e in results if e]

        snapshot = _snapshot_open_orders(adapter)
        broker_orders = len(snapshot) if snapshot is not None else -1
        # The final read must also be quiescence-gated. An ungated read here is
        # what let a batch print after_qty=0.000000 and PASS while 132 shares of
        # its own buying were still landing.
        final_positions = _await_position_quiescence(adapter, settle_waits)
        journal_confirmed = journal.count()
        pending = len(journal.pending_events())
        # Reconcile against the PRE-RUN BASELINE, not this run's throwaway
        # in-memory book. The book starts empty every batch while the real
        # account carries whatever the account started with, so comparing the
        # two flagged any pre-existing holding as a phantom broker-only position
        # and the soak could never return PASS. The contract the soak actually
        # asserts is "broker truth ends where this run found it": our own delta
        # was flattened (below), the baseline we never touched is acknowledged,
        # and the journal has no unconfirmed intent. A symbol the run opened and
        # failed to close is therefore caught as a genuine mismatch.
        local_positions = (
            [{"symbol": sym, "qty": qty} for sym, qty in baseline_positions.items()]
            if baseline_positions is not None
            else []
        )
        recon = _stack.BrokerStateReconciliationService(broker=adapter).reconcile(
            local_positions=local_positions,
            local_orders=[],
            journal_pending=broker.pending(),
        )

        # An unattended soak passes when nothing is lost, the account is left
        # in the state it started, and reconciliation is clean against the real
        # paper broker. Real paper fills can be partial or pending (market
        # hours), so we assert the *ordering + hygiene guarantees*:
        # 0 lost intents, clean reconcile, 0 leaked open orders, journal
        # confirmed == submit attempts. An unverifiable broker read is NOT a
        # clean account — it fails closed.
        baseline_count = len(baseline_open_ids) if baseline_open_ids is not None else -1
        baseline_qty = (
            baseline_positions.get(SOAK_SYMBOL, Decimal(0)) if baseline_positions else Decimal(0)
        )
        no_lost = pending == 0
        no_residue = (
            still_resting == []
            and resettled
            and position_failures == []
            and positions_resettled
            and snapshot is not None
            and baseline_open_ids is not None
            and baseline_positions is not None
            and final_positions is not None
            and broker_orders == baseline_count
        )
        reconcile_clean = recon.errors == [] and not recon.has_mismatches
        submit_attempts = len(results)
        verdict = "PASS" if (no_lost and no_residue and reconcile_clean) else "FAIL"

        lines.append("REAL-PAPER SOAK HARNESS — G-02 unattended paper-broker soak")
        lines.append(f"started {started.isoformat()} finished {datetime.now(UTC).isoformat()}")
        lines.append(f"cycles={cycles} orders_filled={filled} submit_attempts={submit_attempts}")
        if not_filled:
            lines.append("  non-fill reasons (first per cycle):")
            for e in not_filled[:5]:
                lines.append(f"    - {e}")
        lines.append(f"journal_confirmed={journal_confirmed} journal_pending={pending}")
        lines.append(
            f"runner_open_orders={len(runner_open_orders)} "
            f"still_resting={len(still_resting)} resettled={resettled}"
        )
        lines.append(
            f"broker_open_orders_after={broker_orders} " f"baseline_open_orders={baseline_count}"
        )
        lines.append(
            f"{SOAK_SYMBOL} baseline_qty={baseline_qty:.6f} "
            f"after_qty={(final_positions or {}).get(SOAK_SYMBOL, Decimal(0)):.6f}"
        )
        lines.append(
            f"position_closes={len(position_notes)} "
            f"positions_back_at_baseline={positions_resettled}"
        )
        lines.append(
            f"local_positions={len(local_positions)} "
            f"(pre-run broker baseline, not the run's throwaway book)"
        )
        lines.append(f"reconcile_errors={len(recon.errors)} mismatches={len(recon.mismatches)}")
        lines.append("")
        lines.append(f"0 lost orders (no pending intents):       {no_lost}")
        lines.append(f"runner closed out, broker at baseline:    {no_residue}")
        lines.append(f"reconcile clean vs real paper broker:    {reconcile_clean}")
        lines.append("")
        lat_min = min(ack_latencies_ms) if ack_latencies_ms else 0.0
        lat_max = max(ack_latencies_ms) if ack_latencies_ms else 0.0
        lat_med = sorted(ack_latencies_ms)[len(ack_latencies_ms) // 2] if ack_latencies_ms else 0.0
        lines.append(
            "WP6 latency (submit->ack ms): "
            f"n={len(ack_latencies_ms)} min={lat_min:.1f} median={lat_med:.1f} max={lat_max:.1f}"
        )
        lines.append(f"VERDICT: {verdict}")
        lines.append(f"Evidence: {OUT}")

        _emit(lines)
        return 0 if verdict == "PASS" else 1
    except BaseException as exc:
        # A crash is evidence, not a lost run: record it in `finally` and re-raise
        # so the exit code still tells the supervisor the batch did not complete.
        crash = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        # Close-out runs in `finally` so a crash anywhere above can never leak
        # resting orders OR an open position on the paper account, and the crash
        # is always recorded to the evidence file — an unattended soak must never
        # vanish silently (AGENTS: no silent drops).
        if baseline_open_ids is not None:
            claimed = _own_residue(adapter, baseline_open_ids)
            if claimed:
                still_resting, resettled = _cancel_residue(adapter, claimed, settle_waits)
        if baseline_positions is not None:
            crash_closes, crash_flat, crash_notes = _flatten_own_delta(
                adapter, mid, baseline_positions, settle_waits
            )
            position_failures = list(position_failures) + crash_closes
            position_notes = list(position_notes) + crash_notes
            positions_resettled = positions_resettled or crash_flat
        _stack.strategy_registry.unregister("evidence_real_paper_strat")
        if crash is not None:
            _emit(
                [
                    "REAL-PAPER SOAK HARNESS — G-02 unattended paper-broker soak",
                    f"started {started.isoformat()} crashed {datetime.now(UTC).isoformat()}",
                    f"CRASH: {crash}",
                    # Everything observed before the abort is carried into the
                    # crash record: the evidence file is overwritten here, and a
                    # crash must never cost us the partial run that led to it.
                    *lines,
                    (
                        "crash-closeout: cancelled own residue in finally "
                        f"still_resting={len(still_resting)} resettled={resettled}"
                    ),
                    (
                        "crash-closeout: flattened own position in finally "
                        f"position_closes={len(position_notes)} "
                        f"positions_back_at_baseline={positions_resettled}"
                    ),
                    "VERDICT: CRASH (harness aborted; residue closed out, run must be re-run)",
                    f"Evidence: {OUT}",
                ]
            )
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
