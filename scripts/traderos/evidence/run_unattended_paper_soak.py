#!/usr/bin/env python3
"""G-02 evidence: UNATTENDED real Alpaca paper-broker soak runner (24–72h).

The G-02 exit test is an *unattended paper-broker soak (Alpaca paper,
24–72h)*: 0 reconcile errors, 0 duplicate/lost orders across forced
disconnects, journal-recovery replays correctly.

This runner supervises that soak over a wall-clock window by repeatedly
invoking the verified real-path harness (``run_underlying_paper_soak`` works
on the same machine; see run_real_paper_soak.py / run_unattended_paper_soak.py)
in bounded batches. Each batch:

  - places ``--batch-cycles`` market orders through the real production chain
    (CycleExecutor -> JournaledBroker -> AlpacaBrokerAdapter -> real Alpaca
    paper endpoint),
  - writes its own dated evidence log (never overwriting a prior batch),
  - closes out its own residue (0 leaked orders; a user's are never touched),
  - reconcile must come back clean for the batch to count as PASS.

This wrapper appends one atomic row per batch to an aggregate evidence log,
and at the end of the window returns PASS only if every batch passed. It is
self-supervised: a crashed/absent batch is recorded as FAIL, never silently
dropped (AGENTS rule: no silent drops). It requires real paper credentials in
the environment and otherwise exits NO-GO (like the harness).

RESTART / RESUME (the 72h Railway soak). The window is checkpointed to
``docs/evidence/<label>_soak_state.json`` — on the persistent volume, so it
survives the container restart the supervisor performs on failure. A restart
CONTINUES the window from the checkpoint's accumulated elapsed time; it does not
start a fresh 72h clock. Without this, every restart reset the wall-clock
deadline and the soak could never complete: the service exhausted its retries
and went CRASHED with no verdict. A checkpoint whose geometry (window, batch
size, interval, label) differs is set aside as ``.superseded`` and a fresh
window begins, so two different experiments are never spliced into one verdict.
A window already marked ``completed`` is not re-run.

Run (env-only paper keys; unattended window in hours):
    ALPACA_API_KEY=... ALPACA_SECRET_KEY=... \
    PYTHONPATH=. python3 scripts/evidence/run_unattended_paper_soak.py \
        --hours 24 --batch-cycles 10 --interval-minutes 60

Verify a short window first:
    ... python3 scripts/evidence/run_unattended_paper_soak.py \
        --minutes 2 --batch-cycles 3 --interval-minutes 0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS = REPO_ROOT / "scripts" / "evidence" / "run_real_paper_soak.py"
sys.path.insert(0, str(REPO_ROOT / "src"))


def _aggregate_path() -> Path:
    label = os.getenv("SOAK_LOG_LABEL", "unattended_paper_soak")
    date = datetime.now(UTC).date().isoformat()
    return REPO_ROOT / "docs" / "evidence" / f"{date}_{label}_aggregate.log"


def _state_path() -> Path:
    """Durable checkpoint, on the same persistent volume as the evidence log.

    ``docs/evidence`` is the Railway volume mount (``railway.soak.toml``), so
    this survives the container restart that the supervisor performs on
    failure. It must NOT live next to the code: that layer is discarded.
    """
    label = os.getenv("SOAK_LOG_LABEL", "unattended_paper_soak")
    return REPO_ROOT / "docs" / "evidence" / f"{label}_soak_state.json"


# The batch geometry a resume must agree on. A checkpoint written by a
# different soak shape is not resumable — comparing it and silently continuing
# would splice two different experiments into one verdict.
_STATE_SCHEMA = 1


def _harness_digest() -> str:
    """SHA-256 over the two scripts that actually produce the verdict.

    A checkpoint must not be resumable across a change of harness either. The
    geometry guard above exists to stop two different *experiments* being
    spliced into one verdict, but it could not see the case that actually
    mattered in production: the fixed harness was redeployed over a checkpoint
    whose batches had been produced by the buggy one, so the window would have
    inherited two FAILED batches and could never return PASS — leaving the
    operator to either accept a permanently-red window or hand-edit the
    checkpoint by hand. Neither is honest.

    Digests of the files, not the git HEAD: the deployed container may not carry
    ``.git``, and "which revision is running" must be answerable from the volume
    alone. Including the supervisor's own source means any edit to the resume
    logic itself also supersedes.
    """
    digest = hashlib.sha256()
    for path in (Path(__file__), HARNESS):
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def _state_fingerprint(
    window_s: float, batch_cycles: int, interval_minutes: float, label: str
) -> dict[str, Any]:
    return {
        "schema": _STATE_SCHEMA,
        "label": label,
        "window_seconds": round(window_s, 3),
        "batch_cycles": batch_cycles,
        "interval_minutes": interval_minutes,
        "harness_digest": _harness_digest(),
    }


def _load_state(fingerprint: dict[str, Any]) -> dict[str, Any] | None:
    """Read the checkpoint, or ``None`` when there is nothing to resume.

    A checkpoint that does not match this run's geometry is NOT resumed. It is
    moved aside as ``.superseded`` rather than deleted or reused, so the
    previous run's numbers remain auditable while this run starts a clean
    window (no silent drop, no silent reuse).
    """
    path = _state_path()
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"checkpoint unreadable ({exc}); starting a fresh window", flush=True)
        path.replace(path.with_suffix(".json.corrupt"))
        return None

    mismatched = {k: (state.get(k), v) for k, v in fingerprint.items() if state.get(k) != v}
    if mismatched:
        superseded = path.with_suffix(".json.superseded")
        path.replace(superseded)
        print(
            f"checkpoint geometry differs {mismatched}; moved to {superseded.name} "
            "and starting a fresh window",
            flush=True,
        )
        return None
    return state


def _save_state(state: dict[str, Any]) -> None:
    """Atomically persist the checkpoint.

    Write-then-``os.replace`` is the only safe order: a SIGKILL mid-write leaves
    either the old checkpoint or the new one, never a truncated JSON file that
    would silently reset a 72h soak to zero.
    """
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _run_batch(batch: int, batch_cycles: int, label: str) -> tuple[bool, str]:
    env = dict(os.environ)
    env["SOAK_LOG_LABEL"] = f"{label}_batch{batch:04d}"
    env["SOAK_LATENCY_PROBES"] = os.getenv("SOAK_LATENCY_PROBES", "10")
    proc = subprocess.run(
        [sys.executable, str(HARNESS), str(batch_cycles)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=int(os.getenv("SOAK_BATCH_TIMEOUT", "600")),
        check=False,
    )
    combined = (proc.stdout + "\n" + proc.stderr).strip()
    tail = "\n".join(combined.splitlines()[-6:])
    passed = proc.returncode == 0 and "VERDICT: PASS" in proc.stdout
    if not passed:
        tail = "\n".join(combined.splitlines()[-12:])
    return passed, tail


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else "unattended paper soak runner"
    )
    parser.add_argument("--hours", type=float, default=0.0, help="wall-clock window (hours)")
    parser.add_argument("--minutes", type=float, default=0.0, help="wall-clock window (minutes)")
    parser.add_argument(
        "--seconds", type=float, default=0.0, help="wall-clock window (seconds, for drills)"
    )
    parser.add_argument("--batch-cycles", type=int, default=5, help="cycles per batch")
    parser.add_argument("--interval-minutes", type=float, default=60.0, help="time between batches")
    args = parser.parse_args(argv)

    window_s = (args.hours * 3600.0) + (args.minutes * 60.0) + args.seconds
    if window_s <= 0:
        window_s = 86400.0  # default to a 24h window

    started = datetime.now(UTC)
    label = os.getenv("SOAK_LOG_LABEL", "unattended_paper_soak")
    out = _aggregate_path()
    out.parent.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("ALPACA_API_KEY", "")
    secret_key = os.getenv("ALPACA_SECRET_KEY", "")
    if not api_key or not secret_key:
        lines = [
            f"UNATTENDED REAL-PAPER SOAK RUNNER — started {started.isoformat()}",
            "FATAL: no ALPACA_API_KEY / ALPACA_SECRET_KEY (paper keys) in env.",
            "NO-GO: the unattended soak requires real Alpaca paper credentials;",
            "the runner refuses to fabricate broker truth without them.",
            "VERDICT: NO-GO (credentials absent) — runner ready, soak not run",
            f"Evidence: {out}",
        ]
        out.write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return 2

    fingerprint = _state_fingerprint(window_s, args.batch_cycles, args.interval_minutes, label)
    resumed = _load_state(fingerprint)

    # The window is measured from the FIRST run's start, carried across
    # restarts in the checkpoint. Previously it was `time.monotonic()` from
    # process start, so every Railway restart silently began a fresh 72h
    # window: the soak could never finish, and the CRASHED-after-3-retries
    # state looked like a finished run that produced no verdict.
    if resumed is None:
        elapsed_s = 0.0
        batches_passed = 0
        batches_failed = 0
        batch = 0
        restarts = 0
        first_started = started
        resume_note = "fresh window"
    else:
        elapsed_s = float(resumed.get("elapsed_seconds", 0.0))
        batches_passed = int(resumed.get("batches_passed", 0))
        batches_failed = int(resumed.get("batches_failed", 0))
        batch = int(resumed.get("batch", 0))
        restarts = int(resumed.get("restarts", 0)) + 1
        first_started = datetime.fromisoformat(str(resumed["started_at"]))
        resume_note = (
            f"RESUME run_started={started.isoformat()} "
            f"soak_started={first_started.isoformat()} "
            f"elapsed={elapsed_s:.0f}s/{window_s:.0f}s batch={batch} "
            f"passed={batches_passed} failed={batches_failed} restart#{restarts}"
        )

    lines = [
        "UNATTENDED REAL-PAPER SOAK RUNNER (real Alpaca paper)",
        (
            f"started {started.isoformat()}  window={window_s:.0f}s  "
            f"batch_cycles={args.batch_cycles}  interval={args.interval_minutes}m"
        ),
        "each batch = full real-path chain: CycleExecutor -> JournaledBroker ->",
        "AlpacaBrokerAdapter -> Alpaca paper; close-out + clean reconcile required.",
        resume_note,
    ]
    print("\n".join(lines))

    # A completed window is not re-run: the verdict is already decided and
    # recorded. Re-running would overwrite it with a second, unrelated soak.
    if resumed is not None and bool(resumed.get("completed")):
        summary = [
            "",
            f"already completed {resumed.get('finished_at')} — not re-running",
            f"VERDICT: {resumed.get('verdict')} (from completed checkpoint)",
            f"Evidence: {out}",
        ]
        print("\n".join(summary))
        return 0 if resumed.get("verdict") == "PASS" else 1

    run_started = time.monotonic()

    def elapsed() -> float:
        """Wall-clock consumed by the soak across ALL runs of this window."""
        return elapsed_s + (time.monotonic() - run_started)

    state: dict[str, Any] = {
        **fingerprint,
        "started_at": first_started.isoformat(),
        "elapsed_seconds": elapsed_s,
        "batch": batch,
        "batches_passed": batches_passed,
        "batches_failed": batches_failed,
        "completed": False,
        "verdict": None,
        "restarts": restarts,
    }
    _save_state(state)

    def checkpoint() -> None:
        state["elapsed_seconds"] = elapsed()
        state["batch"] = batch
        state["batches_passed"] = batches_passed
        state["batches_failed"] = batches_failed
        _save_state(state)

    while elapsed() < window_s:
        batch += 1
        ts = datetime.now(UTC).isoformat()
        try:
            ok, tail = _run_batch(batch, args.batch_cycles, label)
        except Exception as exc:  # noqa: BLE001 — supervise, never silently drop
            ok, tail = False, f"  batch crashed: {exc}"
        row = f"[{ts}] batch={batch:03d} {'PASS' if ok else 'FAIL'}\n" f"{tail}\n"
        with out.open("a", encoding="utf-8") as fh:
            fh.write(row)
            fh.flush()
            os.fsync(fh.fileno())
        print(row.rstrip(), flush=True)
        if ok:
            batches_passed += 1
        else:
            batches_failed += 1
        # Checkpoint AFTER the row is durably in the log, so a crash can never
        # claim a batch that the evidence file does not contain.
        checkpoint()
        wait = args.interval_minutes * 60.0
        if args.interval_minutes > 0:
            remaining = window_s - elapsed()
            if remaining > 0:
                # Sleep in slices, persisting as we go, so the supervisor can
                # stop the container without the checkpoint losing the elapsed
                # time it actually spent.
                slept = 0.0
                while slept < min(wait, remaining):
                    time.sleep(min(5.0, min(wait, remaining) - slept))
                    slept += 5.0
                    checkpoint()

    finished = datetime.now(UTC)
    all_pass = batches_failed == 0 and batches_passed > 0
    verdict = "PASS" if all_pass else "FAIL"
    summary = [
        "",
        f"finished {finished.isoformat()}",
        f"batches_run={batch} passed={batches_passed} failed={batches_failed}",
        f"window_seconds={elapsed():.0f} (target {window_s:.0f})",
        f"soak_started={first_started.isoformat()} across {restarts + 1} run(s)",
        f"VERDICT: {verdict} (0 reconcile/dup/lost across all batches)",
        f"Evidence: {out}",
    ]
    with out.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(summary) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    print("\n".join(summary))

    state["elapsed_seconds"] = elapsed()
    state["batch"] = batch
    state["batches_passed"] = batches_passed
    state["batches_failed"] = batches_failed
    state["completed"] = True
    state["verdict"] = verdict
    state["finished_at"] = finished.isoformat()
    _save_state(state)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
