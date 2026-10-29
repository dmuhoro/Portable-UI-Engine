# Sprint 32 — Production risk-rail config (WP11), kill-surface surfacing (WP11b), regulator attribution view (WP12), CI evidence-drill job (WP13)

This sprint closes the G-03 "config + operational surface" gap and the G-05
"UI surfacing" gap, and turns the G-06 evidence drills into a CI gate — all
without touching the account-gated WP5–WP7 path (still operator-run per
`LIVE_RUN_POLICY.md`).

- **WP11 (G-03):** the per-order risk rails that already gate the real
  submission seam are now configured from `settings.yaml` / `RISK_*` env
  overrides and **enforced at boot**: LIVE refuses to arm unless every
  production rail (daily-loss, gross-exposure, position size, max positions,
  allowlist) is explicitly configured and sane. The same validation is a
  fail-closed check in the live gate.
- **WP11b (G-03):** the kill switch is an audited, metered, deliberate surface —
  engage/disengage record `risk.kill_switch_*` on the durable audit trail and
  move metrics counters, and the dashboard demands explicit confirmation
  before tripping or re-arming.
- **WP12 (G-05):** causal attribution is surfaced to the operator dashboard as
  a read-only regulator view (`/v1/attribution/replay` window), rendering the
  signal → decision → order → fill chain with per-fill realized PnL.
- **WP13 (G-06):** the 15 credential-free evidence drills run as a dedicated
  CI job; the runner fails the build if ANY drill regresses.

## Ground truth (verified, not assumed)

- The real submission seam is `CycleExecutor` — `self._broker.place_market_order(...)`
  at `cycle_executor.py:384` / `:577`, gated by
  `self._risk_service.authorize_order(...)` at `:343` / `:521`. WP11 configures
  that existing gate; it does not add a parallel one.
- The factory previously wired only `max_gross_exposure`,
  `max_data_staleness_seconds`, `allowed_markets`, `per_users`,
  `require_allowlist` into `RiskService`; `daily_loss_pct`, `max_position_size`
  and `max_positions_total` were silently defaulted. WP11 resolves all rails
  through one validated source (`risk_config.resolve_risk_rails`).
- The kill switch (`/v1/kill-switch/engage|disengage`) already published
  notifications + events but wrote **no** audit record and **no** metric; the
  dashboard called engage with no confirmation. WP11b closes both gaps.
- The attribution replay endpoint (`/v1/attribution/replay`, built in Sprint 27)
  existed but had no UI. WP12 renders it from the real `ReplayService`.
- The 15 credential-free drills all passed in ≤3s with rc=0 locally; the 8
  key-gated drills (live credentials / managed Vault / Postgres / public-market
  network) are kept out of the deterministic CI drill job — credential-gated
  ones are operator-run, and the network-gated ones are exercised by the normal
  test suite when the external feed is reachable.

## Work Completed

### WP11 — production risk-rail config (G-03)
- New `src/traderos/application/risk_config.py`:
  - `RiskRailSettings` dataclass + `resolve_risk_rails(risk_section, *, live)`
    — every numeric rail range-checked (daily-loss/position-size `(0,1]`,
    gross-exposure `(0,10]`, staleness `(0,86400]`, max-positions int `[1,1000]`),
    invalid values raise `ConfigError` (never coerced).
  - Env overrides win over yaml: `RISK_DAILY_LOSS_PCT`, `RISK_MAX_GROSS_EXPOSURE`,
    `RISK_MAX_POSITION_SIZE`, `RISK_MAX_POSITIONS_TOTAL`,
    `RISK_MAX_DATA_STALENESS_SECONDS`, `RISK_ALLOWED_MARKETS` (comma-separated),
    `RISK_REQUIRE_ALLOWLIST`.
  - LIVE is fail-closed by construction: all four production rails must be
    **explicitly** set, `require_allowlist=true`, and a non-empty
    `allowed_markets`. Missing/invalid → `ConfigError` at boot, never a
    permissive default.
  - `validate_production_risk_settings(risk_section) -> list[str]` never raises
    — used by the live gate to report and block.
- `factory.py`: resolves rails through `resolve_risk_rails(...)` and arms the
  real `RiskService` (`factory.py:190-202`). `_resolve_allowed_markets` now
  takes pre-resolved symbols.
- `scripts/governance/live_gate.py`: new check #5 "production risk rails
  configured (WP11)" runs the same validator on the gate's settings.
- `configs/settings.yaml`: documented `risk:` block (conservative paper values
  + comments on the LIVE requirements).
- Tests: `tests/test_production_risk_config.py` (25) — paper defaults,
  env-overrides, live fail-closed, and **factory wiring that proves the real
  `authorize_order` gate is armed**: a `daily_loss_pct=0.01` with a −10
  realized loss on 1000 equity blocks submission. `test_live_gate_governance.py`
  extended (gate passes with complete rails; `risk: {}` → gate returns 1).
  `run_governance_drill.py` updated to supply rails in its PASS scenario.

### WP11b — kill-switch kill surface (G-03)
- `interfaces/api/operator.py`: engage/disengage now write
  `risk.kill_switch_engaged` / `risk.kill_switch_disengaged` to the durable
  audit trail and bump `kill_switch.engaged` / `kill_switch.disengaged`
  counters on the metrics port.
- Dashboard `app.js`: both `ks-engage` and `ks-disengage` are wrapped in an
  explicit `window.confirm` ("ENGAGE KILL SWITCH?" / "DISENGAGE KILL SWITCH?").
- Tests: `test_operator_api.py::test_transitions_are_audited_and_counted`
  (asserts via `orch.audit.find(action=...)` + metrics counters) and
  `test_dashboard.py::test_kill_switch_requires_explicit_confirmation`.

### WP12 — regulator attribution view (G-05)
- `index.html`: "Causal attribution (regulator view)" panel — date window
  inputs, replay button, metrics line, and a table (signal at / strategy /
  market / dir / conf / blocked / complete / order / realized PnL).
- `app.js`: `loadAttribution()` + `renderAttribution()` hitting
  `/v1/attribution/replay?start=..&end=..` (UTC window), rendering
  chains with steps in the row title; wired to the button, window defaults to
  today.
- Tests: `test_dashboard.py` — panel surface, `attr-load` wiring, window
  defaults, and the render keys the API returns.

### WP13 — CI evidence-drill job (G-06)
- New `scripts/evidence/run_ci_drills.py`: runs the 15 credential-free drills
  as subprocesses (PYTHONPATH `src:tests`, per-drill timeout, exit code from
  each drill's `main()`), aggregates verdicts, writes a date-aware evidence
  log, and exits non-zero if ANY drill fails. `--only`, `--list`,
  `--no-evidence` flags for local runs. `KEY_GATED` documents the 8 drills
  kept out of the deterministic CI drill job (live credentials / managed
  Vault / Postgres / public-market network) — asserted in tests so one can
  never silently join the drill job.
- `.github/workflows/ci.yml`: new `evidence-drills` job runs the suite on every
  push/PR and uploads the evidence log as an artifact.
- `run_secret_lifecycle_drill.py` extended: LIVE boot without risk rails now
  proves the WP11 fail-closed layer (a consequence of WP11 — the drill had to
  supply rails to reach the A6 credential check it originally proved).
- Tests: `tests/test_ci_drills_runner.py` (13) — inventory exists / expected
  set / key-gated excluded / aggregation fail-closed / real subprocess
  exit-code + timeout handling / evidence log + `--list`.

## Belt-and-suspenders checks
- Subset runs green after each package (risk-config+gate 41, kill-surface
  operator+dashboard 32, dashboard+WP12 11, CI-drill runner 13, full final
  subset 89).
- Full suite run three times on the final state, each green: **1572 passed /
  82 skipped** (3/3 runs identical).
- `scripts/evidence/run_ci_drills.py` locally: **15/15 PASS** on the final
  state (aggregate log `docs/evidence/2026-08-10_ci_drills.log`).
- Static checks clean on all changed files: `ruff check`, `black --check`,
  `isort --check`; `pyright src/traderos/` 0 errors; dashboard `node --check`
  clean.

## Not done (honest)
- WP5's continuous 24–72h unattended paper-soak window remains an operator-run
  gate (bounded real-paper runs PASS; the full window is the operator's
  deliverable via `run_unattended_paper_soak.py`).
- WP7 live re-arm stays authority-gated: the named Operator (human) and the
  signed GO checklist — nothing here moves the NO-GO default.
- Live PagerDuty/Slack incident delivery still requires a managed on-call
  account with live credentials; managed Vault/KMS rotation cadence still
  requires a managed instance.
- WP11 configures and enforces the rails; an operator must still fill the LIVE
  `allowed_markets` with the actual pilot symbols at deployment time.
- Closing G-03/G-05/G-06 surface gaps does not close G-01/G-02 — the real-broker
  and real-market exit tests stay open.
