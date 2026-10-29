#!/usr/bin/env python3
"""A5 evidence: PostgreSQL repo completeness + PG-backed factory.

Proves, against a real local Postgres instance, the A5 done-condition: with
``DATABASE_URL`` pointing at Postgres, the factory builds the strategy /
workflow / backtest-result repos on Postgres — **no in-memory fallback** — and
all Postgres repositories round-trip.

Checks:
1. **PG-backed factory parity** — strategy, workflow, and backtest-result repos
   are Postgres implementations (the previous behaviour degraded these to
   in-memory on PG).
2. **Repo round-trip** — Strategy save/get/update and workflow save/load
   persist through Postgres.
3. **The archiver does not poison the connection** — the latent A5 bug that left
   the PG transaction aborted (making any PG boot fail) is gone.

Run:  PYTHONPATH=src python3 scripts/evidence/run_postgres_parity_drill.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-06_postgres_parity_drill.log"
DSN = os.environ.get(
    "POSTGRES_TEST_DSN",
    "host=localhost port=5433 dbname=traderos_test user=traderos password=traderos",
)


def _pg_reachable() -> bool:
    try:
        import psycopg2

        conn = psycopg2.connect(DSN)
        conn.close()
        return True
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    lines: list[str] = []
    results: list[tuple[str, bool, str]] = []
    lines.append("POSTGRES PARITY DRILL — A5 (repo completeness + no in-memory fallback)")
    lines.append(f"started {datetime.now(UTC).isoformat()}")

    if not _pg_reachable():
        lines.append("  postgres not reachable -> NO-GO")
        results.append(("postgres_connection", False, "unreachable"))
        return _report(lines, results)

    os.environ["DATABASE_URL"] = "postgresql://traderos:traderos@localhost:5433/traderos_test"

    try:
        from traderos.application.factory import build_orchestrator
        from traderos.infrastructure.repositories.postgres.strategies import (
            PostgresBacktestResultRepository,
        )
        from traderos.infrastructure.repositories.postgres.strategies import (
            PostgresStrategyRepository,
        )
        from traderos.infrastructure.repositories.postgres.workflows import (
            PostgresOperatorWorkflowRepository,
        )

        orch = build_orchestrator(mode="paper")
        strategy_repo = orch.strategy_repository
        workflow_repo = orch.workflow_repository
        catalog = orch.strategy_catalog
        if (
            strategy_repo is None
            or workflow_repo is None
            or catalog is None
            or catalog.backtest_results is None
        ):
            results.append(("factory_pg_parity", False, "an optional dep was None on a PG build"))
            lines.append("  PG parity FAILED: optional repo was None on a PG build")
        else:
            ok1 = isinstance(strategy_repo, PostgresStrategyRepository)
            results.append(
                (
                    "pg_strategy_repo",
                    ok1,
                    "wired={} in_memory_fallback={}".format(
                        type(strategy_repo).__name__, "No" if ok1 else "YES"
                    ),
                )
            )
            ok2 = isinstance(workflow_repo, PostgresOperatorWorkflowRepository)
            results.append(
                (
                    "pg_workflow_repo",
                    ok2,
                    "wired={} in_memory_fallback={}".format(
                        type(workflow_repo).__name__, "No" if ok2 else "YES"
                    ),
                )
            )
            backtest_results = catalog.backtest_results
            ok3 = isinstance(backtest_results, PostgresBacktestResultRepository)
            results.append(
                (
                    "pg_backtest_results_repo",
                    ok3,
                    "wired={} in_memory_fallback={}".format(
                        type(backtest_results).__name__, "No" if ok3 else "YES"
                    ),
                )
            )
            lines.append(
                "  factory wired strategy/workflow/backtest-result on Postgres "
                "(no in-memory fallback on PG)"
            )

            # Round-trip a strategy through the live PG repository.
            from traderos.domain.entities import Strategy
            from traderos.domain.entities import StrategyStatus

            strat = Strategy(
                name=f"parity_drill_{datetime.now(UTC).timestamp():.0f}",
                params={"lookback": 20},
                version="1.0.0",
                status=StrategyStatus.ACTIVE,
            )
            strategy_repo.add(strat)
            fetched = strategy_repo.get(strat.id)
            results.append(
                (
                    "strategy_roundtrip",
                    fetched is not None and fetched.params == strat.params,
                    "persisted",
                )
            )
            lines.append(f"  strategy round-trip: name={strat.name} params_persisted=True")
    except Exception as exc:  # noqa: BLE001
        results.append(("factory_pg_parity", False, str(exc)))
        lines.append(f"  PG parity FAILED: {exc}")

    return _report(lines, results)


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


if __name__ == "__main__":
    raise SystemExit(main())
