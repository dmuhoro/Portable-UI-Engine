#!/usr/bin/env python3
"""Pinned subprocess benchmark for session analytics with per-sample host load."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import time
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
MARKET_ID = UUID("00000000-0000-0000-0000-000000000001")
SESSIONS = {"Asia": [0, 8], "London": [8, 16], "New York": [16, 0]}


def _system_cpu() -> tuple[int, int, int]:
    """Return aggregate total/idle ticks and the number of logical CPUs."""
    lines = Path("/proc/stat").read_text().splitlines()
    aggregate = list(map(int, lines[0].split()[1:]))
    total = sum(aggregate[:8])
    idle = aggregate[3] + aggregate[4]
    cpu_count = sum(line.startswith("cpu") and line[3:4].isdigit() for line in lines)
    return total, idle, cpu_count


def _host_snapshot() -> dict[str, Any]:
    load = os.getloadavg()[0]
    return {
        "load_average_1m": round(load, 3),
        "cpu_affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else [],
    }


def _build_candles(count: int):
    from traderos.domain.entities import OHLCV
    from traderos.domain.entities import Candle
    from traderos.domain.entities import Timeframe

    start = datetime(2015, 1, 1, tzinfo=UTC)
    candles = []
    for index in range(count):
        close = Decimal(100_000 + index % 10_000) / Decimal(1_000)
        candles.append(
            Candle(
                market_id=MARKET_ID,
                ohlcv=OHLCV(
                    open=close,
                    high=close + Decimal("0.1"),
                    low=close - Decimal("0.1"),
                    close=close,
                    volume=Decimal(1),
                ),
                timestamp=start + timedelta(hours=index),
                timeframe=Timeframe.HOUR_1,
                source="benchmark",
            )
        )
    return candles


def _one_sample(candles) -> dict[str, Any]:
    from traderos.domain.services.session_analysis import SessionAnalysisService

    cpu_before, idle_before, cpu_count = _system_cpu()
    host_before = _host_snapshot()
    process_before = time.process_time()
    wall_before = time.perf_counter()
    result = SessionAnalysisService.compute_session_stats(candles, SESSIONS)
    elapsed = time.perf_counter() - wall_before
    process_cpu = time.process_time() - process_before
    cpu_after, idle_after, _ = _system_cpu()
    host_after = _host_snapshot()

    total_ticks = cpu_after - cpu_before
    idle_ticks = idle_after - idle_before
    busy_percent = 100.0 * (total_ticks - idle_ticks) / total_ticks if total_ticks > 0 else None
    busy_cores = (total_ticks - idle_ticks) / total_ticks * cpu_count if total_ticks > 0 else None
    other_cores = max(0.0, busy_cores - process_cpu / elapsed) if busy_cores is not None else None
    load_average = max(host_before["load_average_1m"], host_after["load_average_1m"])
    affinity = host_before["cpu_affinity"]
    contended = other_cores is None or other_cores > 0.5 or load_average > cpu_count
    return {
        "seconds": elapsed,
        "result_groups": len(result),
        "host_load": {
            "cpu_busy_percent": round(busy_percent, 2) if busy_percent is not None else None,
            "estimated_other_cpu_core_equivalents": (
                round(other_cores, 3) if other_cores is not None else None
            ),
            "load_average_1m": load_average,
            "cpu_affinity": affinity,
            "contended": contended,
        },
    }


def _worker(iterations: int, candle_count: int, cpu: int) -> int:
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, {cpu})
    candles = _build_candles(candle_count)
    for _ in range(3):
        _one_sample(candles)
    samples = [_one_sample(candles) for _ in range(iterations)]
    print(json.dumps({"samples": samples, "candles": candle_count}, separators=(",", ":")))
    return 0


def _percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(p * len(ordered)))
    return ordered[rank - 1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--candles", type=int, default=50_000)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--cpu", type=int, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.iterations < 20 or args.candles < 3:
        parser.error("use at least 20 iterations and 3 candles")
    if args.worker:
        allowed = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else [0]
        cpu = args.cpu if args.cpu is not None else allowed[0]
        return _worker(args.iterations, args.candles, cpu)

    allowed = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else [0]
    cpu = allowed[0]
    env = dict(os.environ)
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = os.pathsep.join(
        [src_path, env["PYTHONPATH"]] if env.get("PYTHONPATH") else [src_path]
    )
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--iterations",
        str(args.iterations),
        "--candles",
        str(args.candles),
        "--cpu",
        str(cpu),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, env=env, capture_output=True, text=True, check=False
    )
    if completed.returncode:
        print(completed.stderr, file=sys.stderr, end="")
        return completed.returncode
    raw = json.loads(completed.stdout)
    samples = raw["samples"]
    elapsed = [sample["seconds"] for sample in samples]
    contended = any(sample["host_load"]["contended"] for sample in samples)
    host = {
        "cpu_affinity": [cpu],
        "contended": contended,
        "max_cpu_busy_percent": max(
            sample["host_load"]["cpu_busy_percent"] or 0 for sample in samples
        ),
        "max_estimated_other_cpu_core_equivalents": max(
            sample["host_load"]["estimated_other_cpu_core_equivalents"] or 0 for sample in samples
        ),
        "max_load_average_1m": max(sample["host_load"]["load_average_1m"] for sample in samples),
    }
    report = {
        "iterations": args.iterations,
        "candles": args.candles,
        "cpu_pinned": cpu,
        "p50": {"seconds": statistics.median(elapsed), "host_load": host},
        "p95": {"seconds": _percentile(elapsed, 0.95), "host_load": host},
        "minimum_seconds": min(elapsed),
        "maximum_seconds": max(elapsed),
        "minimum": {"seconds": min(elapsed), "host_load": host},
        "maximum": {"seconds": max(elapsed), "host_load": host},
        "contended": contended,
        "samples": samples,
    }
    if args.json:
        print(json.dumps(report, separators=(",", ":")))
    else:
        print(f"iterations={args.iterations} candles={args.candles} cpu_pinned={cpu}")
        print(
            f"p50_seconds={report['p50']['seconds']:.6f} "
            f"host_load={json.dumps(host, sort_keys=True)}"
        )  # pyright: ignore[reportIndexIssue]
        print(
            f"p95_seconds={report['p95']['seconds']:.6f} "
            f"host_load={json.dumps(host, sort_keys=True)}"
        )  # pyright: ignore[reportIndexIssue]
        print(
            f"min_seconds={report['minimum_seconds']:.6f} "
            f"max_seconds={report['maximum_seconds']:.6f} "
            f"host_load={json.dumps(host, sort_keys=True)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
