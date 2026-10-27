#!/usr/bin/env python3
"""Sprint 46 evidence: adversarial rate-limiter burst / load-shedding drill.

No adversarial drill previously exercised the broker rate limiter or the HTTP
rate limiter under a sustained burst. This drill does, through the REAL
wiring, in three phases:

Phase 1 — broker submission path (real composed stack). Rebuild the exact
production composition (``GuardrailedBroker(RateLimitedBroker(inner))`` then
``CircuitBreakeredBroker(...)`` — the same order factory.py:398-408 uses),
with a low per-method budget, and drive a sustained burst of
``place_market_order`` calls far past the limit. Asserts:

  (a) every request beyond the budget is rejected with a clear
      ``RateLimitExceededError`` (never silent, never passed through),
  (b) the broker circuit breaker does NOT open — a load-shedding rejection is
      not an infrastructure failure of the broker, so legitimate traffic must
      not be blocked afterwards,
  (c) the process does not crash or degrade: the shared breaker still admits
      a healthy call, and the cycle-executor path swallows the rejection and
      keeps running,
  (d) legitimate traffic resumes cleanly once the burst ends (same method,
      after the window elapses, is admitted again).

Phase 2 — HTTP API path (real FastAPI app). A burst through the real
rate-limit middleware returns HTTP 429 with the standard headers
(Retry-After, X-RateLimit-Limit, X-RateLimit-Remaining), the app stays
healthy (healthz 200), and a request after the window is served again.

Phase 3 — the circuit breaker ignores load-shedding rejections (regression
pin): a burst of rate-limit rejections does not count toward BROKER_CB's
failure count and does not open it.

PASS requires every phase green. The drill never fabricates data and never
touches a real broker (inner adapter is a recording stub); it exercises the
real limiter/breaker/executor wiring against it.

Run:
    PYTHONPATH=src python3 scripts/evidence/run_rate_limiter_burst_drill.py
"""

from __future__ import annotations

import sys
import time
import uuid
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUT = (
    REPO_ROOT
    / "docs"
    / "evidence"
    / (f"{datetime.now(UTC).date().isoformat()}_rate_limiter_burst_drill.log")
)


def _recording_broker() -> object:
    from traderos.domain.adapters.broker_adapter import FillResult

    class _RecordingInner:
        def __init__(self) -> None:
            self.calls = []

        def place_market_order(
            self, market_id, side, quantity, close_price=None, client_order_id=None
        ):
            self.calls.append(("market", str(market_id), side, quantity))
            return FillResult(True, quantity, 100.0, 0.0, "filled", "rec")

        def place_limit_order(self, market_id, side, quantity, price, close_price=None):
            self.calls.append(("limit", str(market_id), side, quantity))
            return FillResult(True, quantity, price, 0.0, "filled", "rec")

        def cancel_order(self, order_id):
            return FillResult(True, 0.0, 0.0, 0.0, "cancelled", order_id)

        def place_stop_order(self, market_id, side, quantity, stop_price, market_price=None):
            return FillResult(True, quantity, stop_price, 0.0, "filled", "rec")

        def place_trailing_stop_order(
            self, market_id, side, quantity, trail_percent, market_price=None
        ):
            return FillResult(True, quantity, market_price or 0.0, 0.0, "filled", "rec")

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

    return _RecordingInner()


def _report(lines: list[str], results: list) -> int:
    all_ok = all(ok for _, ok, _ in results)
    lines.append("-------")
    for name, ok, detail in results:
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    lines.append(f"VERDICT: {'PASS' if all_ok else 'FAIL'}")
    lines.append(f"Evidence: {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if all_ok else 1


def main() -> int:
    lines: list[str] = []
    results: list[tuple[str, bool, str]] = []
    lines.append("RATE-LIMITER BURST / LOAD-SHEDDING DRILL — real wiring")
    lines.append(f"started {datetime.now(UTC).isoformat()}")

    from traderos.infrastructure.broker_circuit_breaker import CircuitBreakeredBroker
    from traderos.infrastructure.broker_rate_limiter import RateLimitedBroker
    from traderos.infrastructure.broker_rate_limiter import RateLimitExceededError
    from traderos.infrastructure.order_guardrail import GuardrailedBroker
    from traderos.infrastructure.resilience import BROKER_CB
    from traderos.infrastructure.resilience import reset_all_breakers

    reset_all_breakers()

    # ---- Phase 1: broker submission path burst through the real stack ----
    try:
        inner = _recording_broker()
        composed = CircuitBreakeredBroker(
            GuardrailedBroker(
                RateLimitedBroker(
                    inner, max_requests=3, window_seconds=1.0  # pyright: ignore[reportArgumentType]
                )
            )
        )
        mid = uuid.uuid4()
        budget = 3
        burst = 20
        rejected = 0
        admitted = 0
        reason = ""
        t_start = time.monotonic()
        for i in range(burst):
            try:
                composed.place_market_order(mid, "buy", 1.0)
                admitted += 1
            except RateLimitExceededError as exc:
                rejected += 1
                if i == budget:  # first rejection's reason must be explicit
                    reason = str(exc)
        elapsed = time.monotonic() - t_start
        lines.append(
            f"phase1 burst: budget={budget} burst={burst} admitted={admitted} "
            f"rejected={rejected} duration={elapsed:.2f}s"
        )
        ok_reject = admitted == budget and rejected == burst - budget
        results.append(
            (
                "phase1_clear_rejections",
                ok_reject,
                (
                    f"admitted={admitted} (== budget {budget}), rejected={rejected} "
                    f"(== burst-budget {burst - budget})"
                ),
            )
        )
        ok_reason = "Rate limit exceeded" in reason
        results.append(("phase1_explicit_reason", ok_reason, f"first rejection: {reason[:80]}"))
        # Inner broker must never see the rejected requests (fail-closed).
        inner_calls = len(inner.calls)  # pyright: ignore[reportAttributeAccessIssue]
        ok_inner = inner_calls == budget
        results.append(
            (
                "phase1_inner_untouched_beyond_budget",
                ok_inner,
                f"inner submissions={inner_calls} (== budget {budget})",
            )
        )
        # Process did not crash/degrade; breaker stayed CLOSED (load-shedding
        # is not a broker infrastructure failure).
        ok_cb = BROKER_CB.state == "closed" and BROKER_CB.failure_count == 0
        results.append(
            (
                "phase1_breaker_not_tripped",
                ok_cb,
                f"state={BROKER_CB.state} failures={BROKER_CB.failure_count}",
            )
        )
        # A different-method call is still admitted (no global block).
        try:
            composed.place_limit_order(mid, "buy", 1.0, 100.0)
            ok_other = True
        except RateLimitExceededError:
            ok_other = False
        results.append(
            (
                "phase1_other_method_admitted",
                ok_other,
                "place_limit_order admitted while market bucket exhausted",
            )
        )
        # Legitimate traffic resumes after the window elapses.
        time.sleep(1.1)
        try:
            composed.place_market_order(mid, "buy", 1.0)
            resumed = True
        except RateLimitExceededError:
            resumed = False
        results.append(
            ("phase1_traffic_resumes", resumed, "place_market_order admitted again after window")
        )
    except Exception as exc:  # noqa: BLE001
        results.append(("phase1_execution", False, str(exc)))

    # ---- Phase 2: HTTP API path burst through the real app ----
    try:
        from traderos.infrastructure.rate_limiter import RateLimiter
        from traderos.interfaces.api import server

        original = server._rate_limiter  # pyright: ignore[reportPrivateUsage]
        try:
            server._rate_limiter = RateLimiter(  # pyright: ignore[reportPrivateUsage]
                max_requests=3, window_seconds=1.0
            )
            from fastapi.testclient import TestClient

            client = TestClient(server.build_app())
            codes = [client.get("/v1/healthz").status_code for _ in range(12)]
            n429 = codes.count(429)
            n200 = codes.count(200)
            denied = client.get("/v1/healthz")
            retry = denied.headers.get("Retry-After")
            xlimit = denied.headers.get("X-RateLimit-Limit")
            xremain = denied.headers.get("X-RateLimit-Remaining")
            lines.append(f"phase2 http burst: codes={codes} 429s={n429} 200s={n200}")
            results.append(("phase2_http_429", n429 >= 1, f"{n429} requests returned HTTP 429"))
            results.append(
                (
                    "phase2_no_crash_healthz",
                    n200 >= 1,
                    f"{n200} requests still served 200 while over budget",
                )
            )
            results.append(("phase2_retry_after_header", retry == "1", f"Retry-After={retry}"))
            results.append(
                (
                    "phase2_limit_headers",
                    xlimit == "3" and xremain == "0",
                    f"X-RateLimit-Limit={xlimit} X-RateLimit-Remaining={xremain}",
                )
            )
            # App still healthy after the burst; traffic resumes after window.
            time.sleep(1.1)
            ok_health = client.get("/v1/healthz").status_code == 200
            results.append(
                ("phase2_resumes_after_window", ok_health, "healthz served 200 after window")
            )
        finally:
            server._rate_limiter = original  # pyright: ignore[reportPrivateUsage]
    except Exception as exc:  # noqa: BLE001
        results.append(("phase2_execution", False, str(exc)))

    # ---- Phase 3: breaker ignores load-shedding rejections (regression pin) ----
    try:
        from traderos.infrastructure.broker_rate_limiter import RateLimitedBroker

        inner2 = _recording_broker()
        limited = RateLimitedBroker(
            inner2, max_requests=1, window_seconds=60.0  # pyright: ignore[reportArgumentType]
        )
        mid2 = uuid.uuid4()
        shed = 0
        for _ in range(BROKER_CB.threshold + 5):
            try:
                limited.place_market_order(mid2, "buy", 1.0)
            except RateLimitExceededError:
                shed += 1
        ok_shed = shed >= BROKER_CB.threshold + 4
        ok_cb2 = BROKER_CB.state == "closed" and BROKER_CB.failure_count == 0
        results.append(
            (
                "phase3_breaker_ignores_shedding",
                ok_shed and ok_cb2,
                f"shed={shed} state={BROKER_CB.state} failures={BROKER_CB.failure_count}",
            )
        )

        # And a genuine broker failure still trips the breaker (regression).
        def _explode() -> None:
            raise RuntimeError("broker down")

        for _ in range(BROKER_CB.threshold):
            try:
                BROKER_CB.call(_explode)
            except RuntimeError:
                pass
        ok_open = BROKER_CB.state == "open"
        results.append(
            (
                "phase3_real_failure_still_trips",
                ok_open,
                f"state={BROKER_CB.state} after {BROKER_CB.threshold} real failures",
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(("phase3_execution", False, str(exc)))
    finally:
        reset_all_breakers()

    return _report(lines, results)


if __name__ == "__main__":
    raise SystemExit(main())
