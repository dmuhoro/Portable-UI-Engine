#!/usr/bin/env python3
"""A7 evidence: severity-routed on-call alert transport (fail-closed).

Proves, against the REAL production wiring, that a CRITICAL alert reaches an
external HTTP transport only when a transport actually acknowledges delivery:

1. severity_routing: INFO/WARNING/ERROR alerts stay local (no external packet).
2. delivered_on_2xx: a CRITICAL alert is delivered only when the external
   endpoint returns HTTP 2xx (packet/trace — the receiver captures the actual
   POST body), and the delivery is recorded to audit + metrics.
3. fail_closed_critical: when every transport refuses (5xx), a CRITICAL alert
   is NOT silently dropped — OnCallRouter records the failure and raises
   OnCallDeliveryError so the caller knows no one was paged.
4. low_severity_never_raises: a WARNING with an unreachable transport stays
   local (no failure raised) — severity routing, not fan-out-everything.

The external transport is a real HTTP server listening on a loopback socket;
delivery is proven by the receiver having captured the request — not by a
unit-test spy.

Run:  PYTHONPATH=src python3 scripts/evidence/run_oncall_drill.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
import threading
from datetime import UTC
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from traderos.domain.services.notification_service import NotificationLevel  # noqa: E402
from traderos.domain.services.notification_service import NotificationService  # noqa: E402
from traderos.infrastructure.notifiers.oncall_router import HttpOnCallTransport  # noqa: E402
from traderos.infrastructure.notifiers.oncall_router import OnCallDeliveryError  # noqa: E402
from traderos.infrastructure.notifiers.oncall_router import OnCallRouter  # noqa: E402
from traderos.infrastructure.observability import SQLiteAuditService  # noqa: E402
from traderos.infrastructure.observability import SQLiteMetricsService  # noqa: E402


def _evidence_path() -> Path:
    """Date-aware evidence path so a re-run never overwrites prior evidence."""
    date = datetime.now(UTC).date().isoformat()
    return REPO_ROOT / "docs" / "evidence" / f"{date}_oncall_transport_drill.log"


OUT = _evidence_path()


def _make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from traderos.infrastructure.database.migration_manager import migrate

    migrate(conn)
    return conn


class _Receiver:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def handle(self, body: bytes) -> None:
        self.requests.append(json.loads(body.decode()))


class _Capture(BaseHTTPRequestHandler):
    receiver: _Receiver = _Receiver()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _Capture.receiver.handle(body)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


class _Reject(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        self.send_response(503)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> int:
    lines: list[str] = []
    lines.append("ON-CALL TRANSPORT DRILL — A7 severity routing, fail-closed delivery")
    lines.append(f"started {datetime.now(UTC).isoformat()}")

    results: list[tuple[str, bool, str]] = []

    # --- 1+2: severity routing + delivery on 2xx against a real HTTP server.
    receiver = _Receiver()
    _Capture.receiver = receiver
    server = HTTPServer(("127.0.0.1", 0), _Capture)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    transport_url = f"http://127.0.0.1:{port}/oncall"

    conn = _make_conn()
    audit = SQLiteAuditService(conn)
    metrics = SQLiteMetricsService(conn)
    router = OnCallRouter([HttpOnCallTransport(transport_url)], audit=audit, metrics=metrics)
    notifications = NotificationService(notifier=None, oncall=router)

    lines.append(f"external transport listening at {transport_url}")
    try:
        notifications.info("instrument down", "below threshold")
        notifications.warning("late heartbeat", "below threshold")
        notifications.error("partial breach", "below threshold")
        below_stayed_local = len(receiver.requests) == 0
        lines.append(f"  INFO/WARNING/ERROR stayed local: {below_stayed_local}")

        notifications.critical("kill trip", "position flatten forced")
        delivered_packets = len(receiver.requests)
        last = receiver.requests[-1] if receiver.requests else {}
        delivered_on_2xx = (
            delivered_packets == 1
            and last.get("level") == "critical"
            and last.get("title") == "kill trip"
        )
        audit_after = {e.action for e in audit.get_entries()}
        metrics_after = {
            "oncall.delivered": metrics.get_counter("oncall.delivered"),
            "oncall.delivery_failed": metrics.get_counter("oncall.delivery_failed"),
        }
        results.append(
            (
                "severity_routing",
                below_stayed_local,
                "INFO/WARNING/ERROR produced no external packet",
            )
        )
        results.append(
            (
                "delivered_on_2xx",
                delivered_on_2xx,
                (
                    f"CRITICAL POST captured on the wire: level={last.get('level')} "
                    f"title={last.get('title')}"
                ),
            )
        )
        results.append(
            (
                "delivery_audited",
                "oncall.delivered" in audit_after,
                "delivery recorded to the durable audit trail",
            )
        )
        results.append(
            (
                "delivery_metric",
                metrics_after["oncall.delivered"] == 1.0
                and metrics_after["oncall.delivery_failed"] == 0.0,
                (
                    f"metrics: delivered={metrics_after['oncall.delivered']} "
                    f"failed={metrics_after['oncall.delivery_failed']}"
                ),
            )
        )
    finally:
        server.shutdown()
        conn.close()

    # --- 3: fail-closed CRITICAL — every transport 503 -> raise + audit + metric.
    reject = HTTPServer(("127.0.0.1", 0), _Reject)
    reject_port = reject.server_address[1]
    reject_thread = threading.Thread(target=reject.serve_forever, daemon=True)
    reject_thread.start()
    conn2 = _make_conn()
    audit2 = SQLiteAuditService(conn2)
    metrics2 = SQLiteMetricsService(conn2)
    router2 = OnCallRouter(
        [HttpOnCallTransport(f"http://127.0.0.1:{reject_port}/oncall", max_retries=1)],
        audit=audit2,
        metrics=metrics2,
    )
    try:
        raised = False
        try:
            router2.route(NotificationLevel.CRITICAL, "unclean death", "previous process killed")
        except OnCallDeliveryError:
            raised = True
        audit_after2 = {e.action for e in audit2.get_entries()}
        failed_recorded = "oncall.delivery_failed" in audit_after2
        metric_failed = metrics2.get_counter("oncall.delivery_failed") >= 1.0
        results.append(
            (
                "fail_closed_critical",
                raised and failed_recorded and metric_failed,
                (
                    f"CRITICAL raised={raised} audited={failed_recorded} "
                    f"metric={metric_failed} — no silent drop"
                ),
            )
        )
    finally:
        reject.shutdown()
        conn2.close()

    # --- 4: WARNING with unreachable transport does not raise.
    router3 = OnCallRouter(
        [HttpOnCallTransport("http://127.0.0.1:9/oncall", max_retries=1)],
    )
    try:
        low_ok = router3.route(NotificationLevel.WARNING, "late heartbeat", "below threshold")
        results.append(
            (
                "low_severity_never_raises",
                low_ok is True,
                "WARNING below threshold returned True (stays local, not a failure)",
            )
        )
    except OnCallDeliveryError:
        results.append(("low_severity_never_raises", False, "WARNING raised — severity bug"))

    passed = sum(1 for _, ok, _ in results if ok)
    verdict = "PASS" if passed == len(results) else "FAIL"
    for name, ok, detail in results:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    lines.append("")
    lines.append(f"VERDICT: {verdict} — {passed}/{len(results)} on-call rails proven")
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
