# Build Principles — reusable operating discipline for software manufacturing

**Origin:** distilled from TraderOS (Sprint 25–27 + GAP_READINESS + LIVE_RUN_POLICY),
2026-08-04. **Status:** product-agnostic, reusable artifact for FounderOS.
**Core thesis:** the bottleneck of software manufacturing is **verification, not
generation**. AI can write code fast; the constraint is *proving it is right,
reproducibly, and knowing when it isn't*. Every principle below exists to make
the verification loop cheap, reliable, and loud.

---

## Principles

### P1 — Evidence over aspiration
A claim is only as good as its reproducible evidence. Every capability carries a
score (0–100) and an observable **exit test**. Verdicts are `PASS` / `FAIL` /
`NO-GO` — never vibes, never "close enough." Closing one gap never means risk is
complete.
*TraderOS proof:* `GAP_READINESS.md` + every drill log ends with `VERDICT: PASS/FAIL/NO-GO`.
*Failure mode if ignored:* a feature is "done" on confidence, then breaks in production.

### P2 — Gate every boundary
Nothing crosses from lower-trust to higher-trust without a demonstrated gate.
Research → paper → live. Default is **fail-closed**; unlimited allowances are
bugs; when unsure, take the conservative cap.
*TraderOS proof:* `LIVE_RUN_POLICY.md`, `live_gate.py` (blocks live posture unless every GO condition holds), governance CI job.
*Failure mode if ignored:* a paper feature silently trades real capital.

### P3 — Protect at the real seam
Enforcement lives at the actual submission boundary — not in a helper only the
test path uses. Before building, verify the premise against the real code path.
*TraderOS proof:* risk gate + idempotency keyed to `client_order_id` threaded through the real `CycleExecutor → adapter` chain.
*Failure mode if ignored:* a gate that "passes" while the production path stays unguarded — the worst kind of false confidence.

### P4 — Drill it, lock it
Every feature ships with a **drill** that exercises the real path and a
**suite-locked test** so it cannot rot. Evidence artifacts are committed.
*TraderOS proof:* 7 sprint-27 drills, each with a lock test; all green in CI.
*Failure mode if ignored:* the protection exists in a commit nobody re-runs.

### P5 — Second order as requirements
Before adding a capability, ask what it *requires downstream* and what it
*newly enables*; those are first-class requirements, not afterthoughts.
*TraderOS proof:* A1→A7 chain in `PILOT_TO_PRODUCT.md` — deployment requires auth fail-closed, Postgres, and secret-manager before it can be safe.
*Failure mode if ignored:* the task is "done" but nothing can actually consume it.

### P6 — The critical path is minimal and honest
Split the **gate** (what must be true to ship a safe milestone) from the
**track** (what makes it a great product). Never let gold-plating block the
milestone.
*TraderOS proof:* Track A (pilot gate) vs Track B (product track) in `PILOT_TO_PRODUCT.md`; UI/users deliberately off the critical path.
*Failure mode if ignored:* a year of UI work, no pilot.

### P7 — Run unattended, fail loudly
The overseer may be away (a phone, a weekend). The system must make the safe
path automatic and the unsafe path **loud**: page on exceptions, never silently
pass. Trust = the ability to fail loudly when nobody is watching.
*TraderOS proof:* supervision CRITICAL on unclean death, on-call transport, soak harness fails closed without credentials.
*Failure mode if ignored:* a silent crash overnight becomes a loss by morning.

---

## The manufacturing loop (the routine)

```
1. Define   — scope, exit test, evidence path, blast radius, reviewer.
2. Gate     — confirm the premise against real code; boundary checks.
3. Execute  — specialized agent/labour does the work, fail-closed by default.
4. Verify   — drill the real path; run the exit test; record evidence.
5. Lock     — suite-lock test + CI + committed evidence; verdict recorded.
```

Anything that cannot produce step 4's evidence is not done. Step 2 can veto
before any code is written.

---

## Instantiating for a new product (FounderOS recipe)

1. Write the product's **boundary + red-lines** (what must never happen, fail-closed).
2. Create its **gap register**: one row per capability with score + exit test.
3. Enforce the loop with a **task template** (scope / exit test / evidence path /
   blast radius / reviewer role) so every task is manufacturable.
4. Tier tasks by **blast radius**: execution/risk paths get human-supervised
   gates; CRUD/copy paths get lightweight gates. Same loop, different throttle.
5. Capture every verdict as a **committed artifact** — the audit trail of the
   manufacturing process itself.
6. **Bootstrap**: build the routine by using it on the first real product.

## Bootstrapping note

TraderOS is simultaneously the proof-of-concept *and* the first product in the
portfolio. We forge the routine by executing it here — each sprint leaves both a
product improvement and a sharper version of this discipline. The elixir is not
the code; it is this loop, running reliably, with a human who reads the verdicts.
