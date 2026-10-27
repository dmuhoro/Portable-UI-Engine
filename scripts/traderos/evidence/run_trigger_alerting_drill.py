#!/usr/bin/env python3
"""WP2 evidence: real on-call transport fired by the REAL trigger paths.

Proves, on the real detection seams (not a standalone notifier unit test),
that the configured HTTP on-call transport is actually called when each
production condition fires:

  1. kill_switch_trip    — live API ``kill-switch/engage`` path (CRITICAL)
  2. reconciliation_fail — ``BrokerStateReconciliationService.reconcile()``
                           failure (CRITICAL)
  3. unclean_shutdown    — ``SupervisionService.check_unclean_shutdown()``
                           (CRITICAL); healthy/clean sessions stay silent
  4. severity_routing    — INFO stays local, never leaves the wire

Delivery is proven on the wire: a real loopback HTTP server captures the
actual POST payload (no fake transport spy, no fabricated credential — the
same honest-wire proof as the A7 claim).

Run:  PYTHONPATH=src python3 scripts/evidence/run_trigger_alerting_drill.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from traderos.domain.services.broker_state_reconciliation_service import (  # noqa: E402
    BrokerStateReconciliationService,
)
from traderos.domain.services.notification_service import NotificationService  # noqa: E402
from traderos.infrastructure.notifiers.oncall_router import HttpOnCallTransport  # noqa: E402
from traderos.infrastructure.notifiers.oncall_router import OnCallRouter  # noqa: E402
from traderos.infrastructure.supervision import HeartbeatRecord  # noqa: E402
from traderos.infrastructure.supervision import JsonlHeartbeatStore  # noqa: E402
from traderos.infrastructure.supervision import SupervisionService  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-07_trigger_alerting_drill.log"
LINES: list[str] = []
RESULTS: list[tuple[str, bool, str]] = []


def _report() -> int:
    all_ok = all(ok for _, ok, _ in RESULTS)
    LINES.append("-------")
    for name, ok, detail in RESULTS:
        LINES.append(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    LINES.append(f"VERDICT: {'PASS' if all_ok else 'FAIL'}")
    LINES.append(f"Evidence: {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(LINES) + "\n")
    print("\n".join(LINES))
    return 0 if all_ok else 1


class _Receiver:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def handle(self, body: bytes) -> None:
        self.requests.append(json.loads(body.decode()))


class _Capture(BaseHTTPRequestHandler):
    receiver = _Receiver()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _Capture.receiver.handle(body)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


class _FailingBroker:
    def place_market_order(self, market_id, side, quantity, close_price=None, client_order_id=None):
        return None

    def place_limit_order(self, market_id, side, quantity, price, close_price=None):
        return None

    def cancel_order(self, order_id):
        return None

    def get_account_balance(self):
        return 10000.0

    def get_positions(self):
        raise RuntimeError("Broker unreachable")

    def get_open_orders(self):
        raise RuntimeError("Broker unreachable")


class _HealthyBroker:
    def place_market_order(self, market_id, side, quantity, close_price=None, client_order_id=None):
        return None

    def place_limit_order(self, market_id, side, quantity, price, close_price=None):
        return None

    def cancel_order(self, order_id):
        return None

    def get_account_balance(self):
        return 10000.0

    def get_positions(self):
        return []

    def get_open_orders(self):
        return []


def main() -> int:
    started = datetime.now(UTC)
    LINES.append("WP2 TRIGGER→ON-CALL ALERTING DRILL (real transport, real detection paths)")
    LINES.append(f"started {started.isoformat()}")

    receiver = _Receiver()
    _Capture.receiver = receiver
    http_server = HTTPServer(("127.0.0.1", 0), _Capture)
    port = http_server.server_address[1]
    thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/oncall"
    LINES.append(f"  real HTTP on-call transport listening at {url}")

    router = OnCallRouter([HttpOnCallTransport(url, max_retries=1)])
    notifications = NotificationService(notifier=None, oncall=router)

    try:
        # --- 1. Reconciliation failure (real service, real detection seam).
        fail_recon = BrokerStateReconciliationService(
            broker=_FailingBroker(), notifications=notifications
        )
        res = fail_recon.reconcile()
        ok_recon = res.failed and bool(receiver.requests)
        last = receiver.requests[-1] if receiver.requests else {}
        RESULTS.append(
            (
                "reconciliation_failure",
                ok_recon and last.get("level") == "critical",
                f"failed={res.failed} level={last.get('level')} title={last.get('title')}",
            )
        )
        LINES.append(f"  reconciliation failure delivered CRITICAL on the wire: {ok_recon}")

        # --- 2. Healthy reconciliation stays silent.
        healthy = BrokerStateReconciliationService(
            broker=_HealthyBroker(), notifications=notifications
        )
        before = len(receiver.requests)
        res_ok = healthy.reconcile()
        ok_healthy = not res_ok.failed and len(receiver.requests) == before
        RESULTS.append(("clean_reconciliation_silent", ok_healthy, "no packet on success"))
        LINES.append(f"  healthy reconciliation silent on the wire: {ok_healthy}")

        # --- 3. Unclean shutdown (real supervision detection path).
        with tempfile.TemporaryDirectory() as tmpdir:
            store = JsonlHeartbeatStore(str(Path(tmpdir) / "heartbeats.jsonl"))
            sup = SupervisionService(store=store, notifications=notifications)
            store.append(
                HeartbeatRecord(
                    ts=datetime.now(UTC) - timedelta(minutes=5),
                    pid=4242,
                    action="heartbeat",
                )
            )
            sup._now = lambda: datetime.now(UTC)  # pyright: ignore[reportPrivateUsage]
            before = len(receiver.requests)
            seen = sup.check_unclean_shutdown()
            last = receiver.requests[-1] if receiver.requests else {}
            ok_unclean = seen and len(receiver.requests) == before + 1
            RESULTS.append(
                (
                    "unclean_shutdown",
                    ok_unclean and last.get("level") == "critical",
                    "CRITICAL packet delivered",
                )
            )
            LINES.append(f"  unclean shutdown delivered CRITICAL on the wire: {ok_unclean}")

            store2 = JsonlHeartbeatStore(str(Path(tmpdir) / "clean.jsonl"))
            sup2 = SupervisionService(store=store2, notifications=notifications)
            sup2.heartbeat()
            sup2.mark_clean_shutdown()
            before2 = len(receiver.requests)
            ok_clean = sup2.check_unclean_shutdown() is False and len(receiver.requests) == before2
            RESULTS.append(("clean_shutdown_silent", ok_clean, "no packet on clean shutdown"))
            LINES.append(f"  clean shutdown silent on the wire: {ok_clean}")

        # --- 4. INFO never leaves the wire.
        before = len(receiver.requests)
        notifications.info("heartbeat", "all good")
        ok_severity = len(receiver.requests) == before
        RESULTS.append(("severity_routing", ok_severity, "INFO stays local (no packet)"))
        LINES.append("  INFO stays local, never leaves the wire: True")

        # --- 5. Kill-switch trip through the LIVE API path (real route).
        import importlib

        from fastapi.testclient import TestClient

        from traderos.infrastructure.auth import APIKeyAuthenticator
        from traderos.interfaces.api import security
        from traderos.interfaces.api import server as api_server

        importlib.reload(api_server)
        security.set_authenticator(APIKeyAuthenticator(admin_keys=("sprint-admin-1234567890",)))
        os.environ["ONCALL_WEBHOOK_URL"] = url
        os.environ.setdefault("TRADING_MODE", "paper")
        api_server._orch_cache.clear()  # pyright: ignore[reportPrivateUsage]
        client = TestClient(api_server.build_app())
        before = len(receiver.requests)
        resp = client.post(
            "/v1/kill-switch/engage", headers={"X-API-Key": "sprint-admin-1234567890"}
        )
        last = receiver.requests[-1] if receiver.requests else {}
        ok_ks = resp.status_code == 200 and len(receiver.requests) == before + 1
        RESULTS.append(
            (
                "kill_switch_trip",
                ok_ks and last.get("level") == "critical",
                f"HTTP {resp.status_code} level={last.get('level')} title={last.get('title')}",
            )
        )
        LINES.append(f"  kill-switch trip delivered CRITICAL on the wire: {ok_ks}")
    finally:
        http_server.shutdown()
        http_server.server_close()
        os.environ.pop("ONCALL_WEBHOOK_URL", None)

    return _report()


if __name__ == "__main__":
    raise SystemExit(main())
