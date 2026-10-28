# Analytics Performance Targets

This file is the single source of truth for analytics performance budgets.

## Session analysis

- `workload`: `SessionAnalysisService.compute_session_stats`
- `candles`: `50000`
- `iterations`: `100`
- `warmups`: `3` measured samples are discarded before the 100 recorded samples
- `p95_budget_seconds`: `1.0`
- `contention_policy`: a contended measurement fails the performance test with
  the sampled host load attached; it is never silently skipped or presented as
  a quiet-host result

The one-second budget is retained as a provisional ceiling. A quiet-host run is
required before tightening or replacing it. On 2026-10-04, 100 pinned samples
on the available host measured p50 `0.160256s` and p95 `0.194462s`, but the run
was contended (`54.22%` maximum aggregate CPU busy, `3.346` estimated other CPU
core equivalents, 1-minute load average `1.818`). Those numbers demonstrate
that the runner reports contention; they are not accepted as the quiet baseline
and do not justify changing the budget. It is an inference that a quiet run
would be no slower than this contended run; that inference is not used to change
the budget.

Run the measurement with:

```sh
PYTHONPATH=src python3 scripts/benchmark_analytics.py --iterations 100 --candles 50000
```

The benchmark runs the measured workload in a child process pinned to one
available CPU. Every sample carries CPU busy percentage, estimated competing
CPU core equivalents, 1-minute host load, affinity, and a contention verdict.
