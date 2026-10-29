# FounderOS — One-Page Workflow Spec

**Status:** v1, 2026-08-07. **Product-agnostic, bootstrapped on TraderOS (Sprint 28).**
**Core thesis:** the bottleneck of software manufacturing is proof, not writing.
Every task is manufacturable **only if** its scope, exit test, evidence path,
blast radius, and reviewer are defined before labour starts.

---

## The one task template

Every manufacturing task is a single row with exactly five fields. Nothing
starts until all five are filled; step 2 (Gate) can veto before any code is
written.

| Field        | What it must answer                              | Default / fail-closed rule            |
|--------------|--------------------------------------------------|---------------------------------------|
| **Scope**    | The one capability, and the one boundary it touches | Tightest blast radius that still works |
| **Exit test**| The observable, reproducible pass/fail assertion  | Verdict is the proof, not "it works"  |
| **Sphere of influence (blast radius)** | What breaks if wrong + who must review | Execution/risk = human gate; CRUD = lightweight |
| **Reviewer** | The named role that reads the verdict             | Never the same role that wrote the code |
| **Evidence path** | Where the committed, re-runnable artifact lives | `docs/evidence/`, suite-locked test, drill log |

## The loop (the routine)

```
1. Define  — fill all five fields with a FROZEN scope and exit test.
2. Gate    — confirm the premise against the REAL code; boundary checks;
             VETO loudly if the plan contradicts its own scope.
3. Execute — labour does the work, fail-closed by default. Rejections loud.
4. Verify  — run the exit test on the REAL path; record go/no-go.
5. Lock    — suite-lock test + CI + committed evidence; verdict recorded.
```

Anything that cannot produce step 4's evidence is NOT done. Step 2 can stop
the train before any code exists — this is a feature, not friction.

## Gate: red-lines and fail-closed defaults

- No endpoint/order/state transition without a configured key → deny.
- Unknown user / missing config / absent allowlist → deny (never silently allow).
- No unlimited allowances. When unsure, take the conservative cap.
- Enforcement sits at the REAL submission boundary, not a helper the backtest
  path also calls.

## Reviewer rules (M3)

- **Execution/risk order paths:** human-supervised; a second review is required
  before promote-to-live; the exit test must exercise the actual broker call
  path and prove the broker is NOT invoked when a check refuses.
- **CRUD / copy / low-risk paths:** lightweight auto-review; still suite-locked.

## Bootstrap

TraderOS is the proof-of-concept AND the first product. We forge this routine by
executing it here — each sprint leaves both a product improvement and a sharper
version of the discipline. FounderOS does not need to exist first; it emerges.
