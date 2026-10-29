# TraderOS Release Constitution

This document defines the gates, standards, and sign-offs required to release TraderOS to production. It operates as the final engineering authority over the release lifecycle.

## Definition of Done (DoD)
A feature, work package, or engineering objective is "Done" when:
- It solves the problem stated in the objective.
- It is fully covered by automated tests (Unit and/or Integration).
- It adheres strictly to the Engineering Constitution and ADRs.
- It passes all CI gates (`ruff`, `pyright`, `pytest`).
- It has been documented (changelog, sprint docs, and relevant architecture docs).
- No new technical debt is introduced without explicit tracking.

## Definition of Production Ready
The repository as a whole is "Production Ready" when:
- All features required for the release are "Done".
- Test coverage meets or exceeds the baseline threshold (90%+).
- The `TRADEROS_ENV=production` posture defaults to fail-closed (requires API keys, TLS, restrictive CORS).
- Operational Trust invariants (reconciliation, preflight, kill switches, audit trails) are mathematically and empirically proven via tests.
- Zero known critical or high-severity vulnerabilities exist.
- The pipeline (`make ci`, deploy checks) is entirely green.

## Definition of Controlled Pilot
A "Controlled Pilot" is a restricted live-trading phase where:
- The system operates with real money but under tight constraint guards (`TRADEROS_MIN_ORDER_QTY`, `TRADEROS_MAX_ORDER_NOTIONAL`).
- Only pre-approved, highly monitored strategies are enabled.
- A human operator is actively reviewing the `traderos pilot readiness` and `traderos pilot dry-run` results before any live order execution.
- The objective is strictly verifying broker connectivity, latency, and execution fidelity, not maximizing profit.

## Definition of Release
A "Release" is defined as:
- The deployment of a Production Ready artifact to the live hosting environment (e.g., Railway).
- The publication of a versioned artifact (Docker image to GHCR, GitHub Release with attached notes).
- The transition of the operational phase from Development/Testing to Live/Pilot.

## Definition of Code Freeze
"Code Freeze" is a strict repository state where:
- Feature development is completely halted.
- Only critical, verified bug fixes or security patches are allowed.
- The objective is exclusively risk reduction and stability verification.

## Required Evidence
Before any release, the following evidence must be captured and logged:
- A clean run of `make ci` (0 lint errors, 0 type errors, 100% test pass rate).
- Output of `traderos security audit` confirming a secure posture.
- A generated `FINISH_LINE_DASHBOARD.md` summarizing the operational indices.

## Required Sign-Offs
- **Principal Systems Engineer / Lead Architect**: Approves architecture integrity and code quality.
- **Release Engineer**: Approves deployment artifacts and pipeline health.
- **Operations Lead**: Approves runbooks, monitoring, and kill-switch readiness.

## Release Checklist
- [ ] Code Freeze initiated.
- [ ] Final `make ci` executed and verified green.
- [ ] Security audit executed and verified secure.
- [ ] `CHANGELOG.md` updated with the final release version.
- [ ] `FINISH_LINE_DASHBOARD.md` updated and committed.
- [ ] Version bumped in `pyproject.toml` and `settings.yaml`.
- [ ] Git tag created matching the version (e.g., `v1.1.0`).
- [ ] GitHub Release drafted and published.
- [ ] Production environment variables verified against `SecretRotator`.
- [ ] Deployment triggered and health checks passed in production.
