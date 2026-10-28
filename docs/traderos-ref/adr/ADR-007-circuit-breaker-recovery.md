# ADR-007: Circuit Breaker Recovery Semantics

## Status

Proposed

## Context

TraderOS has two kill-switch / circuit-breaker implementations:

- `KillSwitch` in `domain/services/risk_service.py` — dataclass-based, in-memory, used by `RiskService`
- `PersistentKillSwitch` in `domain/services/reconciliation_service.py` — class-based, persistable state, cooldown-aware

Both currently implement auto-reset recovery: when `can_trade()` is called while the circuit is open, and the cooldown period has elapsed (default 300s), the circuit silently resets itself and returns `allowed=True`. The caller never learns that the circuit *was* open.

This creates a reliability and audit blind spot:
- A circuit that tripped at 02:00 and auto-recovered by 02:05 produces zero alerts, zero logs, zero human awareness.
- The consecutive-failures counter is reset, erasing the evidence of the failure burst.
- Operators discover the failure only if they proactively query historical state.

The Constitution (Principle 2: Evidence over Opinion) requires that "every failure must be learnable." Auto-reset violates this by discarding failure evidence.

## Options

### Option A: Manual-Reset Only (Recommended)

The circuit breaker, once tripped, remains open until an explicit `reset()` call. No recovery path exists inside `can_trade()`.

**How it works:**
- `record_failure()` trips the circuit (circuit_open = True)
- `can_trade()` returns `TradeVerdict(False, "Circuit breaker open")` unconditionally
- Only an explicit `reset()` call clears the circuit
- The operator (human or supervisory system) must investigate, acknowledge, and explicitly re-arm

**Positive:**
- Every trip requires human investigation — no silent recovery
- Alerts and metrics have time to propagate before the circuit clears
- Failure evidence (consecutive_failures, circuit_open_until) is preserved for post-mortem
- Aligns with Constitution §2 Principle 2 (Evidence over Opinion)
- Matches industry practice for production circuit breakers (Hystrix, resilience4j default to manual)

**Negative:**
- Requires operator attention even for transient failures (e.g., a single broker timeout)
- In a无人 (unattended) deployment, the system stays halted until human intervention
- Adds operational burden for false-positive trips

### Option B: Auto-Reset with Cooldown (Current Behavior)

The circuit auto-recovers after a configurable cooldown period. `can_trade()` checks `circuit_open_until + cooldown` and resets silently if the window has passed.

**Positive:**
- Self-healing for transient failures — no human needed for a brief broker blip
- Proven in production at many trading firms for non-critical paths
- Lower operational overhead in high-volume environments

**Negative:**
- Silent recovery hides failure evidence — operators may never know the circuit tripped
- Violates Constitution §2 Principle 2 by discarding learning opportunities
- The cooldown is a guess; the right value depends on failure mode, not calendar time
- Can mask underlying problems (e.g., recurring 300s-separated failures never accumulate)

### Option C: Hybrid — Auto-Reset with Escalation

Auto-reset for N trips within a window; after N trips, lock to manual-reset.

**Positive:**
- Best of both options for common cases
- Graceful degradation from transient to persistent failure modes

**Negative:**
- State machine complexity doubles (need trip-count tracking across windows)
- Hard to reason about in post-mortem ("was it trip 4 or trip 5 that locked it?")
- Increases test surface and maintenance burden

## Decision

**Option A: Manual-Reset Only.**

Rationale:
1. Constitution §2 Principle 2 requires failures to be learnable. Auto-reset discards evidence.
2. TraderOS is currently in paper trading and early live trading. The operational burden of manual reset is acceptable at this scale. If unattended operation becomes necessary, a supervisory process (external health monitor) can call `reset()` after verifying the failure condition has cleared.
3. The code is simpler — no cooldown math, no silent mutation of state inside a getter.
4. Consistency with `PersistentKillSwitch` and `KillSwitch`: both move to the same semantic.

## Consequences

### Positive
- Every circuit trip is visible, auditable, and requires acknowledgment
- Failure evidence is preserved for post-mortem analysis
- Metrics (circuit_breaker.tripped) have unambiguous meaning — trip = halt
- Operators can build external automation on top of a stable, predictable state machine

### Negative
- A transient broker timeout at 03:00 halts trading until morning — acceptable risk for current scale
- Operational runbooks must include circuit-breaker monitoring and reset procedures
- Future work may re-introduce auto-reset for non-critical paths, but only behind explicit operator configuration

## Implementation

1. `KillSwitch.can_trade()`: remove the auto-reset path. Return `False` unconditionally when `circuit_open` is `True`.
2. `PersistentKillSwitch.can_trade()`: same change. Remove the cooldown-based auto-reset.
3. Both classes: `record_failure()` continues to set `circuit_open = True`. Only `reset()` clears it.
4. `MetricsPort.counter("circuit_breaker.tripped")` is incremented on every trip.
5. CLI: `traderos risk reset` calls `reset()` on the active kill switch.

## Compliance

[Constitution §2 Principle 2] Evidence over Opinion — failures must be learnable.
[Constitution §1] Systems over scripts — explicit state transitions over implicit recovery.
