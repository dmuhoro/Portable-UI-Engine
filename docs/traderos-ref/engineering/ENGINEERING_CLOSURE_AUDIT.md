# TraderOS — Engineering Closure Audit

**Status:** LIVE RELEASE DASHBOARD
**Date:** 2026-08-02
**Auditor role:** Release Engineering Lead (Engineering Closure pass)
**Frame:** every figure below was measured directly from the repository, the running toolchain, and the live test suite — none are aspirational.

> Permanent release dashboard. Regenerated at every closure checkpoint. Supersedes any prior "N/A" or "matches code" placeholder.

---

## 1. Repository Health

Measured 2026-08-02 against `HEAD`.

| Metric | Value | Evidence |
|---|---:|---|
| Current commit | `e1a936b` | `git rev-parse HEAD` |
| Current branch | `main` | `git branch --show-current` |
| Total source files | **154** | `find src -name '*.py'` |
| Source LOC | 16,592 | `wc -l` over `src` |
| Total test files | **91** | `find tests -name '*.py'` |
| Test LOC | 15,164 | `wc -l` over `tests` |
| Total tests | **1266** | `pytest -q` — **1266 passed** |
| Coverage | **93.62%** | `pytest` (fail_under = 70) |
| Ruff | **0 errors** | `ruff check .` |
| Black / isort | **clean** | `black --check .`, `isort --check .` |
| Pyright (strict) | **0 errors** | `pyright src/traderos` |
| Security (pip-audit) | **0 known vulnerabilities** | audit of pinned deps |
| Security (bandit) | **0 High** | `bandit -r src/traderos -lll`; 32 Medium = known B608 f-string-SQL false positives (column/table-name interpolation, not user input) |
| Docker | Ready | `Dockerfile` + `docker-compose.yml` (api + daemon + postgres + test-pg) |
| CI | Green | `.github/workflows/ci.yml`: version-check, lint, typecheck, test, security, docker |
| Open PRs | 0 | `git status` / remote |
| Release status | **Pre-Code-Freeze closure** | see §8 |

**Closure deltas this pass:**
- `/metrics` returned **501** because `prometheus-client` was absent from the runtime; installed → `/metrics` returns **200**. The Metrics invariant had been documented "PROVEN" while broken.
- 1 failing test (`test_health_and_metrics_stay_open`) now green.
- 22 ruff errors (5 `src`, 17 `tests`) fixed; whole-repo `ruff check .` clean.
- Coverage 91.8 % → **93.62 %**.
- Deleted 2 dead stubs (`_is_market_hours`, `_drain_open_orders`).

---

## 2. Architecture Health

| Item | Verdict | Evidence |
|---|---|---|
| Ports & Adapters | **CLEAN** | `domain/ports.py` contracts; `infrastructure/`+`interfaces/` implement; no domain→infra imports |
| Dependency direction | **CLEAN** | `tests/architecture/test_dependency_direction.py` (AST audit) + `test_imports.py` |
| Circular imports | **NONE** | import graph compiles; pyright clean |
| Dead abstractions | NONE | vulture hits are false positives (referenced 2–23 files) |
| Unused interfaces | NONE | every port has a concrete adapter |
| Unused repositories | NONE | in-memory / sqlite / postgres consumed by `factory.py` |
| Unused adapters | NONE | alpaca / paper / binance reachable |
| Unused migrations | NONE | `v001`–`v006` registered + tested |
| Unused services | NONE | all constructed by `factory.py` |
| Duplicate logic | MINIMAL | exception-tuple alias introduced this pass (repeated 4× → 1) |
| God classes | **ACCEPTED** | `TradingOrchestrator`, `CycleExecutor`, `DaemonController`, `cli.main` are composition/lifecycle roots; complexity kept out of the domain |

**A-1 — event replay not wired into production path.** `OrderEventJournal` (`infrastructure/journal.py`) + `OrderEventEngine` (`application/order_event_engine.py`) implement durable idempotency + replay (OT-002/003/006) and are unit-tested, but **neither is instantiated anywhere in `src`** (tests only). `factory.py` wires `InMemoryEventBus` into the order flow. The durable journal is therefore **not in the production runtime path** — a correctness/trust gap, not dead code. Owned in §10 (CLOSURE-12, BLOCKER).

**A-2 (actioned):** `DaemonController._is_market_hours` was a dead stub (`return True`) and `_drain_open_orders` was a dead stub recording a fake `shutdown.drain_orders` audit event. Both **deleted** this session (never called, never tested).

---

## 3. Dead Code Audit

Method: `vulture` over `src` + whole-repo reference cross-check (`src` + `tests`) for every flagged symbol.

| Category | Finding | Disposition |
|---|---|---|
| Unused modules | none — all imported transitively | **KEEP** |
| Unused classes | none at production level (`ResearchEngine`, `OrderEventEngine` referenced by consumers) | **KEEP** |
| Unused methods | `_is_market_hours`, `_drain_open_orders` | **DELETE (done)** |
| Unused functions | none | **KEEP** |
| Unused constants | `CRYPTO/FOREX/EQUITY/FUTURES/INACTIVE`, `LONG/SHORT/NEUTRAL`, `DEPRECATED` — enum literals used by value (vulture false positives) | **KEEP** |
| Obsolete compatibility code | `except ImportError:` guards in `factory.py` (optional alpaca/binance) — active install-gated | **KEEP** |
| Legacy wrappers | `PaperBrokerAdapter` fallback | **KEEP** (runtime paper default) |
| Duplicate utilities | none significant | — |
| Old migrations | `v001`–`v006` wired | **KEEP** |
| Temporary workarounds | none | — |
| `as conn` unused | `tests/test_database_connection.py` (F841) | **FIXED** |

In-scope dead code removed; nothing survives on "maybe later" except documented, owned inventory items.

---

## 4. Defensive Code Audit

| Pattern | Location / Count | Classification |
|---|---|---|
| Broad `except Exception` | `daemon_controller._detect_crash` (must never crash); `programme_b` network-skip | **necessary** |
| `try/except: pass` | `factory.py` optional decorator imports (B110, Low) | **necessary** (install-gated) |
| `# pragma: no cover` | ~26 across API surface, application layer, sqlite repos | **necessary** (unreachable defensive branches; audited) |
| `# noqa` | intentional blind-catch / f-string-SQL suppressions | **necessary** (each justified) |
| TODO / FIXME | **0** | — |
| Manual retries | replaced by `infrastructure/retry.py` backoff | **clean** |
| Silent failures | none (all excepts log / report / publish) | **clean** |
| `subprocess.run(check=)` | 1 test lacked `check`; added `check=False` | **fixed** |

**Honesty note:** `order_event_engine.py` is fully covered by tests but has no production caller (§2 returns it to A-1). Its `# pragma: no cover` invariant guards currently document test-only coverage — reclassified as **technical debt** in §10 (CLOSURE-12).

---

## 5. Complexity Audit

Top modules by AST decision-point cyclomatic complexity and LOC:

| Rank | Module | Decision pts | LOC |
|---:|---|---:|---:|
| 1 | `interfaces.cli.main` | 65 | 471 |
| 2 | `infrastructure.market_stream` | 47 | 522 |
| 3 | `application.cycle_executor` | 37 | 484 |
| 4 | `application.daemon_controller` | 32 | 294 |
| 5 | `interfaces.api.operator` | 30 | 537 |
| 6 | `domain.services.paper_trading_service` | 30 | 433 |
| 7 | `domain.services.analysis_service` | 26 | 221 |
| 8 | `infrastructure.database.connection` | 24 | 303 |
| 9 | `infrastructure.alpaca_broker` | 24 | 285 |
| 10 | `infrastructure.message_queue` | 24 | 193 |

**Recommendation:** complexity is concentrated in the application/infra composition layer by design (keeps the domain pure). No decomposition is introduced pre-Code-Freeze (churn without release-risk reduction). `market_stream.py` is the post-freeze refactor candidate (CLOSURE-13, LOW).

---

## 6. Operational Trust Audit

Legend: **PROVEN** = code + passing regression test; **PARTIAL** = proven at unit level, not confirmed in the live path; **UNPROVEN** = no production evidence.

| Invariant | Status | Evidence |
|---|---|---|
| Audit chain | **PROVEN** | `test_audit_integrity`, `audit.py` |
| Kill switch | **PROVEN** | `test_security_policy`; persistent SQLite kill switch |
| Preflight | **PROVEN** | `test_preflight_service`, `test_preflight_execution_integration` |
| Broker reconciliation | **PROVEN** | `test_broker_state_reconciliation`, `test_reconciliation_effects` |
| Market hours | **PARTIAL (improved)** | `test_market_hours_engine` proven; dead daemon gate (always `True`) removed |
| Rate limiting | **PROVEN** | `test_rate_limiter`, `test_broker_rate_limiter` |
| Recovery | **PROVEN** | `test_daemon_controller_recovers_after_crash`, `test_operational_recovery` |
| Backup | **PROVEN** | `test_backup` (sqlite + pg_dump) |
| Restore | **PROVEN** | `test_backup` restore path |
| Rollback | **PROVEN** | migration `down()` idempotency, `test_migration_v004` |
| Metrics | **PROVEN (fixed)** | `/metrics` 200 now; `test_metrics_service` |
| Health | **PROVEN** | OT-010; `test_healthz_liveness`, `test_health_readiness_degraded` |
| Alerts / notifications | **PROVEN** | `test_notification_service`, `test_webhook_notifier` |
| Heartbeat | **PARTIAL** | leader-election heartbeat + `/v1/healthz`; no dedicated process-level report |
| Event replay | **PARTIAL** | durable journal unit-proven (OT-002/003) but **not wired into the live order pipeline** |

**OTI** scored over the 11 always-claims + 4 partials (see dashboard §9).

---

## 7. Documentation Audit

Instruction: every document must match code. Discrepancies:

| Document | Status | Discrepancy |
|---|---|---|
| CONSTITUTION.md | ✅ | matches |
| MEP | ✅ | historical |
| ADRs | ✅ | matches |
| Sprint docs | ✅ | matches (incl. SPRINT_19 working record) |
| Runbooks | ❌ | several CLI verbs asserted that do not exist: `traderos daemon start`, `risk`, `metrics`, `audit verify` (verified vs `add_parser` in `main.py`) |
| Blueprint | ⚠️ stale | completion % from 2026-07-31 (843 tests / 84.6 %); reality = 1266 / 93.6 % |
| Ground Truth | ⚠️ stale | runbook→CLI gaps still open; `pilot` + `security` verbs now added (sprint 17/18) |
| README | ✅ | matches current CLI surface |
| Previous `ENGINEERING_CLOSURE_AUDIT.md` | ✗ | aspirational placeholders — `replaced by this file` |
| Previous `FINISH_LINE_DASHBOARD.md` | ✗ | claimed 99 % / PRI 100 — did not reflect the real metrics + replay gaps — replaced |

**Action:** runbook→CLI verb gaps are a real ops-trust gap, owned in §10 (CLOSURE-14, HIGH).

---

## 8. Release Constitution

Gates/definitions/sign-offs live in `docs/engineering/TRADEROS_RELEASE_CONSTITUTION.md`. This audit supplies the constitution's required evidence:
- `make ci` (lint + format-check + typecheck + test): **GREEN** 2026-08-02
- `pip-audit` 0 vulns; `bandit` 0 High: **GREEN**
- Dashboard regenerated (`FINISH_LINE_DASHBOARD.md`).

**Not yet declaring Code Freeze** because replay wiring (CLOSURE-12), live drills (CLOSURE-15/16) and runbook alignment (CLOSURE-14) are open.

---

## 9. Final Closure Backlog

Verified directly from code/toolchain — no invented work. Units: d = dev-day, wk = work-week.

| ID | Title | Why | Impact | Risk | Deps | Effort | Priority |
|---|---|---|---|---|---|---|---|
| CLOSURE-12 | Wire `OrderEventEngine`/journal into live order path, or formally retire | event-replay is unit-only today | correctness/trust | med | arch+exec review | 1–2 d | **BLOCKER** |
| CLOSURE-15 | Authenticated live Binance connectivity drill | OT-001 remaining risk (no network here) | correctness | live creds | — | 1 d | **BLOCKER** |
| CLOSURE-16 | Live Alpaca contract drill (`cancel_replace`, partial fills, account fields) | OT-009 is duplicate/overflow only | trust | pilot creds | 2 d | 2 d | **BLOCKER** |
| CLOSURE-08 | Controlled pilot (dry-run → constrained real), `pilot` checks run | Definition of Controlled Pilot | commercial | med | CLOSURE-16 | 2 w | BLOCKER |
| CLOSURE-17 | Real PostgreSQL failure drill (failover / disk-full) | R-02 remaining | trust | env | CLOSURE-15 | 1 d | HIGH |
| CLOSURE-14 | Align runbooks to CLI (`daemon start/status`, `risk`, `metrics`, `audit verify`) or rewrite runbook | ops-trust (§7) | ops | — | — | 2 d | HIGH |
| CLOSURE-19 | Re-verify `/metrics` + health under prod runtime resources | metrics fixed; confirm in prod | trust | prod | CLOSURE-15 | 1 d | HIGH |
| CLOSURE-13 | Decompose `market_stream.py` (47 decision points) | reduce complexity risk | maintainability | — | — | 3 d | LOW |
| CLOSURE-10 | Adopt a single daemon heartbeat/report mechanism | OTI partial | ops health | | CLOSURE-12 | 1 d | LOW |
| CLOSURE-11 | CI golden-checkasserting dashboard indices | prevent silent index drift | dual | — | — | 1–2 d | MED |
| CLOSURE-11b | CI integration test asserting `/metrics` 200 (prometheus-client present) | prevent the §1 regression | reliability | — | — | 1/2 d | MEDIUM |
